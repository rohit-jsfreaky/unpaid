from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from unpaid import youtube as yt
from unpaid.extract import Claim, Extraction, Pick
from unpaid.links import LinkBook, LinkCheck, follow, store_param
from unpaid.llm import LLM, LLMNotRecorded, SpendLimitReached, strict_schema
from unpaid.proof import (
    BRAND_SPONSORED,
    COMMISSION,
    FREE_UNIT,
    NO_DISCLOSURE,
    THIRD_PARTY,
    locate,
    norm,
    prove,
)
from unpaid.serpapi import Receipt

R = Receipt(search_id="x", json_endpoint="https://serpapi.com/searches/a/x.json", created_at="2026-10-08 00:00:00 UTC")
DESC = (
    "Best phones under 30k.\n"
    "#Collab #BestUnder30000  #MotorolaIndia #BigBillionMotoDeals\n"
    "Buy here - https://amzn.to/abc\n"
    "Untagged - https://bit.ly/xyz\n"
    "For Sponsorship or business inquiries: me@example.com\n"
    "ALL CONTENT PROVIDED BY THIS CHANNEL IS MEANT FOR EDUCATIONAL PURPOSES​"
)


def page(desc: str = DESC, links: tuple[str, ...] = ("https://amzn.to/abc", "https://bit.ly/xyz")) -> yt.VideoPage:
    return yt.VideoPage(
        video_id="vid00000001",
        title="Best phone under 30000",
        channel="Test Tech",
        channel_link=None,
        subscribers=None,
        views=None,
        likes=None,
        published_text=None,
        published=None,
        description=desc,
        links=[yt.Link(text=u, url=u) for u in links],
        chapters=[],
        has_transcript=True,
        receipt=R,
    )


def transcript() -> yt.Transcript:
    texts = ["नमस्ते दोस्तों", "ये फ़ोन मुझे Vivo ने भेजा है", "इस वीडियो को", "Samsung ने sponsor किया है", "Incogni use code"]
    return yt.Transcript(
        video_id="vid00000001",
        language_code=None,
        script="devanagari",
        available=[],
        segments=[
            yt.Segment(start_ms=i * 10_000, end_ms=None, time_text=f"0:{i * 10:02d}", text=t)
            for i, t in enumerate(texts)
        ],
        error=None,
        receipt=R,
    )


def hit(commission: bool = False) -> yt.Hit:
    return yt.Hit(
        video_id="vid00000001",
        title="t",
        link="https://www.youtube.com/watch?v=vid00000001",
        channel="Test Tech",
        channel_link=None,
        views=10,
        length=None,
        published_text="1 day ago",
        age_days=1,
        snippet=None,
        extensions=["कमीशन मिलेगा"] if commission else [],
        earns_commission=commission,
        products=None,
        query="q",
        hl="hi",
        position=1,
        receipt=R,
    )


def book(tmp_path: Path) -> LinkBook:
    b = LinkBook(tmp_path / "links.json", live=False)
    now = datetime(2026, 10, 8, tzinfo=UTC)
    b.checks = {
        "https://amzn.to/abc": LinkCheck(
            url="https://amzn.to/abc",
            hops=["https://www.amazon.in/dp/B0X?tag=creator-21"],
            store="amazon.in",
            affiliate_param="tag=creator-21",
            error=None,
            checked_at=now,
        ),
        "https://bit.ly/xyz": LinkCheck(
            url="https://bit.ly/xyz", hops=[], store=None, affiliate_param=None, error=None, checked_at=now
        ),
    }
    return b


def claim(
    kind: str, quote: str, party: str | None = None, source: str = "description", seg: int | None = None
) -> Claim:
    return Claim.model_validate(
        {"kind": kind, "party": party, "source": source, "segment": seg, "quote": quote, "meaning_en": "m"}
    )


def test_norm_ignores_only_whitespace_and_invisible_marks() -> None:
    assert norm("a​  b\n c") == "a b c" and norm("Moto") != norm("moto")


