"""The one LLM client: strict JSON answers, temperature 0, every call saved to disk, spend capped.

Same request twice = read from disk, free. Replay mode never calls the provider and needs no key.
"""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel

from unpaid.config import CACHE_DIR, llm_key, load_settings

PROVIDERS = {
    # name: (chat completions URL, env var holding the key)
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
}
# Only route to endpoints that honour every parameter we send (strict JSON schema, temperature).
ROUTING = {"require_parameters": True}


class LLMError(Exception):
    """The provider refused or failed the call."""


class LLMNotRecorded(Exception):
    """Replay mode and this prompt was never answered before."""


class SpendLimitReached(Exception):
    """The saved calls already add up to the spend limit in unpaid.toml."""


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """JSON schema in the form strict mode accepts: $refs inlined, no titles, every key required, no extras."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(copy.deepcopy(defs[node["$ref"].split("/")[-1]]))
            out = {k: walk(v) for k, v in node.items() if k not in ("title", "default")}
            if out.get("type") == "object" and "properties" in out:
                out["required"] = list(out["properties"])
                out["additionalProperties"] = False
            return out
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


def request_hash(request: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


@dataclass
class LLM:
    mode: Literal["live", "replay"]
    model: str
    write_dir: Path = CACHE_DIR / "llm"
    read_dirs: tuple[Path, ...] = (CACHE_DIR / "llm",)
    key: str | None = None
    provider: str = "openrouter"
    spend_limit_usd: float = 0.0
    transport: httpx.BaseTransport | None = None
    calls: int = 0
    cached: int = 0
    cost_usd: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def from_env(cls, write_dir: Path, read_dirs: tuple[Path, ...], mode: str | None = None) -> LLM:
        s = load_settings()
        key = llm_key(PROVIDERS[s.llm_provider][1])
        chosen = mode or ("live" if key else "replay")
        if chosen == "live" and not key:
            raise LLMError(f"live mode needs {PROVIDERS[s.llm_provider][1]} in .env; use replay mode without it")
        return cls(
            mode="live" if chosen == "live" else "replay",
            model=s.llm_model,
            write_dir=write_dir,
            read_dirs=read_dirs,
            key=key,
            provider=s.llm_provider,
            spend_limit_usd=s.llm_spend_limit_usd,
        )

    def _find(self, h: str) -> Path | None:
        for d in self.read_dirs:
            path = d / f"{h}.json"
            if path.exists():
                return path
        return None

    def spent_so_far(self) -> float:
        """Every dollar the saved calls cost, summed from disk."""
        total = 0.0
        for path in self.write_dir.glob("*.json"):
            try:
                total += float(json.loads(path.read_text(encoding="utf-8"))["usage"].get("cost") or 0.0)
            except (OSError, ValueError, KeyError):
                continue
        return total

    def structured[T: BaseModel](self, system: str, user: str, schema: type[T]) -> tuple[T, str]:
        """One answer that must match `schema`. Returns (answer, request hash)."""
        request: dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "strict": True, "schema": strict_schema(schema)},
            },
        }
        h = request_hash(request)
        hit = self._find(h)
        if hit is not None:
            with self._lock:
                self.cached += 1
            return schema.model_validate(json.loads(hit.read_text(encoding="utf-8"))["output"]), h
        if self.mode == "replay":
            raise LLMNotRecorded(f"LLM answer {h} not recorded; replay mode makes no live calls")
        with self._lock:
            if self.spent_so_far() >= self.spend_limit_usd:
                raise SpendLimitReached(
                    f"saved LLM calls cost ${self.spent_so_far():.2f}, the limit in unpaid.toml is "
                    f"${self.spend_limit_usd:.2f}; no call was made"
                )
        url, _ = PROVIDERS[self.provider]
        body = {**request, "provider": ROUTING, "usage": {"include": True}}
        try:
            with httpx.Client(transport=self.transport, timeout=300) as http:
                r = http.post(url, json=body, headers={"Authorization": f"Bearer {self.key}"})
        except httpx.HTTPError as e:
            raise LLMError(f"LLM call failed: {type(e).__name__}") from None
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code != 200 or "choices" not in data:
            err = data.get("error") or {}
            msg = err.get("message") if isinstance(err, dict) else err
            raise LLMError(f"LLM HTTP {r.status_code}: {msg or 'no message'}")
        output = schema.model_validate_json(data["choices"][0]["message"]["content"])
        usage = data.get("usage") or {}
        record = {
            "request": request,
            "output": output.model_dump(mode="json"),
            "usage": usage,
            "served_by": {"model": data.get("model"), "provider": data.get("provider"), "id": data.get("id")},
        }
        text = json.dumps(record, ensure_ascii=False, indent=1)
        if self.key and self.key in text:
            raise LLMError("refusing to save an LLM answer that contains the API key")
        with self._lock:
            self.write_dir.mkdir(parents=True, exist_ok=True)
            (self.write_dir / f"{h}.json").write_text(text, encoding="utf-8")
            self.calls += 1
            self.cost_usd += float(usage.get("cost") or 0.0)
        return output, h
