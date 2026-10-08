from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from unpaid import youtube as yt
from unpaid.collect import Plan, Query, select, showcase_plan
from unpaid.config import PROBE_DIR, load_settings

HINDI = "youtube_search_best-phone-under-30000-hindi_gl-in_hl-hi.json"
ENGLISH = "youtube_search_nothing-phone-3_gl-in.json"


def probe(name: str) -> dict[str, Any]:
    return json.loads((PROBE_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("text", "days"),
    [
        ("12 hours ago", 0.5),
        ("7mo ago", 210),
        ("1y ago", 365),
        ("2 days ago", 2),
        ("Streamed 3 weeks ago", 21),
        ("12 घं॰ पहले", 0.5),
        ("3 सप्ताह पहले", 21),
        ("8 माह पहले", 240),
        ("2 दिन पहले", 2),
        ("Jul 2, 2025", None),
        (None, None),
    ],
)
def test_age_in_days_reads_english_and_hindi(text: str | None, days: float | None) -> None:
    assert yt.age_in_days(text) == days


def test_upload_date_absolute_or_counted_back() -> None:
    at = datetime(2026, 10, 7, 12, tzinfo=UTC)
    assert yt.parse_upload_date("Premiered Jul 2, 2025", at) == datetime(2025, 7, 2, tzinfo=UTC)
    assert yt.parse_upload_date("12 hours ago", at) == datetime(2026, 10, 7, tzinfo=UTC)
    assert yt.parse_upload_date("sometime", at) is None


def test_search_reads_youtube_labels_in_both_languages() -> None:
    hi = yt.parse_search(probe(HINDI), "q", "hi")
    en = yt.parse_search(probe(ENGLISH), "q", "en")
    assert len(hi.hits) == 20 and hi.receipt.search_id == "6ac6b3fdf9aa731e2c815b5a"
    fastoye = next(h for h in hi.hits if h.channel == "Fastoye")
    assert (fastoye.video_id, fastoye.products, fastoye.earns_commission, fastoye.age_days) == (
        "tJHSco5gJhA",
        17,
        False,
        0.5,
    )
    assert sum(h.earns_commission for h in hi.hits) == 3  # "कमीशन मिलेगा"
    assert {h.channel for h in en.hits if h.earns_commission} == {
        "6 Months Later",
        "GSMArena Official",
        "Flossy Carter",
        "Nathan B Tech",
    }


def test_video_page_keeps_full_description_and_its_links() -> None:
    v = yt.parse_video(probe("youtube_video_k5itPbQtz_Y.json"), "k5itPbQtz_Y")
    assert "Incogni" in v.description and v.has_transcript and v.subscribers == 23_000_000
    assert "https://amzn.to/3mFix9d" in {x.url for x in v.links}
    assert v.published == datetime(2025, 7, 2, tzinfo=UTC) and v.chapters[1].start_s == 40


def test_transcript_segments_and_script() -> None:
    t = yt.parse_transcript(probe("youtube_transcript_ZRVRBnrSNnc.json"), "ZRVRBnrSNnc")
    assert len(t.segments) == 38 and t.script == "latin" and t.segments[1].time_text == "0:06"
    assert yt.script_of("ये फ़ोन बहुत अच्छा है") == "devanagari" and yt.script_of("...") == "empty"
    assert yt.script_of("ఈ ఫోన్ చాలా బాగుంది") == "telugu" and yt.script_of("ab ఫన") == "mixed"


def test_select_keeps_recent_budget_videos_and_says_why_others_drop() -> None:
    page = yt.parse_search(probe(HINDI), "q", "hi")
    keep, dropped = select([page], showcase_plan(load_settings()))
    assert len(keep) == 14 and len(dropped) == 6
    assert all((v.hit.age_days or 99) <= 21 for v in keep)
    assert [v.hit.views or 0 for v in keep] == sorted((v.hit.views or 0 for v in keep), reverse=True)
    assert {d.reason for d in dropped} >= {"title doesn't name the budget", "older than 21 days (8 माह पहले)"}


def test_select_dedupes_across_queries_and_caps() -> None:
    page = yt.parse_search(probe(HINDI), "q", "hi")
    again = page.model_copy(update={"query": "q2"})
    plan = Plan(question="x", queries=[Query(text="q", hl="hi")], title_pattern=".", window_days=30, max_videos=5)
    keep, dropped = select([page, again], plan)
    assert len(keep) == 5 and all(v.found_by == ["hi: q", "hi: q2"] for v in keep)
    recent = {h.video_id for h in page.hits if h.age_days is not None and h.age_days <= 30}
    assert sum("limit" in d.reason for d in dropped) == len(recent) - 5


def test_empty_transcript_keeps_serpapis_reason() -> None:
    data = {
        "search_metadata": {"id": "x", "json_endpoint": "https://serpapi.com/searches/a/x.json", "created_at": "t"},
        "search_information": {"results_state": "Fully empty"},
        "error": "YouTube Video Transcript hasn't returned any results for this query.",
    }
    t = yt.parse_transcript(data, "abc")
    assert t.segments == [] and t.script == "empty" and t.error and "hasn't returned" in t.error
