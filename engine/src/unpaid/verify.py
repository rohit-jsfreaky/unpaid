"""`uv run verify`: recompute every public claim from the raw SerpApi files and print PASS or FAIL.

The numbers it computes are written to evidence/numbers.json. README, UI and video copy those, never typed by hand.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from unpaid.agent import Workspace, ask
from unpaid.board import Showcase, build
from unpaid.collect import Collection, Plan, Recording, collect, showcase_plan
from unpaid.config import EVIDENCE_DIR, PROBE_DIR, ROOT, SHOWCASE_DIR, api_key, llm_key, load_settings
from unpaid.label import Labelled, label_all, showcase_paths
from unpaid.links import LinkBook
from unpaid.llm import LLM
from unpaid.proof import BRAND_SPONSORED, COMMISSION, LABELS, NO_DISCLOSURE, locate
from unpaid.score import load_key, score
from unpaid.serpapi import BudgetExceeded, Cache, Client, receipt

SKIP_DIRS = {".git", ".venv", "node_modules", ".next", "__pycache__", ".pytest_cache", ".ruff_cache"}
YOUTUBE_ENGINES = ("youtube", "youtube_video", "youtube_video_transcript")
KEY_IN_URL = re.compile(r"api_key=[0-9a-f]{64}")
OPENROUTER_KEY = re.compile(r"sk-or-v1-[0-9a-f]{32,}")


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
        files = [*PROBE_DIR.glob("*.json"), *(SHOWCASE_DIR / "serpapi").rglob("*.json")]
        assert files, "no recorded files"
        for path in files:
            doc = json.loads(path.read_text(encoding="utf-8"))
            r = receipt(doc.get("response", doc))
            assert r.search_id and r.json_endpoint.startswith("https://serpapi.com/searches/") and r.created_at, path
        return f"{len(files)} of {len(files)} files"

    settings = load_settings()
    replay = Client(mode="replay", key=None, cache=Cache(write_dir=SHOWCASE_DIR, read_dirs=(SHOWCASE_DIR,)))
    run = collect(replay, showcase_plan(settings), settings.gl)
    rec = Recording.model_validate_json((SHOWCASE_DIR / "recording.json").read_text(encoding="utf-8"))
    said = [v for v in run.videos if v.transcript and v.transcript.segments]
    scripts = Counter(v.transcript.script for v in said if v.transcript)
    numbers["showcase"] = {
        "question": run.plan.question,
        "searches": len(run.searches),
        "candidates": len(run.videos) + len(run.dropped),
        "videos": len(run.videos),
        "transcripts": len(said),
        "transcript_scripts": dict(scripts.most_common()),
        "recorded_elapsed_s": rec.elapsed_s,
        "recorded_searches": rec.searches_used + len(run.searches),
    }

    @claim("The showcase run replays with no API key and no searches, identical to collection.json")
    def _() -> str:
        frozen = Collection.model_validate_json((SHOWCASE_DIR / "collection.json").read_text(encoding="utf-8"))
        assert replay.searches_used == 0
        assert [v.model_dump() for v in run.videos] == [v.model_dump() for v in frozen.videos], "stale collection"
        assert run.dropped == frozen.dropped
        return f"{len(run.videos)} videos, {len(run.dropped)} dropped with a reason, 0 searches used"

    @claim("Recorded live: 21 videos opened and 18 transcripts read in one 42-search pass")
    def _() -> str:
        files = sum(len(list((SHOWCASE_DIR / "serpapi" / e).glob("*.json"))) for e in YOUTUBE_ENGINES)
        assert (rec.videos_opened, rec.transcripts_read, rec.searches_used) == (21, 18, 42), rec
        assert files == len(run.searches) + rec.searches_used == 45, files
        assert rec.transcripts_read == len(said)
        return f"{rec.elapsed_s}s on {rec.started_at:%d %b %H:%M} UTC; {files} YouTube SerpApi files on disk"

    @claim("Every opened video is recent and names the budget; every skipped one says why")
    def _() -> str:
        for v in run.videos:
            assert v.hit.age_days is not None and v.hit.age_days <= run.plan.window_days, v.hit.title
            assert re.search(run.plan.title_pattern, v.hit.title, re.IGNORECASE), v.hit.title
        assert all(d.reason for d in run.dropped)
        missing = [v for v in run.videos if not (v.transcript and v.transcript.segments)]
        assert all(v.problem for v in missing), [v.hit.video_id for v in missing if not v.problem]
        return f"no transcript from SerpApi: {', '.join(v.hit.channel for v in missing)}"

    @claim("Transcripts are read in the language YouTube returned (no translation step)")
    def _() -> str:
        assert set(scripts) <= {"latin", "devanagari", "telugu", "malayalam"}, scripts
        return ", ".join(f"{k} {n}" for k, n in scripts.most_common())

    llm_dir, links_file, labels_file = showcase_paths(SHOWCASE_DIR)
    frozen_labels = Labelled.model_validate_json(labels_file.read_text(encoding="utf-8"))
    by_id = {v.hit.video_id: v for v in run.videos}
    proven = frozen_labels.videos
    per_label = {x: sum(x in v.label_names for v in proven) for x in (*LABELS, NO_DISCLOSURE)}
    scores = score(proven, load_key(EVIDENCE_DIR / "answer-key.csv"))
    numbers["labels"] = {
        "videos": len(proven),
        "per_label": per_label,
        "model": frozen_labels.model,
        "llm_cost_usd": round(frozen_labels.llm_cost_usd, 4),
        "affiliate_links": sum(1 for c in LinkBook(links_file, live=False).checks.values() if c.is_affiliate),
        "answer_key": [s.model_dump() for s in scores],
    }

    @claim("Labels replay with no API key: saved LLM answers and link checks, 0 calls, identical to labels.json")
    def _() -> str:
        llm = LLM(mode="replay", model=frozen_labels.model, write_dir=llm_dir, read_dirs=(llm_dir,))
        again = label_all(run, llm, LinkBook(links_file, live=False))
        assert llm.calls == 0 and llm.cached == len(again.videos)
        assert [v.model_dump() for v in again.videos] == [v.model_dump() for v in proven], "stale labels.json"
        return f"{len(again.videos)} videos from {llm.cached} saved answers ({frozen_labels.model})"

    @claim("Every label has its receipt: a quote found word for word, a tagged link, or YouTube's own label")
    def _() -> str:
        book = LinkBook(links_file, live=False)
        n = 0
        for p in proven:
            v = by_id[p.video_id]
            assert v.page
            for e in p.labels:
                n += 1
                if e.source in ("description", "transcript"):
                    place = locate(e.quote, v.page, v.transcript, e.segment)
                    assert place and place.source == e.source and place.segment == e.segment, (p.channel, e.quote)
                elif e.source == "description_link":
                    assert e.quote in v.page.description, (p.channel, e.quote)
                    assert any((c := book.get(x.url)) and c.is_affiliate for x in v.page.links), p.channel
                else:
                    assert e.quote in v.hit.extensions, (p.channel, e.quote)
        return f"{n} labels on {sum(bool(p.labels) for p in proven)} videos; {per_label[NO_DISCLOSURE]} show " + (
            f"'{NO_DISCLOSURE}'"
        )

    @claim("We read what they say out loud: a label proven by a spoken transcript line, with its timestamp")
    def _() -> str:
        spoken = [(p, e) for p in proven for e in p.labels if e.source == "transcript"]
        assert spoken and all(e.time_text and "&t=" in e.url for _, e in spoken)
        p, e = spoken[0]
        return f"{p.channel} at {e.time_text}: {e.quote!r} ({e.meaning_en})"

    @claim("Traps stay unlabelled: 'not sponsored', inquiry lines and channel disclaimers")
    def _() -> str:
        named = {p.channel: p for p in proven}
        assert named["Tech Buffet"].label_names == [NO_DISCLOSURE] and named["Tech Buffet"].denials
        assert named["Techy Pathshala"].label_names == [NO_DISCLOSURE] and named["Techy Pathshala"].denials
        assert named["Madan Gaikwad"].label_names == [NO_DISCLOSURE]  # "ALL CONTENT PROVIDED BY THIS CHANNEL"
        assert named["Harsh Gamer"].label_names == [NO_DISCLOSURE]  # same disclaimer
        assert BRAND_SPONSORED not in named["Harshit Technical"].label_names  # "For Sponsorship ... inquiries"
        assert named["Harshit Technical"].label_names == [COMMISSION]
        return "Tech Buffet + Techy Pathshala denials shown as notes, not labels"

    @claim("Answer key (21 videos, every line read): precision and recall per label")
    def _() -> str:
        rows = [s for s in scores if s.key or s.found]
        assert all(s.key + s.found > 0 for s in rows)

        def pct(x: float | None) -> str:
            return "-" if x is None else f"{x:.0%}"

        lines = [
            f"{s.label}: precision {pct(s.precision)} ({s.right}/{s.found}), recall {pct(s.recall)} ({s.right}/{s.key})"
            + (f"; missed {', '.join(s.missed)}" if s.missed else "")
            + (f"; wrong {', '.join(s.wrong)}" if s.wrong else "")
            for s in rows
        ]
        return "\n      ".join(lines)

    shop_client = Client(mode="replay", key=None, cache=Cache(write_dir=SHOWCASE_DIR, read_dirs=(SHOWCASE_DIR,)))
    show = build(SHOWCASE_DIR, shop_client)
    board = show.board
    numbers["board"] = {
        "videos_with_picks": board.videos_with_picks,
        "no_disclosure_videos_with_picks": board.no_disclosure_videos_with_picks,
        "disclosed_videos_with_picks": board.disclosed_videos_with_picks,
        "top_all": board.top_all,
        "top_no_disclosure": board.top_no_disclosure,
        "phones": [p.model_dump(exclude={"mentions"}) for p in board.phones[:10]],
        "lowest_price": {pp.phone: pp.lowest.model_dump() if pp.lowest else None for pp in show.prices},
    }

    @claim("The board replays with no API key: rankings and Google Shopping prices, 0 searches, = board.json")
    def _() -> str:
        frozen = Showcase.model_validate_json((SHOWCASE_DIR / "board.json").read_text(encoding="utf-8"))
        assert shop_client.searches_used == 0 and frozen == show, "stale board.json: run uv run unpaid board"
        return f"{len(board.phones)} phones from {board.videos_with_picks} videos; prices for {len(show.prices)}"

    @claim("What reviewers recommend: all of them vs only those with no disclosure found")
    def _() -> str:
        rows = []
        for p in board.phones[:5]:
            rows.append(
                f"{p.name}: {p.no_disclosure}/{board.no_disclosure_videos_with_picks} no-disclosure videos, "
                f"{p.disclosed}/{board.disclosed_videos_with_picks} disclosed"
            )
        assert all(p.all == p.no_disclosure + p.disclosed for p in board.phones)
        assert sum(len(p.mentions) for p in board.phones) == sum(p.all for p in board.phones)
        top = f"top 3 all: {', '.join(board.top_all)} | top 3 no disclosure: {', '.join(board.top_no_disclosure)}"
        return "\n      ".join([top, *rows])

    @claim("Every price comes from a recorded Google Shopping search, cheapest per seller, phone matched by title")
    def _() -> str:
        ids = {
            json.loads(f.read_text(encoding="utf-8"))["response"]["search_metadata"]["id"]
            for f in (SHOWCASE_DIR / "serpapi" / "google_shopping").glob("*.json")
        }
        out = []
        for pp in show.prices:
            assert all(o.search_id in ids for o in pp.offers)
            assert [o.price for o in pp.offers] == sorted(o.price for o in pp.offers)
            low = pp.lowest
            said = f"Rs {low.price:,} at {low.seller} ({len(pp.offers)} sellers)" if low else "— (no listing found)"
            out.append(f"{pp.phone}: {said}")
        return "; ".join(out)

    @claim("Ask in plain words: the agent plans the recorded searches and rebuilds the board (no keys, 0 spend)")
    def _() -> str:
        with tempfile.TemporaryDirectory() as tmp:  # nothing cached on this machine can help
            ws = Workspace.open(replay=True, root=Path(tmp))
            plans: list[dict[str, object]] = []
            again = ask(run.plan.question, ws, on_event=lambda e: plans.append(e) if e["type"] == "plan" else None)
        assert plans and Plan.model_validate(plans[0]["plan"]) == showcase_plan(settings)
        assert ws.client.searches_used == 0 and ws.llm.calls == 0
        assert again == show, "the agent's board differs from board.json"
        queries = ", ".join(f"{q.text!r} ({q.hl})" for q in run.plan.queries)
        return f"{run.plan.question!r} → {queries}"

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
        keys = [k for k in (api_key(), llm_key("OPENROUTER_API_KEY")) if k]
        files = _repo_files()
        for path in files:
            text = path.read_bytes().decode("utf-8", errors="ignore")
            assert not KEY_IN_URL.search(text) and not OPENROUTER_KEY.search(text), path
            assert not any(k in text for k in keys), path
        return f"{len(files)} files scanned for SerpApi + OpenRouter keys" + (
            "" if keys else " (no local keys: pattern scan only)"
        )

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
