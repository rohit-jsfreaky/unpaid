"""Live prices for the top products: one Google Shopping search each, then every product is matched against all of them.

A result counts only if its title names every model word of the product, isn't an accessory *for* it ("Earbuds for
Realme P4 Power", "Case compatible with ..."), isn't a part or a used unit, and isn't far below the product's own
typical price. No fixed price floor, so ₹1,000 earbuds work as well as ₹30,000 phones.
"""

from __future__ import annotations

import re
from statistics import median
from typing import Any

from pydantic import BaseModel

from unpaid.aggregate import phone_key
from unpaid.serpapi import Client, Params, receipt

# Never the product itself, whatever is being bought.
NOT_THE_PRODUCT = re.compile(
    r"\b(refurbished|renewed|pre-?owned|unboxed|used|motherboard|housing|spare|replacement|folder|flex|"
    r"lcd screen|touchscreen|display for|display with|cover|tempered glass|screen guard|protector|lamination|skin)\b",
    re.IGNORECASE,
)
# "X for <model>" / "X compatible with <model>": an accessory for the product, not the product.
FOR_IT = re.compile(r"\b(for|compatible|suitable|fits)\b")
# A different model of the same line: "P4" is not "P4 Pro", "Edge 70" is not "Edge 70 Fusion".
VARIANT_WORDS = r"(?:pro|plus|max|ultra|fusion|power|lite|neo|turbo|mini|prime|edge|slim|x|s|r|t|e|5g\s*pro)"
# An offer below this share of the product's typical price is a part, an accessory or a used unit.
FLOOR_SHARE = 0.4


class Offer(BaseModel):
    seller: str
    title: str
    price: int
    price_text: str
    link: str | None
    search_id: str  # the Google Shopping search this offer came from
    searched_at: str


class PhonePrices(BaseModel):
    phone: str
    offers: list[Offer]  # one per seller, cheapest first
    skipped: int  # results that weren't this phone

    @property
    def lowest(self) -> Offer | None:
        return self.offers[0] if self.offers else None


def shopping_params(phone: str) -> Params:
    return {
        "engine": "google_shopping",
        "q": phone,
        "gl": "in",
        "hl": "en",
        "google_domain": "google.co.in",
        # No min_price: Google's own price filter returned 0-6 results for these new phones (8 Oct). Code filters.
    }


def model_words(phone: str) -> list[str]:
    """The model words after the brand: "Realme P4 Pro 5G" → ["p4", "pro"]."""
    words = [w for w in re.findall(r"[a-z0-9+]+", phone.lower()) if w not in ("5g", "galaxy")]
    return words[1:] or words


def is_this_phone(title: str, phone: str) -> bool:
    """Whole words, in order, no variant word right after ("P4 Pro" isn't "P4 Pro Max" or "P4x"), not a part or an
    accessory for it."""
    if NOT_THE_PRODUCT.search(title):
        return False
    text = " ".join(re.findall(r"[a-z0-9+]+", title.lower().replace("moto ", "motorola ")))
    brand = phone_key(phone).split(" ")[0]
    model = r"\s?".join(re.escape(w) for w in model_words(phone))
    m = re.search(rf"\b{model}\b(?!\s?{VARIANT_WORDS}\b)", text)
    if m is None or brand not in text.split():
        return False
    return FOR_IT.search(text[: m.start()]) is None


def parse_shopping(responses: list[dict[str, Any]], phone: str) -> PhonePrices:
    """Every offer for `phone` across all the shopping searches we ran, cheapest per seller."""
    found: list[Offer] = []
    skipped = 0
    for data in responses:
        r_ = receipt(data)
        for r in data.get("shopping_results") or []:
            title, price = str(r.get("title") or ""), r.get("extracted_price")
            if not isinstance(price, int | float) or price <= 0 or not is_this_phone(title, phone):
                skipped += 1
                continue
            found.append(
                Offer(
                    seller=str(r.get("source") or "unknown"),
                    title=title,
                    price=int(price),
                    price_text=str(r.get("price") or ""),
                    link=r.get("product_link") or r.get("link"),
                    search_id=r_.search_id,
                    searched_at=r_.created_at,
                )
            )
    floor = FLOOR_SHARE * median(o.price for o in found) if found else 0
    best: dict[str, Offer] = {}
    for offer in found:
        if offer.price < floor:
            skipped += 1
            continue
        k = offer.seller.lower()  # "Amazon.in" and "amazon.in" are one seller
        if k not in best or offer.price < best[k].price:
            best[k] = offer
    return PhonePrices(phone=phone, offers=sorted(best.values(), key=lambda o: o.price), skipped=skipped)


def prices(client: Client, phones: list[str]) -> list[PhonePrices]:
    params = [shopping_params(p) for p in phones]
    client.check_budget(len(client.missing(params)))
    responses = [client.search(p).data for p in params]
    return [parse_shopping(responses, phone) for phone in phones]