def test_locate_description_line_and_transcript_span() -> None:
    p, t = page(), transcript()
    d = locate("#Collab #BestUnder30000 #MotorolaIndia", p, t, None)
    assert d and d.source == "description" and "BigBillionMotoDeals" in d.context
    s = locate("इस वीडियो को Samsung ने sponsor", p, t, 2)  # runs across segments 2 and 3
    assert s and (s.source, s.segment, s.time_text, s.start_s) == ("transcript", 2, "0:20", 20)
    assert locate("ये फ़ोन मुझे Oppo ने भेजा है", p, t, 1) is None  # one word changed: not found


def test_every_label_needs_its_quote(tmp_path: Path) -> None:
    ex = Extraction(
        claims=[
            claim("paid_sponsorship", "#Collab #BestUnder30000 #MotorolaIndia", "Motorola"),
            claim("free_unit", "ये फ़ोन मुझे Vivo ने भेजा है", "Vivo", "transcript", 1),
            claim("paid_sponsorship", "इस वीडियो को Samsung ने sponsor किया है", "Samsung", "transcript", 2),
            claim("paid_sponsorship", "Incogni use code", "Incogni", "transcript", 4),
            claim("paid_sponsorship", "Sponsored by Realme for this video", "Realme"),  # invented
        ],
        picks=[],
    )
    v = prove(hit(), page(), transcript(), ex, "h", book(tmp_path))
    got = {(e.label, e.party) for e in v.labels}
    assert (BRAND_SPONSORED, "Motorola") in got and (FREE_UNIT, "Vivo") in got and (BRAND_SPONSORED, "Samsung") in got
    assert (THIRD_PARTY, "Incogni") in got
    assert [d.reason for d in v.dropped] == ["quote not found word for word"]
    vivo = next(e for e in v.labels if e.party == "Vivo")
    assert vivo.url.endswith("&t=10s") and vivo.time_text == "0:10"


def test_traps_never_become_labels(tmp_path: Path) -> None:
    ex = Extraction(
        claims=[
            claim("paid_sponsorship", "For Sponsorship or business inquiries", "Test Tech"),
            claim("free_unit", "ALL CONTENT PROVIDED BY THIS CHANNEL", "Test Tech"),
            claim("paid_sponsorship", "#Collab #BestUnder30000", "Samsung"),  # Samsung isn't named there
            claim("paid_sponsorship", "Best phones under 30k.", None),
        ],
        picks=[],
    )
    v = prove(hit(), page(links=("https://bit.ly/xyz",)), transcript(), ex, "h", book(tmp_path))
    assert v.labels == [] and v.label_names == [NO_DISCLOSURE]
    reasons = [d.reason for d in v.dropped]
    assert reasons == [
        "an inquiry line, disclaimer or denial",
        "an inquiry line, disclaimer or denial",
        "'Samsung' isn't named where quoted",
        "sponsor not named",
    ]


def test_denial_is_shown_but_is_not_a_label(tmp_path: Path) -> None:
    p = page("This video is not sponsored by any brand.", links=())
    ex = Extraction(claims=[claim("denial", "not sponsored by any brand")], picks=[])
    v = prove(hit(), p, None, ex, "h", book(tmp_path))
    assert v.label_names == [NO_DISCLOSURE] and len(v.denials) == 1


def test_commission_only_from_a_tagged_link_or_youtubes_label(tmp_path: Path) -> None:
    tagged = prove(hit(), page(), None, None, None, book(tmp_path))
    assert tagged.label_names == [COMMISSION] and tagged.labels[0].quote == "Buy here - https://amzn.to/abc"
    assert tagged.labels[0].party == "1 link to amazon.in with the creator's affiliate id"
    untagged = prove(hit(), page(links=("https://bit.ly/xyz",)), None, None, None, book(tmp_path))
    assert untagged.label_names == [NO_DISCLOSURE]
    yt_label = prove(hit(commission=True), page(links=()), None, None, None, book(tmp_path))
    assert yt_label.labels[0].source == "youtube_label" and yt_label.labels[0].quote == "कमीशन मिलेगा"


