from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError
from test_proof import book, hit, page, transcript

from unpaid import extract, uses
from unpaid.category import PHONE, category_for, is_phone
from unpaid.extract import Claim, Extraction, Pick
from unpaid.llm import LLM
from unpaid.prices import is_this_phone, parse_shopping
from unpaid.proof import BRAND_SPONSORED, THIRD_PARTY, prove

HERE = Path(__file__).parent


def test_phone_prompts_are_word_for_word_the_recorded_ones() -> None:
    # The recorded run's saved answers are keyed by these exact prompts; templating must not change a character.
    assert extract.system_prompt(PHONE) == (HERE / "recorded_extract_prompt.txt").read_text(encoding="utf-8")
    assert uses.system_prompt(PHONE) == (HERE / "recorded_uses_prompt.txt").read_text(encoding="utf-8")


def test_is_phone() -> None:
    assert is_phone("phone") and is_phone("Smartphone") and is_phone("mobile phone")
    assert not is_phone("earbuds") and not is_phone("laptop")


def fake_llm(tmp_path: Path, answer: dict[str, Any]) -> LLM:
    def handler(request: httpx.Request) -> httpx.Response:
        body = {
            "id": "g",
            "model": "m",
            "choices": [{"message": {"content": json.dumps(answer)}}],
            "usage": {"cost": 0},
        }
        return httpx.Response(200, json=body)

    key = "sk-or-test-" + "z" * 32
    return LLM(
        mode="live", model="m", write_dir=tmp_path, read_dirs=(tmp_path,), key=key, spend_limit_usd=1,
        transport=httpx.MockTransport(handler),
    )  # fmt: skip


def test_other_products_get_their_features_from_the_llm_and_keep_every_must_have(tmp_path: Path) -> None:
    answer = {
        "features": [
            {"name": "Sound", "words": ["sound", "bass", "साउंड", "audio"]},
            {"name": "Noise cancellation", "words": ["anc", "noise", "नॉइज़"]},
            {"name": "battery", "words": ["battery", "बैटरी", "playtime"]},
        ]
    }
    cat = category_for("Earbuds", ["bass", "sweat proof"], fake_llm(tmp_path, answer))
    assert (cat.product, cat.plural, cat.item, cat.header) == ("earbuds", "earbuds", "product", "PRODUCTS")
    keys = [a.key for a in cat.areas]
    assert keys == ["sound", "noise cancellation", "battery", "sweat proof"]  # "bass" is a word of sound
    assert uses.areas_for(["bass", "sweat proof", "warranty"], cat) == (["sound", "sweat proof"], ["warranty"])
    prompt = uses.system_prompt(cat)
    assert "YouTube earbuds review" in prompt and "sound, noise cancellation, battery, sweat proof." in prompt
    assert "phone" not in extract.system_prompt(cat).replace("`phone`", "")
    assert category_for("phone", ["camera"], None) is PHONE


def test_answer_model_only_accepts_this_categorys_features() -> None:
    model = uses.answer_model(("sound", "battery"))
    good = {"phone": "boAt Airdopes 141", "area": "sound", "verdict": "good", "source": "description",
            "segment": None, "quote": "q", "meaning_en": "m"}  # fmt: skip
    assert model.model_validate({"claims": [good]}).claims[0].area == "sound"
    with pytest.raises(ValidationError):
        model.model_validate({"claims": [{**good, "area": "camera"}]})


@pytest.mark.parametrize(
    ("title", "want"),
    [
        ("boAt Airdopes 141 with 42H Playtime, ENx Tech", True),
        ("Ear Tips for boAt Airdopes 141", False),  # an accessory for it
        ("Silicone Case Compatible with boAt Airdopes 141", False),
        ("boAt Airdopes 141 (Renewed)", False),
        ("boAt Airdopes 141 Pro", False),  # a different model
    ],
)
def test_matching_works_for_any_product(title: str, want: bool) -> None:
    assert is_this_phone(title, "boAt Airdopes 141") is want


def test_cheap_products_keep_their_prices_and_odd_lows_are_dropped() -> None:
    rows = [("boAt Airdopes 141", "A", 1099), ("boAt Airdopes 141", "B", 1199), ("boAt Airdopes 141", "C", 299)]
    data = {
        "search_metadata": {"id": "s", "json_endpoint": "https://serpapi.com/searches/a/s.json", "created_at": "t"},
        "shopping_results": [{"title": t, "source": s, "extracted_price": p} for t, s, p in rows],
    }
    pp = parse_shopping([data], "boAt Airdopes 141")
    assert [(o.seller, o.price) for o in pp.offers] == [("A", 1099), ("B", 1199)] and pp.skipped == 1


def test_sponsor_who_makes_a_recommended_product_is_the_brand(tmp_path: Path) -> None:
    p = page("This video is sponsored by boAt. Use code X.", links=())
    pick = Pick.model_validate(
        {"phone": "boAt Airdopes 141", "rank": 1, "source": "description", "segment": None, "quote": "q",
         "meaning_en": "m"}
    )  # fmt: skip
    claim = Claim.model_validate(
        {"kind": "paid_sponsorship", "party": "boAt", "source": "description", "segment": None,
         "quote": "This video is sponsored by boAt.", "meaning_en": "m"}
    )  # fmt: skip
    v = prove(hit(), p, transcript(), Extraction(claims=[claim], picks=[pick]), "h", book(tmp_path))
    assert v.label_names == [BRAND_SPONSORED]
    other = prove(hit(), p, transcript(), Extraction(claims=[claim], picks=[]), "h", book(tmp_path))
    assert other.label_names == [THIRD_PARTY]
