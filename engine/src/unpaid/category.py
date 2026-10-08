"""What kind of product a question is about, and the features reviewers judge it on.

Phones have a curated profile (feature words in English, Hindi, Telugu and Malayalam, checked on real reviews).
Any other product gets its features from the LLM once per question; they are saved with the report and every quote
is then checked against those words by code, the same way.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from unpaid.llm import LLM

PHONE_WORDS = {"phone", "phones", "smartphone", "smartphones", "mobile", "mobiles", "mobile phone", "5g phone"}


class AreaSpec(BaseModel):
    key: str  # "camera", "noise cancellation"
    name: str  # "Camera"
    words: list[str]  # a quote about this area must contain one of these (stems, any script)
    hint: str = ""  # extra words for the prompt, e.g. "including gaming"


class Category(BaseModel):
    product: str  # the shopper's word: "phone", "earbuds"
    noun: str  # "phone review", "earbuds review"
    plural: str  # "phones", "earbuds"
    item: str  # "phone" / "product": what the creator recommends
    header: str  # the list header in prompts: "PHONES" / "PRODUCTS"
    name_rule: str  # how to name a product
    spec_example: str  # a bare spec with no opinion
    word_examples: str  # example area words
    areas: list[AreaSpec]


PHONE_AREAS = [
    AreaSpec(
        key="camera",
        name="Camera",
        words=[
            "camera", "cam ", "photo", "selfie", "portrait", "zoom", "telephoto", "sensor", "megapixel", "कैमर",
            "फोटो", "फ़ोटो", "सेल्फ", "मेगापिक्सल", "కెమెర", "ఫోటో", "సెల్ఫీ", "ക്യാമറ", "ഫോട്ടോ",
        ],
    ),
    AreaSpec(
        key="battery",
        name="Battery",
        words=["battery", "mah", "backup", "बैटर", "बैट्र", "बैकअप", "బ్యాటర", "బ్యాకప్", "ബാറ്ററ", "ബാക്കപ്പ്"],
    ),
    AreaSpec(
        key="performance",
        name="Performance",
        hint="including gaming",
        words=[
            "performance", "gaming", "game", "processor", "chipset", "snapdragon", "dimensity", "परफ", "गेम",
            "प्रोसेस", "పర్ఫా", "పెర్ఫా", "గేమ", "ప్రాసెస", "പെർഫോ", "ഗെയിം",
        ],
    ),
    AreaSpec(
        key="display",
        name="Display",
        words=[
            "display", "screen", "amoled", "oled", "lcd", "brightness", "nits", "डिस्प्ल", "स्क्रीन", "एमोलेड",
            "एलसीडी", "డిస్ప్ల", "స్క్రీన్", "ഡിസ്പ്ല",
        ],
    ),
    AreaSpec(key="charging", name="Charging", words=["charging", "charger", "चार्ज", "ఛార్జ", "చార్జ", "ചാർജ"]),
    AreaSpec(
        key="design",
        name="Design",
        words=["design", "build", "looks", "slim", "thin", "weight", "डिज़ाइन", "डिजाइन", "लुक", "డిజైన్", "లుక్", "ഡിസൈൻ"],
    ),
    AreaSpec(
        key="software",
        name="Software",
        words=["software", " ui", "update", "android", "bloatware", "सॉफ्टवेयर", "अपडेट", "సాఫ్ట్", "అప్డేట్", "സോഫ്റ്റ്"],
    ),
]  # fmt: skip

PHONE = Category(
    product="phone",
    noun="phone",
    plural="phones",
    item="phone",
    header="PHONES",
    name_rule='the standard English "Brand Model" name, e.g. "Motorola Edge 60 Pro", "iQOO Neo 10", "Samsung Galaxy\n'
    "  M36\". Don't include RAM/storage or colour.",
    spec_example='"it has a 5000mAh battery"',
    word_examples='"camera", "कैमरा", "battery", "बैटरी"',
    areas=PHONE_AREAS,
)


def is_phone(product: str) -> bool:
    return " ".join(re.findall(r"[a-z0-9]+", product.lower())) in PHONE_WORDS


def plural(word: str) -> str:
    return word if word.endswith("s") else f"{word}s"


ASPECTS_SYSTEM = """A shopper in India wants to buy the product below. List the features reviewers judge this kind of
product on, 5 to 7 of them, always including every feature the shopper says they care about.
For each feature give:
- name: one or two plain lowercase English words ("sound", "noise cancellation", "battery").
- words: 10 to 20 words reviewers use when they talk about it, so a sentence about this feature contains at least one:
  1. English words and short stems ("batter" for battery, "workout").
  2. The same English words the way YouTube's auto-captions spell them in Hindi, Telugu and Malayalam scripts.
     Captions write English words by sound, not by meaning: "बेस" for bass, "साउंड" for sound, "माइक" for mic,
     "वर्कआउट" for workout, "रनिंग" for running, "बैटरी" for battery, "బేస్", "ബേസ്".
  3. Hindi words with the same meaning, in Devanagari and in Latin letters ("आवाज़", "awaaz").
Keep each word short and specific to the feature; no common words like "good", "quality", "best"."""


class Aspect(BaseModel):
    name: str
    words: list[str]


class Aspects(BaseModel):
    features: list[Aspect]


def _key(name: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", name.lower()))[:40]


def category_for(product: str, must_haves: list[str], llm: LLM | None) -> Category:
    """The phone profile for phones; for anything else, features from the LLM (saved, then checked by code)."""
    if is_phone(product):
        return PHONE
    if llm is None:
        raise ValueError(f"{product!r} needs its features from the LLM")
    asked = "\n".join(f"- {m}" for m in must_haves) or "- (nothing specific)"
    answer, _ = llm.structured(ASPECTS_SYSTEM, f"PRODUCT: {product}\nTHE SHOPPER CARES ABOUT:\n{asked}", Aspects)
    areas: list[AreaSpec] = []
    for a in answer.features:
        key = _key(a.name)
        words = sorted({w.strip().lower() for w in a.words if len(w.strip()) >= 3} | {key})
        if key and key not in {x.key for x in areas}:
            areas.append(AreaSpec(key=key, name=key.capitalize(), words=words))
    for m in must_haves:  # every must-have becomes a feature, even if the LLM left it out
        k = _key(m)
        if k and not any(k == a.key or k in a.words for a in areas):
            areas.append(AreaSpec(key=k, name=k.capitalize(), words=[k]))
    noun = " ".join(re.findall(r"[a-z0-9]+", product.lower())) or "product"
    return Category(
        product=noun,
        noun=noun,
        plural=plural(noun),
        item="product",
        header="PRODUCTS",
        name_rule='the brand and model as sold, e.g. "boAt Airdopes 141". Don\'t include colour.',
        spec_example="a bare spec with no opinion",
        word_examples=", ".join(f'"{a.words[0]}"' for a in areas[:3]),
        areas=areas,
    )
