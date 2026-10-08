"""The report for one question: labelled videos, what reviewers recommend, and live prices.

`assemble` is the one place a report is put together, for the recorded showcase and for a new question alike.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel

from unpaid.aggregate import Board, tally
from unpaid.collect import Collection
from unpaid.label import Labelled, showcase_paths
from unpaid.prices import PhonePrices, prices
from unpaid.proof import Proven
from unpaid.serpapi import Client
from unpaid.uses import AreaBoard, FoundUses, areas_for, tally_uses
from unpaid.youtube import parse_created_at

USES_FILE = "uses.json"


class Review(BaseModel):
    """What the report shows about a video besides its labels."""

    video_id: str
    published: datetime | None  # the video page's date, or the search's relative age counted back
    published_text: str | None
    views: int | None
    length: str | None
    products_tagged: int | None  # YouTube's "N products" chip
    language: str | None  # the script of the captions we read, e.g. "devanagari"
    has_transcript: bool
    thumbnail: str


class Showcase(BaseModel):
    id: str
    question: str
    checked_at: datetime  # when the first search ran
    searches: list[str]  # what was searched on YouTube
    videos_found: int  # unique videos the searches returned
    must_haves: list[str]  # what the shopper said matters, in their words
    focus: list[str]  # those must-haves as areas we rank (camera, battery, ...)
    not_tracked: list[str]  # must-haves we don't rank, shown as such
    reviews: list[Review]
    videos: list[Proven]
    board: Board
    areas: list[AreaBoard]  # what reviewers praise each phone for; the shopper's areas first
    prices: list[PhonePrices]


def report_id(run: Collection) -> str:
    """ "best-phone-under-30000-2026-10-08": the first search, then the day it ran."""
    first = run.searches[0]
    slug = "-".join(re.findall(r"[a-z0-9]+", first.query.lower()))[:60]
    return f"{slug}-{first.searched_at:%Y-%m-%d}"


def reviews_of(run: Collection) -> list[Review]:
    out: list[Review] = []
    for v in run.videos:
        h, page, t = v.hit, v.page, v.transcript
        published = page.published if page and page.published else None
        if published is None and h.age_days is not None:
            published = parse_created_at(h.receipt.created_at) - timedelta(days=h.age_days)
        out.append(
            Review(
                video_id=h.video_id,
                published=published,
                published_text=page.published_text if page and page.published_text else h.published_text,
                views=(page.views if page and page.views else None) or h.views,
                length=h.length,
                products_tagged=h.products,
                language=t.script if t and t.segments else None,
                has_transcript=bool(t and t.segments),
                thumbnail=f"https://i.ytimg.com/vi/{h.video_id}/hqdefault.jpg",
            )
        )
    return out


def ranked(run: Collection, labelled: Labelled, uses: FoundUses) -> tuple[Board, list[AreaBoard], list[str]]:
    """The overall ranking, the per-area rankings, and must-haves we don't track (shown as such)."""
    board = tally(labelled.videos)
    focus, other = areas_for(run.plan.must_haves)
    return board, tally_uses(labelled.videos, uses, board, focus), other


def top_phones(board: Board, areas: list[AreaBoard]) -> list[str]:
    """Phones to price: the top three overall and without disclosure, plus the best for what the shopper wants."""
    best = [n for a in areas if a.focus for n in (a.best_no_disclosure, a.best_all) if n]
    return list(dict.fromkeys(board.top_all + board.top_no_disclosure + best))


def assemble(question: str, run: Collection, labelled: Labelled, uses: FoundUses, found: list[PhonePrices]) -> Showcase:
    board, areas, other = ranked(run, labelled, uses)
    return Showcase(
        id=report_id(run),
        question=question,
        checked_at=run.searches[0].searched_at,
        searches=[s.query for s in run.searches],
        videos_found=len(run.videos) + len(run.dropped),
        must_haves=run.plan.must_haves,
        focus=[a.area for a in areas if a.focus],
        not_tracked=other,
        reviews=reviews_of(run),
        videos=labelled.videos,
        board=board,
        areas=areas,
        prices=found,
    )


def build(showcase: Path, client: Client) -> Showcase:
    run = Collection.model_validate_json((showcase / "collection.json").read_text(encoding="utf-8"))
    labelled = Labelled.model_validate_json(showcase_paths(showcase)[2].read_text(encoding="utf-8"))
    uses = FoundUses.model_validate_json((showcase / USES_FILE).read_text(encoding="utf-8"))
    board, areas, _ = ranked(run, labelled, uses)
    return assemble(run.plan.question, run, labelled, uses, prices(client, top_phones(board, areas)))
