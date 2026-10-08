"""Unpaid: which YouTube reviewers disclosed being paid, given the product, or earning commission."""

from __future__ import annotations

import argparse
import json

from unpaid.serpapi import Client, fetch_account


def _collect(args: argparse.Namespace) -> None:
    from unpaid.collect import collect, recording_of, showcase_plan
    from unpaid.config import SHOWCASE_DIR, load_settings
    from unpaid.serpapi import Cache

    settings = load_settings()
    client = Client.from_env("replay" if args.replay else None)
    # The showcase records into its own folder and reads only from it, so the frozen run is self-contained.
    client.cache = Cache(write_dir=SHOWCASE_DIR / "serpapi", read_dirs=(SHOWCASE_DIR,))
    run = collect(client, showcase_plan(settings), settings.gl, open_videos=not args.searches_only, on_event=print)
    for v in run.videos:
        t = v.transcript
        said = v.problem or (f"{len(t.segments)} seg {t.script}" if t else "not opened")
        when = v.hit.published_text or "?"
        print(f"KEEP  {v.hit.views or 0:>8}  {when:<14} {v.hit.channel[:22]:<22} {v.hit.title[:60]} | {said}")
    for d in run.dropped:
        print(f"DROP  {d.channel[:22]:<22} {d.title[:60]} | {d.reason}")
    print(f"\n{len(run.videos)} kept, {len(run.dropped)} dropped, {run.searches_used} searches used, {run.elapsed_s}s")
    if not args.searches_only:
        out = SHOWCASE_DIR / "collection.json"
        out.write_text(run.model_dump_json(indent=1), encoding="utf-8")
        print(f"wrote {out}")
        if run.mode == "live" and run.searches_used:
            rec = SHOWCASE_DIR / "recording.json"
            rec.write_text(recording_of(run).model_dump_json(indent=1), encoding="utf-8")
            print(f"wrote {rec}")


def _label(args: argparse.Namespace) -> None:
    from unpaid.collect import Collection
    from unpaid.config import SHOWCASE_DIR
    from unpaid.label import Labelled, label_all, showcase_paths
    from unpaid.links import LinkBook
    from unpaid.llm import LLM

    run = Collection.model_validate_json((SHOWCASE_DIR / "collection.json").read_text(encoding="utf-8"))
    llm_dir, links_file, out = showcase_paths(SHOWCASE_DIR)
    llm = LLM.from_env(write_dir=llm_dir, read_dirs=(llm_dir,), mode="replay" if args.replay else None)
    book = LinkBook(links_file, live=not args.replay)
    result = label_all(run, llm, book)
    for v in result.videos:
        names = ", ".join(v.label_names)
        counts = f"picks={len(v.picks)} dropped={len(v.dropped)} denials={len(v.denials)}"
        print(f"{v.channel[:22]:<22} {names:<45} {counts}")
        for e in v.labels:
            print(f"    {e.label}: [{e.source} {e.time_text or ''}] {e.quote[:90]!r} ({e.party})")
        for d in v.dropped:
            print(f"    x {d.kind}: {d.reason}: {d.quote[:80]!r}")
    print()
    print(f"{result.model}: {result.llm_calls} calls, {result.llm_cached} from disk, ${result.llm_cost_usd:.4f}")
    if args.replay and out.exists():
        # A replay re-proves the saved answers; the recording's own call count and cost stay as recorded.
        before = Labelled.model_validate_json(out.read_text(encoding="utf-8"))
        result = result.model_copy(
            update={"llm_calls": before.llm_calls, "llm_cached": before.llm_cached, "llm_cost_usd": before.llm_cost_usd}
        )
    out.write_text(result.model_dump_json(indent=1), encoding="utf-8")
    print(f"wrote {out}")


