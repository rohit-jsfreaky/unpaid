"""Paths and settings. Everything a run depends on comes from unpaid.toml and .env."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(os.environ.get("UNPAID_ROOT", Path(__file__).resolve().parents[3]))
CACHE_DIR = ROOT / "cache"
EVIDENCE_DIR = ROOT / "evidence"
PROBE_DIR = EVIDENCE_DIR / "probe-2026-10-07"
# The recorded demo run: raw SerpApi files in serpapi/, the run itself in collection.json.
SHOWCASE_DIR = EVIDENCE_DIR / "showcase-2026-10-08"


@dataclass(frozen=True)
class Settings:
    keep_at_least: int
    gl: str
    languages: tuple[str, ...]
    window_days: int
    max_videos: int


def load_settings(path: Path | None = None) -> Settings:
    raw = tomllib.loads((path or ROOT / "unpaid.toml").read_text(encoding="utf-8"))
    budget, yt = raw["budget"], raw["youtube"]
    return Settings(
        keep_at_least=int(budget["keep_at_least"]),
        gl=str(yt["gl"]),
        languages=tuple(yt["languages"]),
        window_days=int(yt["window_days"]),
        max_videos=int(yt["max_videos"]),
    )


def api_key() -> str | None:
    """The SerpApi key, from the environment or .env. None means replay only."""
    load_dotenv(ROOT / ".env")
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    return key or None
