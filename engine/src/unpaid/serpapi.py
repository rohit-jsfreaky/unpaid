"""SerpApi over plain HTTPS, with record-once / replay-free caching and a budget guard.

Every response is stored under cache/ keyed by a hash of the request (never the API key).
Recorded evidence folders are read as cache too, so the 7 Oct probes and every frozen run replay with no key.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx

from unpaid.config import CACHE_DIR, EVIDENCE_DIR, api_key, load_settings

SEARCH_URL = "https://serpapi.com/search.json"
ACCOUNT_URL = "https://serpapi.com/account.json"

Mode = Literal["live", "replay"]
Params = dict[str, str | int]


class SerpApiError(Exception):
    """SerpApi refused the call (bad key, rate limit, server error)."""


class NotRecorded(Exception):
    """Replay mode and this request was never recorded."""


class BudgetExceeded(Exception):
    """The run would leave fewer searches than unpaid.toml allows."""


def canonical(params: Params) -> dict[str, str]:
    return {k: str(v) for k, v in sorted(params.items()) if k != "api_key" and v is not None}


def request_key(params: Params) -> str:
    blob = json.dumps(canonical(params), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


@dataclass(frozen=True)
class Result:
    key: str
    request: dict[str, str]
    data: dict[str, Any]
    from_cache: bool


def _request_of(doc: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """(request, response) for a stored file: our envelope, or a raw SerpApi response."""
    if "request" in doc and "response" in doc:
        return doc["request"], doc["response"]
    if isinstance(doc.get("search_parameters"), dict):
        return doc["search_parameters"], doc
    return None


@dataclass
class Cache:
    write_dir: Path = CACHE_DIR
    read_dirs: tuple[Path, ...] = (CACHE_DIR, EVIDENCE_DIR)
    _index: dict[str, Path] | None = field(default=None, init=False, repr=False)

    def _build(self) -> dict[str, Path]:
        index: dict[str, Path] = {}
        for folder in self.read_dirs:
            if not folder.exists():
                continue
            for path in sorted(folder.rglob("*.json")):
                try:
                    doc = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                pair = _request_of(doc) if isinstance(doc, dict) else None
                if pair:
                    index.setdefault(request_key(pair[0]), path)
        return index

    @property
    def index(self) -> dict[str, Path]:
        if self._index is None:
            self._index = self._build()
        return self._index

    def get(self, params: Params) -> Result | None:
        key = request_key(params)
        path = self.index.get(key)
        if path is None:
            return None
        pair = _request_of(json.loads(path.read_text(encoding="utf-8")))
        assert pair is not None
        return Result(key=key, request=canonical(params), data=pair[1], from_cache=True)

    def put(self, params: Params, data: dict[str, Any], secret: str) -> Result:
        key = request_key(params)
        text = json.dumps({"request": canonical(params), "response": data}, ensure_ascii=False, indent=1)
        if secret in text:
            raise SerpApiError("refusing to cache a response that contains the API key")
        engine = str(params.get("engine", "search"))
        path = self.write_dir / engine / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.index[key] = path
        return Result(key=key, request=canonical(params), data=data, from_cache=False)


def fetch_account(key: str) -> dict[str, Any]:
    """Account usage. This endpoint is free: it does not count as a search."""
    try:
        r = httpx.get(ACCOUNT_URL, params={"api_key": key}, timeout=30)
    except httpx.HTTPError as e:
        raise SerpApiError(f"account check failed: {type(e).__name__}") from None
    if r.status_code != 200:
        raise SerpApiError(f"account check failed: HTTP {r.status_code}")
    return r.json()


@dataclass
class Client:
    mode: Mode
    cache: Cache = field(default_factory=Cache)
    key: str | None = None
    keep_at_least: int = 30
    account: Callable[[str], dict[str, Any]] = fetch_account
    transport: httpx.BaseTransport | None = None
    searches_used: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def from_env(cls, mode: Mode | None = None) -> Client:
        key = api_key()
        chosen: Mode = mode or ("live" if key else "replay")
        if chosen == "live" and not key:
            raise SerpApiError("live mode needs SERPAPI_API_KEY in .env; use replay mode without it")
        return cls(mode=chosen, key=key, keep_at_least=load_settings().keep_at_least)

    def missing(self, requests: Iterable[Params]) -> list[Params]:
        return [p for p in requests if self.cache.get(p) is None]

    def check_budget(self, planned: int) -> int | None:
        """Refuse a run that would cross the limit. Returns searches left before the run."""
        if planned == 0:
            return None
        if self.mode == "replay":
            raise NotRecorded(f"{planned} request(s) not recorded; replay mode makes no live calls")
        assert self.key
        left = int(self.account(self.key)["total_searches_left"])
        if left - planned < self.keep_at_least:
            raise BudgetExceeded(
                f"this run needs {planned} searches; {left} left, and unpaid.toml keeps at least {self.keep_at_least}"
            )
        return left

    def search(self, params: Params) -> Result:
        hit = self.cache.get(params)
        if hit is not None:
            return hit
        if self.mode == "replay":
            raise NotRecorded(f"not recorded: {canonical(params)}")
        assert self.key
        try:
            with httpx.Client(transport=self.transport, timeout=90) as http:
                r = http.get(SEARCH_URL, params={**canonical(params), "api_key": self.key})
        except httpx.HTTPError as e:
            raise SerpApiError(f"SerpApi call failed: {type(e).__name__}") from None
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code != 200:
            raise SerpApiError(f"SerpApi HTTP {r.status_code}: {data.get('error', 'no message')}")
        with self._lock:
            self.searches_used += 1
            return self.cache.put(params, data, self.key)


@dataclass(frozen=True)
class Receipt:
    """Where a number came from: the SerpApi search id, its archived JSON and when it ran."""

    search_id: str
    json_endpoint: str
    created_at: str


def receipt(data: dict[str, Any]) -> Receipt:
    meta = data.get("search_metadata") or {}
    return Receipt(
        search_id=str(meta.get("id", "")),
        json_endpoint=str(meta.get("json_endpoint", "")),
        created_at=str(meta.get("created_at", "")),
    )
