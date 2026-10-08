from __future__ import annotations

from typing import Any

import pytest

from unpaid.aggregate import phone_key, tally
from unpaid.prices import is_this_phone, parse_shopping
from unpaid.proof import COMMISSION, Evidence, Proven, ProvenPick


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Realme P4 Pro 5G", "realme P4 Pro"),
        ("Samsung Galaxy M56 5G", "Samsung M56"),
        ("Nothing Phone (4a)", "Nothing Phone 4a"),
        ("POCO X8", "Poco X8"),
        ("Moto Edge 60 Pro", "Motorola Edge 60 Pro"),
        ("Motorola Moto G96", "Motorola G96"),
        ("Xiaomi Redmi Note 15 Pro", "Redmi Note 15 Pro"),
    ],
)
def test_phone_key_merges_spellings(a: str, b: str) -> None:
    assert phone_key(a) == phone_key(b)


def test_phone_key_keeps_different_models_apart() -> None:
    assert phone_key("Motorola Edge 70") != phone_key("Motorola Edge 70 Fusion")
    assert phone_key("Realme P4") != phone_key("Realme P4 Pro") != phone_key("Realme P4x")


@pytest.mark.parametrize(
    ("title", "phone", "want"),
    [
        ("Motorola Edge 70 Fusion 5G (8GB/256GB)", "Motorola Edge 70 Fusion", True),
        ("Motorola Motorola Edge 70 Fusion 5G 8GB RAM", "Motorola Edge 70 Fusion", True),
        ("moto edge 70 fusion", "Motorola Edge 70 Fusion", True),
        ("Motorola Edge 70 Fusion Back Cover", "Motorola Edge 70 Fusion", False),
        ("Motorola Edge 70 Fusion 5G", "Motorola Edge 70", False),
        ("Realme P4 PRO 8+128", "Realme P4 Pro", True),
        ("realme P4x 5G Smartphone", "Realme P4 Pro", False),
        ("Realme P4 Pro 5G 256GB 12GB RAM Motherboard - ORIGINAL", "Realme P4 Pro", False),
        ("Display for Realme P4 Pro 5G - White (Combo Folder)", "Realme P4 Pro", False),
        ("realme P4 Power 5G", "Realme P4 Power", True),
        ("realme P4 Power 5G", "Realme P4 Pro", False),
        ("Realme Narzo Power 5G", "Realme P4 Power", False),
        ("realme P4s 5G", "Realme P4", False),
    ],
)
def test_shopping_title_matches_only_that_phone(title: str, phone: str, want: bool) -> None:
    assert is_this_phone(title, phone) is want


def shop(*rows: tuple[str, str, float], sid: str = "s1") -> dict[str, Any]:
    return {
        "search_metadata": {"id": sid, "json_endpoint": "https://serpapi.com/searches/a/s.json", "created_at": "t"},
        "shopping_results": [{"title": t, "source": s, "extracted_price": p, "price": f"₹{p}"} for t, s, p in rows],
    }


def test_offers_pooled_across_searches_cheapest_per_seller() -> None:
    a = shop(("Realme P4 Pro 5G Cover", "Pikkme", 199), ("Realme P4 PRO 8+128", "Shop A", 28999), sid="a")
    b = shop(
        ("realme P4 Pro 5G", "shop a", 27999),  # same seller, other case, cheaper
        ("realme P4 Pro", "Shop B", 8000),  # under the floor: not a real new phone at this price
        ("realme P4 Power 5G", "Shop C", 32999),
        sid="b",
    )
    pp = parse_shopping([a, b], "Realme P4 Pro")
    assert [(o.seller, o.price, o.search_id) for o in pp.offers] == [("shop a", 27999, "b")]
    assert pp.skipped == 3  # cover, under the floor, a different phone
    power = parse_shopping([a, b], "Realme P4 Power")  # found in the other phone's search
    assert power.lowest and (power.lowest.price, power.lowest.search_id) == (32999, "b")


def video(vid: str, labelled: bool, *phones: str) -> Proven:
    ev = Evidence(
        label=COMMISSION, party=None, source="youtube_label", quote="Earns commission", meaning_en=None,
        segment=None, time_text=None, url="u",
    )  # fmt: skip
    return Proven(
        video_id=vid,
        channel=f"ch-{vid}",
        title="t",
        link="l",
        views=1,
        has_transcript=True,
        labels=[ev] if labelled else [],
        denials=[],
        picks=[
            ProvenPick(phone=p, rank=i + 1, quote="q", meaning_en="m", source="transcript", time_text="0:01", url="u")
            for i, p in enumerate(phones)
        ],
        dropped=[],
        extraction=None,
    )


def test_tally_splits_no_disclosure_from_disclosed_reviewers() -> None:
    vids = [
        video("a", True, "Phone X", "Phone Y"),
        video("b", True, "Phone X", "phone x 5G"),  # one video counts once
        video("c", False, "Phone Y"),
        video("d", False, "Phone Y", "Phone Z"),
        video("e", False),  # no picks: not counted
    ]
    b = tally(vids, top=2)
    assert (b.videos_with_picks, b.no_disclosure_videos_with_picks, b.disclosed_videos_with_picks) == (4, 2, 2)
    x = next(p for p in b.phones if p.key == phone_key("Phone X"))
    y = next(p for p in b.phones if p.key == phone_key("Phone Y"))
    assert (x.all, x.no_disclosure, x.disclosed, x.share_disclosed) == (2, 0, 2, 1.0)
    assert (y.all, y.no_disclosure, y.share_no_disclosure) == (3, 2, 1.0)
    assert b.top_all == ["Phone Y", "Phone X"] and b.top_no_disclosure == ["Phone Y", "Phone Z"]
