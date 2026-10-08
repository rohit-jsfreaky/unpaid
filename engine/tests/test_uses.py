from __future__ import annotations

from typing import Any

from test_proof import hit, page, transcript

from unpaid.aggregate import tally
from unpaid.category import PHONE, AreaSpec
from unpaid.collect import Video
from unpaid.proof import COMMISSION, Evidence, Proven, ProvenPick
from unpaid.uses import (
    FoundUses,
    UseAnswer,
    VideoUses,
    areas_for,
    names_area,
    names_phone,
    prove_uses,
    tally_uses,
)
from unpaid.youtube import Segment, Transcript


def area(key: str) -> AreaSpec:
    return next(a for a in PHONE.areas if a.key == key)


def test_area_words_match_spelling_variants_and_scripts() -> None:
    assert names_area("एंड परफॉरमेंस भी आपको इसमें अच्छी मिल जाती है।", area("performance"))  # not परफॉर्मेंस
    assert names_area("बैटरी बैकअप तो यार ठीक है।", area("battery"))
    assert names_area("ఈ ఫోన్ కెమెరా చాలా బాగుంది", area("camera"))
    assert names_area("The camera is great", area("camera")) and not names_area("The camera is great", area("battery"))


def test_names_phone_uses_whole_model_words() -> None:
    assert names_phone("डिस्प्ले में Redmi और Poco वालों ने कोई कमी नहीं छोड़ी", "POCO X8")
    assert not names_phone("कैमरा भी अच्छा है।", "Vivo T5")
    assert not names_phone("the P4x is fine", "Realme P4")


def test_must_haves_map_to_areas_and_unknown_ones_are_kept_aside() -> None:
    assert areas_for(["camera", "Battery", "photography", "gaming"]) == (["camera", "battery", "performance"], [])
    assert areas_for(["camera", "warranty"]) == (["camera"], ["warranty"])


def claim(**kw: Any) -> dict[str, Any]:
    base = {"source": "transcript", "segment": None, "meaning_en": "m", "verdict": "good"}
    return {**base, **kw}


def video() -> Video:
    t: Transcript = transcript()
    t = t.model_copy(
        update={
            "segments": [
                *t.segments,
                Segment(start_ms=50_000, end_ms=None, time_text="0:50", text="कैमरा भी अच्छा है।"),
                Segment(start_ms=60_000, end_ms=None, time_text="1:00", text="Vivo T5 की बैटरी बड़ी है।"),
            ]
        }
    )
    return Video(hit=hit(), found_by=["q"], page=page(), transcript=t)


def test_prove_uses_keeps_only_what_code_can_check() -> None:
    answer = UseAnswer.model_validate(
        {
            "claims": [
                claim(phone="Vivo T5", area="battery", quote="Vivo T5 की बैटरी बड़ी है।"),  # kept
                claim(phone="Vivo T5", area="camera", quote="कैमरा भी अच्छा है।"),  # same line for two phones
                claim(phone="iQOO Z1", area="camera", quote="कैमरा भी अच्छा है।"),
                claim(phone="Vivo T5", area="camera", quote="बैटरी बड़ी है।"),  # doesn't name camera
                claim(phone="Nokia 1", area="battery", quote="Vivo T5 की बैटरी बड़ी है।"),  # not their pick
                claim(phone="Vivo T5", area="battery", quote="battery lasts two days"),  # not in the text
            ]
        }
    )
    out = prove_uses(video(), ["Vivo T5", "iQOO Z1"], answer)
    assert [(u.phone, u.area, u.time_text) for u in out.uses] == [("Vivo T5", "battery", "1:00")]
    assert out.uses[0].url.endswith("&t=60s")
    assert [d.reason for d in out.dropped] == [
        "the same sentence was credited to several phones",
        "the same sentence was credited to several phones",
        "the quote doesn't name camera",
        "'Nokia 1' isn't one of their picks",
        "quote not found word for word",
    ]


def proven(vid: str, tie: bool, *phones: str) -> Proven:
    ev = Evidence(
        label=COMMISSION, party=None, source="youtube_label", quote="Earns commission", meaning_en=None,
        segment=None, time_text=None, url="u",
    )  # fmt: skip
    return Proven(
        video_id=vid, channel=f"ch-{vid}", title="t", link="l", views=1, has_transcript=True,
        labels=[ev] if tie else [], denials=[],
        picks=[ProvenPick(phone=p, rank=1, quote="q", meaning_en="m", source="transcript", time_text=None, url="u")
               for p in phones],
        dropped=[], extraction=None,
    )  # fmt: skip


def uses(vid: str, *items: tuple[str, str, str]) -> VideoUses:
    return VideoUses.model_validate(
        {
            "video_id": vid,
            "dropped": [],
            "uses": [
                {"phone": p, "area": a, "verdict": v, "quote": "q", "meaning_en": "m", "source": "transcript",
                 "time_text": None, "url": "u"}
                for p, a, v in items
            ],
        }
    )  # fmt: skip


def test_tally_uses_splits_praise_by_disclosure_and_puts_focus_first() -> None:
    vids = [proven("a", False, "Phone X", "Phone Y"), proven("b", True, "Phone X"), proven("c", False, "Phone Y")]
    found = FoundUses(
        model="m",
        llm_calls=0,
        llm_cost_usd=0,
        videos=[
            uses("a", ("Phone X", "camera", "good"), ("Phone Y", "battery", "good"), ("Phone X", "battery", "weak")),
            uses("b", ("Phone X", "camera", "good"), ("Phone X", "camera", "good")),  # one review counts once
            uses("c", ("phone y 5G", "battery", "good"), ("Phone Y", "display", "good")),
        ],
    )
    areas = tally_uses(vids, found, tally(vids), ["battery", "camera"])
    assert [a.area for a in areas] == ["camera", "battery", "display"]
    cam, bat = areas[0], areas[1]
    x = cam.phones[0]
    assert (x.name, x.good, x.good_no_disclosure, x.good_disclosed) == ("Phone X", 2, 1, 1)
    y = bat.phones[0]
    assert (y.name, y.good_no_disclosure, bat.best_no_disclosure) == ("Phone Y", 2, "Phone Y")
    assert next(p for p in bat.phones if p.name == "Phone X").weak == 1
    assert all(a.focus for a in areas[:2]) and not areas[2].focus
