"""Live prices for the top phones: one Google Shopping search each, then every phone is matched against all of them.

A result counts only if its title names every model word of the phone and isn't an accessory or a refurbished unit.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from unpaid.aggregate import phone_key
from unpaid.serpapi import Client, Params, receipt

NOT_THE_PHONE = re.compile(
    r"\b(case|cover|glass|guard|protector|lamination|skin|charger|cable|adapter|earbuds?|lens|holder|stand|"
    r"motherboard|housing|spare|replacement|combo|folder|flex|button|touchscreen|display for|display with|"
    r"lcd screen|refurbished|renewed|pre-?owned|unboxed|used)\b",
    re.IGNORECASE,
)
# A different model of the same line: "P4" is not "P4 Pro", "Edge 70" is not "Edge 70 Fusion".
VARIANT_WORDS = r"(?:pro|plus|max|ultra|fusion|power|lite|neo|turbo|mini|prime|edge|slim|x|s|r|t|e|5g\s*pro)"
MIN_PRICE = 10_000  # below this a "phone" result in this budget is an accessory


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
    """Whole words, in order, and no variant word right after ("P4 Pro" doesn't match "P4 Pro Max" or "P4x")."""
    if NOT_THE_PHONE.search(title):
        return False
    text = " ".join(re.findall(r"[a-z0-9+]+", title.lower().replace("moto ", "motorola ")))
    brand = phone_key(phone).split(" ")[0]
    model = r"\s?".join(re.escape(w) for w in model_words(phone))
    return brand in text.split() and re.search(rf"\b{model}\b(?!\s?{VARIANT_WORDS}\b)", text) is not None


def parse_shopping(responses: list[dict[str, Any]], phone: str) -> PhonePrices:
    """Every offer for `phone` across all the shopping searches we ran, cheapest per seller."""
    best: dict[str, Offer] = {}
    skipped = 0
    for data in responses:
        r_ = receipt(data)
        for r in data.get("shopping_results") or []:
            title, price = str(r.get("title") or ""), r.get("extracted_price")
            if not isinstance(price, int | float) or price < MIN_PRICE or not is_this_phone(title, phone):
                skipped += 1
                continue
            seller = str(r.get("source") or "unknown")
            offer = Offer(
                seller=seller,
                title=title,
                price=int(price),
                price_text=str(r.get("price") or ""),
                link=r.get("product_link") or r.get("link"),
                search_id=r_.search_id,
                searched_at=r_.created_at,
            )
            k = seller.lower()  # "Amazon.in" and "amazon.in" are one seller
            if k not in best or offer.price < best[k].price:
                best[k] = offer
    return PhonePrices(phone=phone, offers=sorted(best.values(), key=lambda o: o.price), skipped=skipped)


def prices(client: Client, phones: list[str]) -> list[PhonePrices]:
    params = [shopping_params(p) for p in phones]
    client.check_budget(len(client.missing(params)))
    responses = [client.search(p).data for p in params]
    return [parse_shopping(responses, phone) for phone in phones]
