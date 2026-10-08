"""The board for one question: labelled videos, what reviewers recommend, and live prices. From recorded files only."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from unpaid.aggregate import Board, tally
from unpaid.collect import Collection
from unpaid.label import Labelled, showcase_paths
from unpaid.prices import PhonePrices, prices
from unpaid.proof import Proven
from unpaid.serpapi import Client


class Showcase(BaseModel):
    question: str
    videos: list[Proven]
    board: Board
    prices: list[PhonePrices]


def build(showcase: Path, client: Client) -> Showcase:
    run = Collection.model_validate_json((showcase / "collection.json").read_text(encoding="utf-8"))
    labelled = Labelled.model_validate_json(showcase_paths(showcase)[2].read_text(encoding="utf-8"))
    board = tally(labelled.videos)
    phones = list(dict.fromkeys(board.top_all + board.top_no_disclosure))
    return Showcase(question=run.plan.question, videos=labelled.videos, board=board, prices=prices(client, phones))
