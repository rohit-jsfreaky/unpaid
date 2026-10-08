"""Collect: a plan's YouTube searches → pick the recent review videos → open each one → read its transcript.

The budget is checked before each stage, so a run never starts a stage it can't finish.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from unpaid import youtube as yt
from unpaid.config import Settings
from unpaid.serpapi import Client, SerpApiError

Event = dict[str, Any]
OnEvent = Callable[[Event], None]


class Query(BaseModel):
    text: str
    hl: str


class Plan(BaseModel):
    question: str
    queries: list[Query]
    # A video is opened only if its title matches this (e.g. it names the budget).
    title_pattern: str
    window_days: int
    max_videos: int
    # What the shopper said matters ("camera", "battery"). Not used to search; used to rank what reviewers praise.
    must_haves: list[str] = Field(default_factory=list)


def showcase_plan(s: Settings) -> Plan:
    """The recorded demo question. Step 5 makes the same kind of plan from free text."""
    return Plan(
        question="best phone under 30k for camera and battery, big billion days",
        queries=[
            Query(text="best phone under 30000", hl="en"),
            Query(text="best phone under 30000 big billion days", hl="en"),
            Query(text="best phone under 30000 hindi", hl="hi"),
        ],
        title_pattern=r"30\s?k\b|30,?000|₹\s?30\b|30\s?(?:हज़ार|हजार)",
        window_days=s.window_days,
        max_videos=s.max_videos,
        must_haves=["camera", "battery"],
    )


class Dropped(BaseModel):
    video_id: str
    title: str
    channel: str
    reason: str


class Video(BaseModel):
    hit: yt.Hit
    found_by: list[str]
    page: yt.VideoPage | None = None
    transcript: yt.Transcript | None = None
    problem: str | None = None


class Recording(BaseModel):
    """How the live recording went. Written once by a live run; replays never touch it."""

    started_at: datetime
    elapsed_s: float
    searches_used: int
    videos_opened: int
    transcripts_read: int


class Collection(BaseModel):
    plan: Plan
    gl: str
    mode: str
    started_at: datetime
    elapsed_s: float
    searches_used: int
    searches: list[yt.SearchPage]
    videos: list[Video]
    dropped: list[Dropped]


def select(pages: list[yt.SearchPage], plan: Plan) -> tuple[list[Video], list[Dropped]]:
    """Unique videos in search order; keep recent ones whose title matches; cap by views."""
    seen: dict[str, Video] = {}
    for page in pages:
        for h in page.hits:
            label = f"{page.hl}: {page.query}"
            if h.video_id in seen:
                if label not in seen[h.video_id].found_by:
                    seen[h.video_id].found_by.append(label)
            else:
                seen[h.video_id] = Video(hit=h, found_by=[label])
    pattern = re.compile(plan.title_pattern, re.IGNORECASE)
    keep: list[Video] = []
    dropped: list[Dropped] = []

    def drop(v: Video, reason: str) -> None:
        dropped.append(Dropped(video_id=v.hit.video_id, title=v.hit.title, channel=v.hit.channel, reason=reason))

    for v in seen.values():
        if v.hit.age_days is None:
            drop(v, f"upload date unreadable ({v.hit.published_text!r})")
        elif v.hit.age_days > plan.window_days:
            drop(v, f"older than {plan.window_days} days ({v.hit.published_text})")
        elif not pattern.search(v.hit.title):
            drop(v, "title doesn't name the budget")
        else:
            keep.append(v)
    keep.sort(key=lambda v: v.hit.views or 0, reverse=True)
    for v in keep[plan.max_videos :]:
        drop(v, f"over the {plan.max_videos}-video limit (fewer views)")
    return keep[: plan.max_videos], dropped


def collect(
    client: Client, plan: Plan, gl: str, open_videos: bool = True, on_event: OnEvent | None = None
) -> Collection:
    emit = on_event or (lambda _e: None)
    started, t0 = datetime.now(UTC), time.perf_counter()

    params = [yt.search_params(q.text, q.hl, gl) for q in plan.queries]
    client.check_budget(len(client.missing(params)))
    pages: list[yt.SearchPage] = []
    for q in plan.queries:
        emit({"type": "tool", "tool": "youtube", "query": q.text, "hl": q.hl, "status": "start"})
        page = yt.search(client, q.text, q.hl, gl)
        pages.append(page)
        emit({"type": "tool", "tool": "youtube", "query": q.text, "hl": q.hl, "status": "done", "hits": len(page.hits)})

    videos, dropped = select(pages, plan)
    emit({"type": "selected", "keep": len(videos), "dropped": len(dropped)})

    if open_videos:
        # Upper bound: every video has a transcript.
        needed = [yt.video_params(v.hit.video_id, gl) for v in videos] + [
            yt.transcript_params(v.hit.video_id) for v in videos
        ]
        client.check_budget(len(client.missing(needed)))

        def open_one(v: Video) -> Video:
            vid = v.hit.video_id
            try:
                emit({"type": "tool", "tool": "youtube_video", "v": vid, "status": "start"})
                v.page = yt.video(client, vid, gl)
                emit({"type": "tool", "tool": "youtube_video", "v": vid, "status": "done"})
                if not v.page.has_transcript:
                    v.problem = "YouTube shows no transcript for this video"
                    return v
                emit({"type": "tool", "tool": "youtube_video_transcript", "v": vid, "status": "start"})
                v.transcript = yt.transcript(client, vid)
                if not v.transcript.segments:
                    v.problem = f"no transcript: {v.transcript.error or 'SerpApi returned no lines'}"
                emit(
                    {
                        "type": "tool",
                        "tool": "youtube_video_transcript",
                        "v": vid,
                        "status": "done",
                        "segments": len(v.transcript.segments),
                    }
                )
            except SerpApiError as e:
                v.problem = str(e)
                emit({"type": "tool", "v": vid, "status": "error", "detail": str(e)})
            return v

        with ThreadPoolExecutor(max_workers=6) as pool:
            videos = list(pool.map(open_one, videos))

    return Collection(
        plan=plan,
        gl=gl,
        mode=client.mode,
        started_at=started,
        elapsed_s=round(time.perf_counter() - t0, 1),
        searches_used=client.searches_used,
        searches=pages,
        videos=videos,
        dropped=dropped,
    )


def recording_of(run: Collection) -> Recording:
    return Recording(
        started_at=run.started_at,
        elapsed_s=run.elapsed_s,
        searches_used=run.searches_used,
        videos_opened=sum(v.page is not None for v in run.videos),
        transcripts_read=sum(bool(v.transcript and v.transcript.segments) for v in run.videos),
    )
