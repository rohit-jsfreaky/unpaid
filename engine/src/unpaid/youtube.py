"""The three YouTube tools (search, video page, transcript) and their parsers.

Every field comes from a SerpApi response. Anything we can't read stays None; callers show "—" with the reason.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from unpaid.serpapi import Client, Params, Receipt, receipt

# YouTube's own commerce labels, as they appear in `extensions` (hl=en / hl=hi).
COMMISSION_LABELS = {"Earns commission", "कमीशन मिलेगा"}
NEW_LABELS = {"New", "नया"}
PRODUCTS_RE = re.compile(r"^(\d+)\s*(?:products?|प्रॉडक्ट)$")

# Relative ages: "12 hours ago", "7mo ago", "1y ago", "12 घं॰ पहले", "3 सप्ताह पहले", "8 माह पहले".
AGE_RE = re.compile(r"(\d+)\s*([^\d\s]+(?:\s[^\d\s]+)?)\s*(?:ago|पहले)")
AGE_UNITS: list[tuple[tuple[str, ...], float]] = [
    (("second", "seconds", "s", "सेकंड"), 1 / 86400),
    (("minute", "minutes", "min", "mins", "मिनट"), 1 / 1440),
    (("hour", "hours", "h", "hr", "hrs", "घं॰", "घंटे", "घंटा"), 1 / 24),
    (("day", "days", "d", "दिन"), 1),
    (("week", "weeks", "w", "wk", "wks", "सप्ताह", "हफ़्ते", "हफ्ते"), 7),
    (("month", "months", "mo", "mos", "माह", "महीने", "महीना"), 30),
    (("year", "years", "y", "yr", "yrs", "वर्ष", "साल"), 365),
]
DATE_RE = re.compile(r"([A-Z][a-z]{2}) (\d{1,2}), (\d{4})")


def age_in_days(text: str | None) -> float | None:
    """Days since upload from YouTube's relative text, in English or Hindi. None if we can't read it."""
    if not text:
        return None
    m = AGE_RE.search(text)
    if not m:
        return None
    unit = m.group(2).strip()
    for names, days in AGE_UNITS:
        if unit in names:
            return int(m.group(1)) * days
    return None


def parse_created_at(text: str) -> datetime:
    return datetime.strptime(text.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def parse_upload_date(text: str | None, searched_at: datetime) -> datetime | None:
    """`Jul 2, 2025` (video page, hl=en), or a relative age counted back from when SerpApi ran the search."""
    if not text:
        return None
    m = DATE_RE.search(text)
    if m:
        return datetime.strptime(" ".join(m.groups()), "%b %d %Y").replace(tzinfo=UTC)
    age = age_in_days(text)
    return None if age is None else searched_at - timedelta(days=age)


def video_id_of(link: str) -> str | None:
    m = re.search(r"[?&]v=([\w-]{11})", link)
    return m.group(1) if m else None


class Hit(BaseModel):
    """One video in a YouTube search result."""

    video_id: str
    title: str
    link: str
    channel: str
    channel_link: str | None
    views: int | None
    length: str | None
    published_text: str | None
    age_days: float | None
    snippet: str | None
    extensions: list[str]
    earns_commission: bool
    products: int | None
    query: str
    hl: str
    position: int
    receipt: Receipt


class SearchPage(BaseModel):
    query: str
    hl: str
    searched_at: datetime
    hits: list[Hit]
    receipt: Receipt


def search_params(query: str, hl: str, gl: str) -> Params:
    return {"engine": "youtube", "search_query": query, "gl": gl, "hl": hl}


def parse_search(data: dict[str, Any], query: str, hl: str) -> SearchPage:
    r = receipt(data)
    hits: list[Hit] = []
    for i, v in enumerate(data.get("video_results") or [], start=1):
        link = str(v.get("link") or "")
        vid = v.get("video_id") or video_id_of(link)
        if not vid:
            continue
        ext = [str(x) for x in v.get("extensions") or []]
        products = next((int(m.group(1)) for x in ext if (m := PRODUCTS_RE.match(x.strip()))), None)
        channel = v.get("channel") or {}
        views = v.get("views")
        hits.append(
            Hit(
                video_id=str(vid),
                title=str(v.get("title") or ""),
                link=link,
                channel=str(channel.get("name") or ""),
                channel_link=channel.get("link"),
                views=views if isinstance(views, int) else None,
                length=v.get("length"),
                published_text=v.get("published_date"),
                age_days=age_in_days(v.get("published_date")),
                snippet=v.get("description"),
                extensions=ext,
                earns_commission=any(x.strip() in COMMISSION_LABELS for x in ext),
                products=products,
                query=query,
                hl=hl,
                position=int(v.get("position_on_page") or i),
                receipt=r,
            )
        )
    return SearchPage(query=query, hl=hl, searched_at=parse_created_at(r.created_at), hits=hits, receipt=r)


def search(client: Client, query: str, hl: str, gl: str) -> SearchPage:
    return parse_search(client.search(search_params(query, hl, gl)).data, query, hl)


class Link(BaseModel):
    text: str
    url: str


class Chapter(BaseModel):
    title: str
    start_s: int


class VideoPage(BaseModel):
    """The full video page: complete description with its links, chapters, and whether a transcript exists."""

    video_id: str
    title: str
    channel: str
    channel_link: str | None
    subscribers: int | None
    views: int | None
    likes: int | None
    published_text: str | None
    published: datetime | None
    description: str
    links: list[Link]
    chapters: list[Chapter]
    has_transcript: bool
    receipt: Receipt


def video_params(video_id: str, gl: str) -> Params:
    return {"engine": "youtube_video", "v": video_id, "gl": gl, "hl": "en"}


def parse_video(data: dict[str, Any], video_id: str) -> VideoPage:
    r = receipt(data)
    raw = data.get("description")
    desc: dict[str, Any] = raw if isinstance(raw, dict) else {"content": raw or ""}
    channel = data.get("channel") or {}
    return VideoPage(
        video_id=video_id,
        title=str(data.get("title") or ""),
        channel=str(channel.get("name") or ""),
        channel_link=channel.get("link"),
        subscribers=channel.get("extracted_subscribers"),
        views=data.get("extracted_views"),
        likes=data.get("extracted_likes"),
        published_text=data.get("published_date"),
        published=parse_upload_date(data.get("published_date"), parse_created_at(r.created_at)),
        description=str(desc.get("content") or ""),
        links=[Link(text=str(x.get("text") or ""), url=str(x["url"])) for x in desc.get("links") or [] if x.get("url")],
        chapters=[
            Chapter(title=str(c.get("title") or ""), start_s=int(c.get("time_start") or 0))
            for c in data.get("chapters") or []
        ],
        has_transcript=bool((data.get("transcript") or {}).get("serpapi_link")),
        receipt=r,
    )


def video(client: Client, video_id: str, gl: str) -> VideoPage:
    return parse_video(client.search(video_params(video_id, gl)).data, video_id)


class Segment(BaseModel):
    start_ms: int
    end_ms: int | None
    time_text: str
    text: str


class Transcript(BaseModel):
    """What the reviewer said, as YouTube's caption track. `script` says which text came back."""

    video_id: str
    language_code: str | None
    script: str  # "latin" | "devanagari" | "telugu" | ... | "mixed" | "empty"
    available: list[str]
    segments: list[Segment]
    # SerpApi's own message when it found no transcript (e.g. "hasn't returned any results").
    error: str | None
    receipt: Receipt


