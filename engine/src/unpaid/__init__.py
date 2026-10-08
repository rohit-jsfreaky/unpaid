"""Unpaid: which YouTube reviewers disclosed being paid, given the product, or earning commission."""

from __future__ import annotations

import argparse
import json

from unpaid.serpapi import Client, fetch_account


def main() -> None:
    parser = argparse.ArgumentParser(prog="unpaid")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("account", help="show SerpApi searches left (free call)")
    args = parser.parse_args()

    if args.cmd == "account":
        client = Client.from_env("live")
        assert client.key
        info = fetch_account(client.key)
        print(json.dumps({k: info.get(k) for k in ("plan_name", "total_searches_left", "this_month_usage")}))