def test_picks_need_their_quote_too(tmp_path: Path) -> None:
    pick = {"phone": "Vivo T4", "rank": 1, "source": "transcript", "segment": 1, "meaning_en": "m"}
    ex = Extraction(
        claims=[],
        picks=[
            Pick.model_validate({**pick, "quote": "ये फ़ोन"}),
            Pick.model_validate({**pick, "quote": "best phone ever"}),
        ],
    )
    v = prove(hit(), page(links=()), transcript(), ex, "h", book(tmp_path))
    assert [p.phone for p in v.picks] == ["Vivo T4"] and v.dropped[0].kind == "pick"


def test_store_param_and_redirect_following() -> None:
    assert store_param("https://www.amazon.in/ref=as_li_ss_tl?tag=abc-21&linkCode=sl2") == ("amazon.in", "tag=abc-21")
    assert store_param("https://www.flipkart.com/p?affid=xyz") == ("flipkart.com", "affid=xyz")
    assert store_param("https://www.amazon.in/dp/B0X") == ("amazon.in", None)

    asked: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        asked.append(str(request.url))
        if request.method != "GET":  # like link.amazon: HEAD gets a 404
            return httpx.Response(404)
        nxt = {
            "https://link.amazon/A": "https://amzlinks.in/A",
            "https://amzlinks.in/A": "https://www.amazon.in/dp/B0X?tag=creator-21",
        }
        return httpx.Response(302, headers={"location": nxt[str(request.url)]})

    c = follow("https://link.amazon/A", httpx.MockTransport(handler))
    assert c.is_affiliate and c.affiliate_param == "tag=creator-21" and len(c.hops) == 2
    assert not any("amazon.in" in u for u in asked)  # the store itself is never requested


def test_linkbook_replay_refuses_unchecked(tmp_path: Path) -> None:
    with pytest.raises(LookupError):
        LinkBook(tmp_path / "links.json", live=False).check_all(["https://amzn.to/new"])
    LinkBook(tmp_path / "links.json", live=False).check_all(["https://www.youtube.com/@x"])  # skipped, no error


def fake_llm(calls: list[dict[str, Any]], cost: float = 0.01) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        body = {
            "id": "gen-1",
            "model": "m",
            "provider": "p",
            "choices": [{"message": {"content": json.dumps({"claims": [], "picks": []})}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": cost},
        }
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


def test_llm_records_once_replays_free_and_caps_spend(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    key = "sk-or-" + "k" * 40
    llm = LLM(
        mode="live", model="m", write_dir=tmp_path, read_dirs=(tmp_path,), key=key, spend_limit_usd=0.015,
        transport=fake_llm(calls),
    )  # fmt: skip
    first, h1 = llm.structured("sys", "user 1", Extraction)
    again, h2 = llm.structured("sys", "user 1", Extraction)
    assert first == again and h1 == h2 and len(calls) == 1 and llm.cached == 1
    assert calls[0]["temperature"] == 0 and calls[0]["response_format"]["json_schema"]["strict"] is True
    assert key not in "".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.json"))
    llm.structured("sys", "user 2", Extraction)  # spent 0.02 now >= 0.015
    with pytest.raises(SpendLimitReached):
        llm.structured("sys", "user 3", Extraction)
    replay = LLM(mode="replay", model="m", write_dir=tmp_path, read_dirs=(tmp_path,))
    assert replay.structured("sys", "user 1", Extraction)[1] == h1
    with pytest.raises(LLMNotRecorded):
        replay.structured("sys", "never asked", Extraction)


def test_strict_schema_requires_every_key() -> None:
    s = strict_schema(Extraction)
    claim_schema = s["properties"]["claims"]["items"]
    assert claim_schema["additionalProperties"] is False and set(claim_schema["required"]) == set(Claim.model_fields)
