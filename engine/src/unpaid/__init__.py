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
    from unpaid.label import label_all, showcase_paths
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
