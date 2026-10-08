"""`uv run verify`: recompute every public claim from the raw SerpApi files and print PASS or FAIL.

The numbers it computes are written to evidence/numbers.json. README, UI and video copy those, never typed by hand.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

from unpaid.config import EVIDENCE_DIR, PROBE_DIR, ROOT, api_key, load_settings
from unpaid.serpapi import BudgetExceeded, Cache, Client, receipt

SKIP_DIRS = {".git", ".venv", "node_modules", ".next", "__pycache__", ".pytest_cache", ".ruff_cache"}
KEY_IN_URL = re.compile(r"api_key=[0-9a-f]{64}")


def _repo_files() -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        out += [Path(dirpath) / f for f in filenames if f != ".env"]
    return out


def checks() -> tuple[list[tuple[str, Callable[[], str]]], dict[str, object]]:
    numbers: dict[str, object] = {}
    out: list[tuple[str, Callable[[], str]]] = []

    def claim(text: str) -> Callable[[Callable[[], str]], Callable[[], str]]:
        def wrap(fn: Callable[[], str]) -> Callable[[], str]:
            out.append((text, fn))
            return fn

        return wrap

    @claim("The 7 Oct probes replay with no API key and no searches")
    def _() -> str:
        # Frozen probe folder only, so the result can't depend on what this laptop has cached since.
        client = Client(mode="replay", key=None, cache=Cache(write_dir=PROBE_DIR, read_dirs=(PROBE_DIR,)))
        hi = client.search(
            {"engine": "youtube", "search_query": "best phone under 30000 review hindi", "gl": "in", "hl": "hi"}
        )
        video = client.search({"engine": "youtube_video", "v": "k5itPbQtz_Y", "gl": "in"})
        transcript = client.search({"engine": "youtube_video_transcript", "v": "ZRVRBnrSNnc", "language_code": "en"})
        assert client.searches_used == 0 and hi.from_cache and video.from_cache and transcript.from_cache
        n = (len(hi.data["video_results"]), len(transcript.data["transcript"]))
        return f"Hindi search {n[0]} videos, transcript {n[1]} segments, 0 searches used"

    @claim("Every recorded SerpApi file carries its receipt (search id, json_endpoint, timestamp)")
    def _() -> str:
        files = sorted(EVIDENCE_DIR.rglob("*.json"))
        files = [p for p in files if p.name != "numbers.json"]
        assert files, "no recorded files"
        for path in files:
            doc = json.loads(path.read_text(encoding="utf-8"))
            r = receipt(doc.get("response", doc))
            assert r.search_id and r.json_endpoint.startswith("https://serpapi.com/searches/") and r.created_at, path
        return f"{len(files)} of {len(files)} files"

    @claim("Budget guard refuses a run that would cross the limit in unpaid.toml")
    def _() -> str:
        keep = load_settings().keep_at_least
        client = Client(
            mode="live", key="x" * 64, keep_at_least=keep, account=lambda _k: {"total_searches_left": keep + 3}
        )
        assert client.check_budget(3) == keep + 3
        try:
            client.check_budget(4)
        except BudgetExceeded:
            return f"keep_at_least={keep}: 3 allowed, 4 refused"
        raise AssertionError("4 searches were allowed")

    @claim("No API key in any repo file")
    def _() -> str:
        key = api_key()
        files = _repo_files()
        for path in files:
            text = path.read_bytes().decode("utf-8", errors="ignore")
            assert not KEY_IN_URL.search(text), path
            assert not key or key not in text, path
        return f"{len(files)} files scanned" + ("" if key else " (no local key: pattern scan only)")

    return out, numbers


def main() -> None:
    items, numbers = checks()
    failed = 0
    for text, fn in items:
        try:
            detail = fn()
            print(f"PASS  {text}\n      {detail}")
        except Exception as e:  # every failure is reported; none stops the others
            failed += 1
            print(f"FAIL  {text}\n      {type(e).__name__}: {e}")
    if not failed:
        (EVIDENCE_DIR / "numbers.json").write_text(json.dumps(numbers, indent=1) + "\n", encoding="utf-8")
    print(f"\n{len(items) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