def _board(args: argparse.Namespace) -> None:
    from unpaid.board import build
    from unpaid.config import SHOWCASE_DIR
    from unpaid.serpapi import Cache

    client = Client.from_env("replay" if args.replay else None)
    client.cache = Cache(write_dir=SHOWCASE_DIR / "serpapi", read_dirs=(SHOWCASE_DIR,))
    show = build(SHOWCASE_DIR, client)
    for pp in show.prices:
        print(f"{pp.phone}: {len(pp.offers)} sellers, {pp.skipped} other results skipped")
        for o in pp.offers[:6]:
            print(f"    Rs {o.price:>7,}  {o.seller:<22} {o.title[:70]}")
    print(f"top (all): {show.board.top_all}")
    print(f"top (no disclosure): {show.board.top_no_disclosure}")
    print(f"{client.searches_used} searches used")
    out = SHOWCASE_DIR / "board.json"
    out.write_text(show.model_dump_json(indent=1), encoding="utf-8")
    print(f"wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="unpaid")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("account", help="show SerpApi searches left (free call)")
    c = sub.add_parser("collect", help="record (or replay) the showcase question's videos and transcripts")
    c.add_argument("--replay", action="store_true", help="never call SerpApi, use the recorded files only")
    c.add_argument(
        "--searches-only", action="store_true", help="run the YouTube searches and show the pick, open nothing"
    )
    lb = sub.add_parser("label", help="label the recorded showcase videos (LLM finds, code proves)")
    lb.add_argument("--replay", action="store_true", help="use saved LLM answers and link checks only")
    bd = sub.add_parser("board", help="rank the phones and fetch live prices for the top ones")
    bd.add_argument("--replay", action="store_true", help="use recorded prices only")
    q = sub.add_parser("ask", help="ask a buying question; prints every step, then the top picks")
    q.add_argument("question")
    q.add_argument("--replay", action="store_true", help="answer only from recorded runs (no keys, no spend)")
    q.add_argument("--record-showcase", action="store_true", help="save new LLM answers into the showcase evidence")
    q.add_argument("--record-into", help="record the whole run into this evidence folder (replays for judges)")
    us = sub.add_parser("uses", help="find what each recommended phone is good at (LLM finds, code proves)")
    us.add_argument("--replay", action="store_true", help="use saved LLM answers only")
    sub.add_parser("site", help="export the landing page's real examples (web/content/landing.json)")
    sv = sub.add_parser("serve", help="run the API on localhost")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--reload", action="store_true", help="restart when engine code changes (development)")
    args = parser.parse_args()

    if args.cmd == "account":
        client = Client.from_env("live")
        assert client.key
        info = fetch_account(client.key)
        print(json.dumps({k: info.get(k) for k in ("plan_name", "total_searches_left", "this_month_usage")}))
    elif args.cmd == "collect":
        _collect(args)
    elif args.cmd == "label":
        _label(args)
    elif args.cmd == "board":
        _board(args)
    elif args.cmd == "ask":
        _ask(args)
    elif args.cmd == "site":
        _site()
    elif args.cmd == "uses":
        _uses(args)
    elif args.cmd == "serve":
        import uvicorn

        uvicorn.run("unpaid.api:app", host="127.0.0.1", port=args.port, reload=args.reload)


def _uses(args: argparse.Namespace) -> None:
    from unpaid.board import USES_FILE
    from unpaid.collect import Collection
    from unpaid.config import SHOWCASE_DIR
    from unpaid.label import Labelled, showcase_paths
    from unpaid.llm import LLM
    from unpaid.uses import FoundUses, find_uses

    run = Collection.model_validate_json((SHOWCASE_DIR / "collection.json").read_text(encoding="utf-8"))
    labelled = Labelled.model_validate_json(showcase_paths(SHOWCASE_DIR)[2].read_text(encoding="utf-8"))
    llm_dir = showcase_paths(SHOWCASE_DIR)[0]
    llm = LLM.from_env(write_dir=llm_dir, read_dirs=(llm_dir,), mode="replay" if args.replay else None)
    found = find_uses(run, labelled.videos, llm)
    names = {v.video_id: v.channel for v in labelled.videos}
    for vu in found.videos:
        print(f"{names[vu.video_id][:22]:<22} kept {len(vu.uses):>2}  dropped {len(vu.dropped):>2}")
        for u in vu.uses:
            print(f"    {u.verdict:<4} {u.area:<11} {u.phone[:26]:<26} [{u.time_text or 'desc'}] {u.quote[:70]!r}")
        for d in vu.dropped:
            print(f"    x {d.kind}: {d.reason}: {d.quote[:60]!r}")
    print(f"\n{found.model}: {found.llm_calls} calls, ${found.llm_cost_usd:.4f}")
    out = SHOWCASE_DIR / USES_FILE
    if args.replay and out.exists():
        # A replay re-proves the saved answers; the recording's own call count and cost stay as recorded.
        before = FoundUses.model_validate_json(out.read_text(encoding="utf-8"))
        found = found.model_copy(update={"llm_calls": before.llm_calls, "llm_cost_usd": before.llm_cost_usd})
    out.write_text(found.model_dump_json(indent=1), encoding="utf-8")
    print(f"wrote {out}")


def _site() -> None:
    from unpaid.board import Showcase
    from unpaid.config import EVIDENCE_DIR, SHOWCASE_DIR
    from unpaid.label import showcase_paths
    from unpaid.links import LinkBook
    from unpaid.site import LANDING_FILE, render

    show = Showcase.model_validate_json((SHOWCASE_DIR / "board.json").read_text(encoding="utf-8"))
    numbers = json.loads((EVIDENCE_DIR / "numbers.json").read_text(encoding="utf-8"))
    book = LinkBook(showcase_paths(SHOWCASE_DIR)[1], live=False)
    LANDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    LANDING_FILE.write_text(render(show, book, numbers["labels"]["answer_key"]), encoding="utf-8")
    print(f"wrote {LANDING_FILE}")


def _ask(args: argparse.Namespace) -> None:
    from pathlib import Path

    from unpaid.agent import Workspace, ask
    from unpaid.board import REPORT_FILE
    from unpaid.config import SHOWCASE_DIR

    if args.record_into:
        # A recorded run: SerpApi files, LLM answers, link checks and the report all go into one evidence folder.
        root = Path(args.record_into).resolve()
        ws = Workspace.open(replay=args.replay, root=root)
    else:
        ws = Workspace.open(replay=args.replay, llm_dir=SHOWCASE_DIR / "llm" if args.record_showcase else None)

    def show(e: dict[str, object]) -> None:
        if e.get("type") == "tool" and e.get("status") == "start":
            return
        print(json.dumps(e, ensure_ascii=False)[:200])

    result = ask(args.question, ws, on_event=show)
    b = result.board
    print(f"\ntop (all): {b.top_all}\ntop (no disclosure): {b.top_no_disclosure}")
    for a in result.areas:
        if a.focus:
            print(f"best for {a.area}: {a.best_no_disclosure} (no disclosure) / {a.best_all} (all)")
    print(f"searches used: {ws.client.searches_used}; LLM calls: {ws.llm.calls} new, {ws.llm.cached} saved")
    if args.record_into:
        out = Path(args.record_into) / REPORT_FILE
        out.write_text(result.model_dump_json(indent=1), encoding="utf-8")
        print(f"wrote {out}")
