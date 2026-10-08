"""Code proves: a label shows only with a quote found word for word in the stored text, or YouTube's own label.

The LLM's claims come in; what survives goes out with its receipt (where it was found, and a timestamped link).
Everything that didn't survive is kept too, with the reason, so the drop can be audited.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel

from unpaid.extract import Extraction
from unpaid.links import LinkBook
from unpaid.youtube import COMMISSION_LABELS, Hit, Transcript, VideoPage

BRAND_SPONSORED = "Brand-sponsored"
FREE_UNIT = "Free unit from the brand"
COMMISSION = "Earns commission"
THIRD_PARTY = "Third-party sponsor"
NO_DISCLOSURE = "No disclosure found"
LABELS = (BRAND_SPONSORED, FREE_UNIT, COMMISSION, THIRD_PARTY)

# Companies that sell phones in India. A sponsor whose name holds one of these, or the brand of a product the reviewer
# recommends in that video, makes it "Brand-sponsored"; any other sponsor (an app, a retailer, a VPN) is "Third-party".
PHONE_BRANDS = {
    "samsung", "galaxy", "motorola", "moto", "vivo", "iqoo", "oppo", "realme", "oneplus", "xiaomi", "redmi", "mi",
    "poco", "nothing", "cmf", "google", "pixel", "apple", "iphone", "infinix", "tecno", "lava", "honor", "asus",
    "nokia", "itel", "acer", "ai+", "nxtquantum",
}  # fmt: skip

# Lines that use money words but disclose nothing. A claim whose quote matches is dropped, whatever the LLM said.
NOT_A_DISCLOSURE = re.compile(
    r"not\s+sponsor|#notsponsored|no\s+brand|inquir|enquir|contact|business|e-?mail|@|"
    r"provided\s+by\s+this\s+channel|educational|copyright|fair\s+use",
    re.IGNORECASE,
)
ZERO_WIDTH = re.compile(r"[​‌‍⁠﻿]")


def norm(text: str) -> str:
    """Same text, compared fairly: Unicode NFC, invisible zero-width marks removed, runs of whitespace as one space."""
    return " ".join(ZERO_WIDTH.sub("", unicodedata.normalize("NFC", text)).split())


def brand_word(party: str | None, brands: set[str] = PHONE_BRANDS) -> str | None:
    """The sponsor's name holds a product brand: a brand the reviewer recommends here, or a known phone brand."""
    if not party:
        return None
    words = re.findall(r"[a-z0-9+]+", party.lower())
    return next((w for w in words if w in brands), None)


def pick_brands(ex: Extraction | None) -> set[str]:
    """Brands of the products this reviewer recommends: the first word of each pick ("boAt Airdopes 141" → boat)."""
    out: set[str] = set()
    for p in ex.picks if ex else []:
        words = re.findall(r"[a-z0-9+]+", p.phone.lower())
        if words:
            out.add(words[0])
    return out


class Place(BaseModel):
    source: Literal["description", "transcript"]
    segment: int | None = None
    time_text: str | None = None
    start_s: int | None = None
    context: str  # the description line or transcript segments the quote sits in


def locate(quote: str, page: VideoPage, transcript: Transcript | None, hint: int | None) -> Place | None:
    """Where `quote` appears word for word: one description line, or 1-3 consecutive transcript segments."""
    q = norm(quote)
    if len(q) < 4:
        return None
    for line in page.description.splitlines():
        if q in norm(line):
            return Place(source="description", context=line.strip())
    if q in norm(page.description):  # spans two lines
        return Place(source="description", context=q)
    segs = transcript.segments if transcript else []
    order = sorted(range(len(segs)), key=lambda i: abs(i - hint) if hint is not None else i)
    for width in (1, 2, 3):
        for i in order:
            window = " ".join(s.text for s in segs[i : i + width])
            if q in norm(window):
                s = segs[i]
                return Place(
                    source="transcript",
                    segment=i,
                    time_text=s.time_text,
                    start_s=s.start_ms // 1000,
                    context=" ".join(x.text for x in segs[max(0, i - 1) : i + width + 1]),
                )
    return None


class Evidence(BaseModel):
    label: str
    party: str | None
    source: Literal["description", "transcript", "description_link", "youtube_label"]
    quote: str
    meaning_en: str | None  # AI translation, shown as such
    segment: int | None
    time_text: str | None
    url: str  # the video, at the timestamp when the quote was spoken


class Dropped(BaseModel):
    kind: str
    quote: str
    reason: str


class ProvenPick(BaseModel):
    phone: str
    rank: int | None
    quote: str
    meaning_en: str
    source: str
    time_text: str | None
    url: str


class Proven(BaseModel):
    video_id: str
    channel: str
    title: str
    link: str
    views: int | None
    has_transcript: bool
    labels: list[Evidence]
    denials: list[Evidence]
    picks: list[ProvenPick]
    dropped: list[Dropped]
    extraction: str | None  # hash of the saved LLM answer

    @property
    def label_names(self) -> list[str]:
        names = {e.label for e in self.labels}
        return [x for x in LABELS if x in names] or [NO_DISCLOSURE]


