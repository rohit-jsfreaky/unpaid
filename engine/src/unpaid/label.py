"""Label every collected video: check its links, ask the LLM for sentences, keep only what code can prove."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel

from unpaid.collect import Collection, OnEvent, Video
from unpaid.extract import extract
from unpaid.links import LinkBook
from unpaid.llm import LLM
from unpaid.proof import Proven, prove


class Labelled(BaseModel):
    model: str
    llm_calls: int
    llm_cached: int
    llm_cost_usd: float
    videos: list[Proven]


def label_all(run: Collection, llm: LLM, book: LinkBook, on_event: OnEvent | None = None) -> Labelled:
    emit = on_event or (lambda _e: None)
    checked = book.check_all([x.url for v in run.videos if v.page for x in v.page.links])
    emit({"type": "tool", "tool": "links", "step": "follow description links", "status": "done", "checked": checked})

    def one(v: Video) -> Proven | None:
        if v.page is None:
            return None
        emit({"type": "tool", "tool": "llm", "step": "find disclosures", "v": v.hit.video_id, "status": "start"})
        ex, h = extract(llm, v.page, v.transcript)
        p = prove(v.hit, v.page, v.transcript, ex, h, book)
        emit(
            {
                "type": "video",
                "v": p.video_id,
                "channel": p.channel,
                "labels": p.label_names,
                "picks": len(p.picks),
                "dropped": len(p.dropped),
            }
        )
        return p

    with ThreadPoolExecutor(max_workers=6) as pool:
        proven = [p for p in pool.map(one, run.videos) if p is not None]
    return Labelled(
        model=llm.model,
        llm_calls=llm.calls,
        llm_cached=llm.cached,
        llm_cost_usd=round(llm.cost_usd, 6),
        videos=proven,
    )


def showcase_paths(showcase: Path) -> tuple[Path, Path, Path]:
    """(saved LLM answers, link checks, labels) for a recorded run folder."""
    return showcase / "llm", showcase / "links.json", showcase / "labels.json"
