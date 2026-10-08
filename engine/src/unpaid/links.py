"""Does a description link pay the creator? Follow its redirects and look for the store's affiliate tag.

Amazon's Associates short links carry the creator's Associate ID ("tag=") — Amazon.in Associates Central, SiteStripe
help. We read only redirect headers and stop at the first hop that points at Amazon or Flipkart, so no store page is
ever loaded. Results are saved once (links.json) and replayed with no network.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from pydantic import BaseModel

# Links that can't pay a commission on a phone: social profiles and the platform itself.
SKIP_HOSTS = {
    "youtube.com", "youtu.be", "instagram.com", "twitter.com", "x.com", "facebook.com", "t.me", "telegram.me",
    "whatsapp.com", "wa.me", "linkedin.com", "threads.net",
}  # fmt: skip
STORES = {"amazon.in": "tag", "amazon.com": "tag", "flipkart.com": "affid", "dl.flipkart.com": "affid"}
MAX_HOPS = 6


class LinkCheck(BaseModel):
    url: str
    hops: list[str]  # every URL we were sent to, in order
    store: str | None  # "amazon.in" / "flipkart.com" when the chain reached a store
    affiliate_param: str | None  # "tag=<id>" or "affid=<id>" when the store URL carries one
    error: str | None
    checked_at: datetime

    @property
    def is_affiliate(self) -> bool:
        return self.affiliate_param is not None


def host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def store_param(url: str) -> tuple[str | None, str | None]:
    """("amazon.in", "tag=abc-21") if `url` is a store URL carrying an affiliate id."""
    h = host(url)
    store = next((s for s in STORES if h == s or h.endswith("." + s)), None)
    if store is None:
        return None, None
    key = STORES[store]
    value = (parse_qs(urlparse(url).query).get(key) or [None])[0]
    return store, (f"{key}={value}" if value else None)


def worth_checking(url: str) -> bool:
    return host(url) not in SKIP_HOSTS


def follow(url: str, transport: httpx.BaseTransport | None = None) -> LinkCheck:
    hops: list[str] = []
    current = url
    error = None
    try:
        with httpx.Client(transport=transport, timeout=15, follow_redirects=False) as http:
            for _ in range(MAX_HOPS):
                store, param = store_param(current)
                if store:
                    return LinkCheck(
                        url=url, hops=hops, store=store, affiliate_param=param, error=None, checked_at=datetime.now(UTC)
                    )
                # GET, not HEAD: some shorteners (link.amazon) answer HEAD with 404. Streamed, so no body is read.
                with http.stream("GET", current, headers={"User-Agent": "Mozilla/5.0"}) as r:
                    status, loc = r.status_code, r.headers.get("location")
                if not (300 <= status < 400 and loc):
                    break
                current = urljoin(current, loc)
                hops.append(current)
    except httpx.HTTPError as e:
        error = type(e).__name__
    return LinkCheck(url=url, hops=hops, store=None, affiliate_param=None, error=error, checked_at=datetime.now(UTC))


class LinkBook:
    """Saved link checks. Live mode checks what's missing; replay mode only reads."""

    def __init__(
        self,
        path: Path,
        live: bool,
        transport: httpx.BaseTransport | None = None,
        also_read: tuple[Path, ...] = (),
    ) -> None:
        self.path = path
        self.live = live
        self.transport = transport
        self.checks = self._load(path)
        # Recorded checks (e.g. the showcase's) are read but never rewritten.
        self.recorded: dict[str, LinkCheck] = {}
        for extra in also_read:
            self.recorded.update(self._load(extra))

    @staticmethod
    def _load(path: Path) -> dict[str, LinkCheck]:
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return {u: LinkCheck.model_validate(c) for u, c in raw.items()}

    def check_all(self, urls: list[str]) -> int:
        """Check every link not seen before. Returns how many were checked now."""
        todo = sorted({u for u in urls if worth_checking(u) and self.get(u) is None})
        if not todo:
            return 0
        if not self.live:
            raise LookupError(f"{len(todo)} link(s) never checked; replay mode makes no network calls")
        with ThreadPoolExecutor(max_workers=4) as pool:
            for c in pool.map(lambda u: follow(u, self.transport), todo):
                self.checks[c.url] = c
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {u: c.model_dump(mode="json") for u, c in sorted(self.checks.items())}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return len(todo)

    def get(self, url: str) -> LinkCheck | None:
        return self.checks.get(url) or self.recorded.get(url)
