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
from unpaid.youtube import parse_created_at


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
    reviews: list[Review]
    videos: list[Proven]
    board: Board
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


def assemble(question: str, run: Collection, labelled: Labelled, found: list[PhonePrices]) -> Showcase:
    board = tally(labelled.videos)
    return Showcase(
        id=report_id(run),
        question=question,
        checked_at=run.searches[0].searched_at,
        searches=[s.query for s in run.searches],
        videos_found=len(run.videos) + len(run.dropped),
        reviews=reviews_of(run),
        videos=labelled.videos,
        board=board,
        prices=found,
    )


def top_phones(board: Board) -> list[str]:
    return list(dict.fromkeys(board.top_all + board.top_no_disclosure))


def build(showcase: Path, client: Client) -> Showcase:
    run = Collection.model_validate_json((showcase / "collection.json").read_text(encoding="utf-8"))
    labelled = Labelled.model_validate_json(showcase_paths(showcase)[2].read_text(encoding="utf-8"))
    return assemble(run.plan.question, run, labelled, prices(client, top_phones(tally(labelled.videos))))