def _url(video_id: str, place: Place | None) -> str:
    base = f"https://www.youtube.com/watch?v={video_id}"
    return f"{base}&t={place.start_s}s" if place and place.start_s is not None else base


def link_evidence(page: VideoPage, book: LinkBook) -> list[Evidence]:
    """Description links that lead to a store URL carrying the creator's affiliate id. Code only, no LLM."""
    paid = [(x, c) for x in page.links if (c := book.get(x.url)) and c.is_affiliate]
    if not paid:
        return []
    first, check = paid[0]
    line = next((ln.strip() for ln in page.description.splitlines() if first.url in ln or first.text.strip() in ln), "")
    stores = sorted({c.store or "" for _, c in paid})
    n = len(paid)
    return [
        Evidence(
            label=COMMISSION,
            party=f"{n} link{'s' if n > 1 else ''} to {' / '.join(stores)} with the creator's affiliate id",
            source="description_link",
            quote=line or first.url,
            meaning_en=f"{first.url} leads to {check.store} with {check.affiliate_param}",
            segment=None,
            time_text=None,
            url=_url(page.video_id, None),
        )
    ]


def prove(
    hit: Hit,
    page: VideoPage,
    transcript: Transcript | None,
    ex: Extraction | None,
    ex_hash: str | None,
    book: LinkBook,
) -> Proven:
    labels: list[Evidence] = []
    denials: list[Evidence] = []
    dropped: list[Dropped] = []

    if hit.earns_commission:
        tag = next(x for x in hit.extensions if x.strip() in COMMISSION_LABELS)
        labels.append(
            Evidence(
                label=COMMISSION,
                party="YouTube's own label",
                source="youtube_label",
                quote=tag,
                meaning_en="Earns commission" if tag != "Earns commission" else None,
                segment=None,
                time_text=None,
                url=_url(page.video_id, None),
            )
        )
    labels += link_evidence(page, book)

    for c in ex.claims if ex else []:
        place = locate(c.quote, page, transcript, c.segment)
        if place is None:
            dropped.append(Dropped(kind=c.kind, quote=c.quote, reason="quote not found word for word"))
            continue
        if c.kind == "denial":
            denials.append(
                Evidence(
                    label="Says: not sponsored",
                    party=None,
                    source=place.source,
                    quote=c.quote,
                    meaning_en=c.meaning_en,
                    segment=place.segment,
                    time_text=place.time_text,
                    url=_url(page.video_id, place),
                )
            )
            continue
        if NOT_A_DISCLOSURE.search(norm(c.quote)):
            dropped.append(Dropped(kind=c.kind, quote=c.quote, reason="an inquiry line, disclaimer or denial"))
            continue
        if c.kind == "affiliate_statement":
            label, party = COMMISSION, None
        elif c.kind == "free_unit":
            label, party = FREE_UNIT, c.party
        else:
            if not c.party:
                dropped.append(Dropped(kind=c.kind, quote=c.quote, reason="sponsor not named"))
                continue
            # The sponsor's name must be in the quote or right next to it, not inferred from elsewhere.
            first = re.findall(r"[a-z0-9+]+", c.party.lower())
            if not first or first[0] not in norm(place.context).lower():
                dropped.append(Dropped(kind=c.kind, quote=c.quote, reason=f"{c.party!r} isn't named where quoted"))
                continue
            brands = PHONE_BRANDS | pick_brands(ex)
            label, party = (BRAND_SPONSORED if brand_word(c.party, brands) else THIRD_PARTY), c.party
        labels.append(
            Evidence(
                label=label,
                party=party,
                source=place.source,
                quote=c.quote,
                meaning_en=c.meaning_en,
                segment=place.segment,
                time_text=place.time_text,
                url=_url(page.video_id, place),
            )
        )

    picks: list[ProvenPick] = []
    for p in ex.picks if ex else []:
        place = locate(p.quote, page, transcript, p.segment)
        if place is None:
            dropped.append(Dropped(kind="pick", quote=p.quote, reason=f"{p.phone}: quote not found word for word"))
            continue
        picks.append(
            ProvenPick(
                phone=p.phone,
                rank=p.rank,
                quote=p.quote,
                meaning_en=p.meaning_en,
                source=place.source,
                time_text=place.time_text,
                url=_url(page.video_id, place),
            )
        )

    return Proven(
        video_id=page.video_id,
        channel=page.channel or hit.channel,
        title=page.title or hit.title,
        link=hit.link,
        views=hit.views,
        has_transcript=bool(transcript and transcript.segments),
        labels=labels,
        denials=denials,
        picks=picks,
        dropped=dropped,
        extraction=ex_hash,
    )
