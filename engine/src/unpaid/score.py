"""Precision and recall of the labels against the hand-made answer key (evidence/answer-key.csv)."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel

from unpaid.proof import LABELS, NO_DISCLOSURE, Proven


class LabelScore(BaseModel):
    label: str
    key: int  # videos the answer key gives this label
    found: int  # videos the product gives this label
    right: int  # both
    precision: float | None  # None when the product gave the label to no video
    recall: float | None  # None when the key has no such video
    missed: list[str]
    wrong: list[str]


def load_key(path: Path) -> dict[str, set[str]]:
    key: dict[str, set[str]] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key.setdefault(row["video_id"], set()).add(row["label"])
    return key


def score(videos: list[Proven], key: dict[str, set[str]]) -> list[LabelScore]:
    got = {v.video_id: set(v.label_names) for v in videos if v.video_id in key}
    names = {v.video_id: v.channel for v in videos}
    out: list[LabelScore] = []
    for label in (*LABELS, NO_DISCLOSURE):
        k = {vid for vid, s in key.items() if label in s}
        f = {vid for vid, s in got.items() if label in s}
        right = k & f
        out.append(
            LabelScore(
                label=label,
                key=len(k),
                found=len(f),
                right=len(right),
                precision=round(len(right) / len(f), 3) if f else None,
                recall=round(len(right) / len(k), 3) if k else None,
                missed=sorted(names.get(v, v) for v in k - f),
                wrong=sorted(names.get(v, v) for v in f - k),
            )
        )
    return out