def transcript_params(video_id: str) -> Params:
    # No English track → SerpApi returns the video's first available language (official docs).
    return {"engine": "youtube_video_transcript", "v": video_id, "language_code": "en"}


def script_of(text: str) -> str:
    """The writing system most letters use ("latin", "devanagari", "telugu", ...), "mixed", or "empty"."""
    counts: Counter[str] = Counter(unicodedata.name(c, "?").split(" ")[0].lower() for c in text if c.isalpha())
    if not counts:
        return "empty"
    top, n = counts.most_common(1)[0]
    return top if n / sum(counts.values()) > 0.6 else "mixed"


def parse_transcript(data: dict[str, Any], video_id: str) -> Transcript:
    segs = [
        Segment(
            start_ms=int(s.get("start_ms") or 0),
            end_ms=s.get("end_ms"),
            time_text=str(s.get("start_time_text") or ""),
            text=str(s.get("snippet") or ""),
        )
        for s in data.get("transcript") or []
        if isinstance(s, dict)
    ]
    available = data.get("available_transcripts") or []
    chosen = next((a for a in available if a.get("selected")), None)
    return Transcript(
        video_id=video_id,
        language_code=(chosen or {}).get("language_code"),
        script=script_of(" ".join(s.text for s in segs)),
        available=[f"{a.get('language_code')}:{a.get('type') or 'manual'}" for a in available],
        segments=segs,
        error=data.get("error"),
        receipt=receipt(data),
    )


def transcript(client: Client, video_id: str) -> Transcript:
    return parse_transcript(client.search(transcript_params(video_id)).data, video_id)
