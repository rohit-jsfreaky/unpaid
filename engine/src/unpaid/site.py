"""The landing page's real examples, exported from the recorded report. The website never types a number by hand.

`uv run unpaid site` writes web/content/landing.json; `uv run verify` fails if it differs from a fresh export.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from unpaid.board import Showcase
from unpaid.config import ROOT
from unpaid.links import LinkBook
from unpaid.proof import BRAND_SPONSORED, COMMISSION, NO_DISCLOSURE, Proven

LANDING_FILE = ROOT / "web" / "content" / "landing.json"
LANGUAGE = {"latin": "English", "devanagari": "Hindi", "telugu": "Telugu", "malayalam": "Malayalam"}


def _names(v: Proven) -> list[str]:
    return v.label_names


def landing(show: Showcase, book: LinkBook, answer_key: list[dict[str, Any]]) -> dict[str, Any]:
    reviews = {r.video_id: r for r in show.reviews}
    with_ties = [v for v in show.videos if v.labels]
    per_label = Counter(n for v in show.videos for n in _names(v))
    links = sum(1 for v in show.videos for x in v.labels if x.source == "description_link")
    paid_links = sum(1 for c in book.checks.values() if c.is_affiliate)

    def example(source: str, label: str) -> dict[str, Any]:
        v, e = next((v, e) for v in show.videos for e in v.labels if e.source == source and e.label == label)
        return {
            "channel": v.channel,
            "title": v.title,
            "top_pick": min(v.picks, key=lambda p: p.rank or 99).phone if v.picks else None,
            "label": e.label,
            "party": e.party,
            "quote": e.quote,
            "meaning_en": e.meaning_en,
            "time_text": e.time_text,
            "url": e.url,
            "language": LANGUAGE.get(reviews[v.video_id].language or "", "English"),
        }

    deny_v, deny = next((v, d) for v in show.videos for d in v.denials)
    b = show.board
    rows = []
    for v in sorted(show.videos, key=lambda v: -(v.views or 0)):
        top = min(v.picks, key=lambda p: p.rank or 99).phone if v.picks else None
        r = reviews[v.video_id]
        rows.append(
            {
                "channel": v.channel,
                "views": v.views,
                "published": r.published.isoformat() if r.published else None,
                "language": LANGUAGE.get(r.language or ""),
                "labels": _names(v),
                "top_pick": top,
            }
        )
    top_phone = b.top_all[0]
    top_prices = next(p for p in show.prices if p.phone == top_phone)
    return {
        "question": show.question,
        "checked_at": show.checked_at.isoformat(),
        "videos_found": show.videos_found,
        "reviews": len(show.videos),
        "with_ties": len(with_ties),
        "per_label": {k: per_label.get(k, 0) for k in (NO_DISCLOSURE, COMMISSION, BRAND_SPONSORED)},
        "videos_with_paid_links": links,
        "paid_links": paid_links,
        "languages": dict(Counter(LANGUAGE.get(r.language or "", "No captions") for r in show.reviews).most_common()),
        "brand_example": example("description", BRAND_SPONSORED),
        "spoken_example": example("transcript", COMMISSION),
        "denial_example": {
            "channel": deny_v.channel,
            "quote": deny.quote,
            "meaning_en": deny.meaning_en,
            "time_text": deny.time_text,
            "url": deny.url,
        },
        "groups": {
            "no_disclosure": b.no_disclosure_videos_with_picks,
            "disclosed": b.disclosed_videos_with_picks,
        },
        "phones": [
            {"name": p.name, "no_disclosure": p.no_disclosure, "disclosed": p.disclosed, "all": p.all}
            for p in b.phones[:5]
        ],
        "prices": {
            "phone": top_phone,
            "sellers": len(top_prices.offers),
            "offers": [
                {"seller": o.seller, "price": o.price, "searched_at": o.searched_at} for o in top_prices.offers[:4]
            ],
        },
        "rows": rows,
        "accuracy": [
            {k: s[k] for k in ("label", "key", "found", "right", "precision", "recall", "missed")}
            for s in answer_key
            if s["key"] or s["found"]
        ],
        "report_id": show.id,
    }


def render(show: Showcase, book: LinkBook, answer_key: list[dict[str, Any]]) -> str:
    return json.dumps(landing(show, book, answer_key), ensure_ascii=False, indent=1) + "\n"
