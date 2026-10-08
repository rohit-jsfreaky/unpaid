"""What each recommended product is good at, in the reviewer's own words: camera, battery, sound and so on.

AI finds, code proves (same rule as the labels): a claim is kept only if its quote is found word for word, the
product is one this reviewer actually picked, and the quote itself names the feature ("battery", "बैटरी", "బ్యాటరీ").
The features come from the product's category (category.py). A separate pass from the labels, so the labels and
their accuracy numbers stay as recorded.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from typing import Any, Literal, cast

from pydantic import BaseModel, create_model

from unpaid.aggregate import Board, phone_key
from unpaid.category import PHONE, AreaSpec, Category
from unpaid.collect import Collection, Video
from unpaid.extract import user_prompt
from unpaid.llm import LLM
from unpaid.proof import NO_DISCLOSURE, Dropped, Proven, locate, norm

SYSTEM_TEMPLATE = """You read one YouTube {noun} review: its description and what was said in the video (English, Hindi,
Hinglish, Telugu, Malayalam or a mix). The reviewer recommends the {plural} listed under {header}.

For each of those {plural}, find every place where the reviewer gives an opinion on one of these areas:
{areas}.
- verdict "good": they praise it for that area or recommend it for people who care about that area.
- verdict "weak": they say it falls short in that area.
- Skip bare specs with no opinion ({spec_example}).
- `phone` must be copied exactly from the {header} list.

Quoting rules (strict; your quotes are checked by a program and dropped if they don't match):
- Copy each quote EXACTLY from the text: same script, spelling, punctuation and capitals. Never translate.
- The quote itself must contain the word for the area (e.g. {word_examples}).
- Use the shortest exact span that shows the opinion, at most 200 characters.
- A transcript quote comes from one segment [i] (it may run on into [i+1]); give that i as `segment`.
  A description quote has `segment` null.
- `meaning_en`: a plain English meaning of the quote.
If there is nothing, return an empty list. Never invent anything."""


def system_prompt(cat: Category) -> str:
    """The instructions for one kind of product. For phones this is, word for word, the recorded prompt."""
    areas = ", ".join(f"{a.key} ({a.hint})" if a.hint else a.key for a in cat.areas)
    return SYSTEM_TEMPLATE.format(
        noun=cat.noun,
        plural=cat.plural,
        header=cat.header,
        areas=areas,
        spec_example=cat.spec_example,
        word_examples=cat.word_examples,
    )


class UseClaim(BaseModel):
    phone: str
    area: str
    verdict: Literal["good", "weak"]
    source: Literal["description", "transcript"]
    segment: int | None
    quote: str
    meaning_en: str


class UseAnswer(BaseModel):
    claims: list[UseClaim]


@cache
def answer_model(keys: tuple[str, ...]) -> type[UseAnswer]:
    """UseAnswer whose `area` must be one of this category's features (a strict enum for the LLM)."""
    area = cast(Any, Literal).__getitem__(keys)
    claim = create_model(
        "UseClaim",
        __base__=UseClaim,
        area=(area, ...),
    )
    claims: Any = cast(Any, list)[claim]
    return cast(type[UseAnswer], create_model("UseAnswer", __base__=UseAnswer, claims=(claims, ...)))


class ProvenUse(BaseModel):
    phone: str  # as the reviewer's pick was named
    area: str
    verdict: Literal["good", "weak"]
    quote: str
    meaning_en: str
    source: str
    time_text: str | None
    url: str


class VideoUses(BaseModel):
    video_id: str
    uses: list[ProvenUse]
    dropped: list[Dropped]


class FoundUses(BaseModel):
    model: str
    llm_calls: int
    llm_cost_usd: float
    videos: list[VideoUses]


def names_area(quote: str, area: AreaSpec) -> bool:
    """The quote contains one of the feature's words (stems, any script)."""
    text = f" {norm(quote).casefold()} "
    return any(w.casefold() in text for w in area.words)


def names_phone(quote: str, phone: str) -> bool:
    """The quote names this product: its brand or a model word ("Poco", "P4", "Fusion")."""
    text = norm(quote).casefold()
    words = [w for w in re.findall(r"[a-z0-9+]+", phone.casefold()) if len(w) >= 2 and w not in ("5g", "galaxy")]
    return any(re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", text) for w in words)


def areas_for(must_haves: list[str], cat: Category = PHONE) -> tuple[list[str], list[str]]:
    """The shopper's must-haves as the category's features ("photography" → camera), and the ones it doesn't track."""
    found: list[str] = []
    other: list[str] = []
    for m in must_haves:
        word = " ".join(re.findall(r"[a-z0-9]+", m.lower()))
        hit = next(
            (
                a.key
                for a in cat.areas
                if word == a.key or any(w.strip() and (w.strip() in word or word in w.strip()) for w in a.words)
            ),
            None,
        )
        if hit is None:
            other.append(m)
        elif hit not in found:
            found.append(hit)
    return found, other


def prove_uses(v: Video, picks: list[str], answer: UseAnswer, cat: Category = PHONE) -> VideoUses:
    assert v.page is not None
    specs = {a.key: a for a in cat.areas}
    kept: list[ProvenUse] = []
    dropped: list[Dropped] = []
    allowed = set(picks)
    # One sentence credited to several products ("the camera is good too") is only kept for the ones it names.
    credited: dict[str, set[str]] = {}
    for c in answer.claims:
        credited.setdefault(norm(c.quote), set()).add(c.phone)
    for c in answer.claims:
        kind = f"use:{c.area}"
        if c.area not in specs:
            dropped.append(Dropped(kind=kind, quote=c.quote, reason=f"{c.area!r} isn't a feature we track"))
            continue
        if c.phone not in allowed:
            dropped.append(Dropped(kind=kind, quote=c.quote, reason=f"{c.phone!r} isn't one of their picks"))
            continue
        if len(credited[norm(c.quote)]) > 1 and not names_phone(c.quote, c.phone):
            dropped.append(Dropped(kind=kind, quote=c.quote, reason="the same sentence was credited to several phones"))
            continue
        place = locate(c.quote, v.page, v.transcript, c.segment)
        if place is None:
            dropped.append(Dropped(kind=kind, quote=c.quote, reason="quote not found word for word"))
            continue
        if not names_area(c.quote, specs[c.area]):
            dropped.append(Dropped(kind=kind, quote=c.quote, reason=f"the quote doesn't name {c.area}"))
            continue
        base = f"https://www.youtube.com/watch?v={v.page.video_id}"
        kept.append(
            ProvenUse(
                phone=c.phone,
                area=c.area,
                verdict=c.verdict,
                quote=c.quote,
                meaning_en=c.meaning_en,
                source=place.source,
                time_text=place.time_text,
                url=f"{base}&t={place.start_s}s" if place.start_s is not None else base,
            )
        )
    return VideoUses(video_id=v.hit.video_id, uses=kept, dropped=dropped)


def find_uses(
    run: Collection,
    videos: list[Proven],
    llm: LLM,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    cat: Category = PHONE,
) -> FoundUses:
    emit = on_event or (lambda _e: None)
    picks = {p.video_id: [x.phone for x in p.picks] for p in videos}
    schema = answer_model(tuple(a.key for a in cat.areas))
    system = system_prompt(cat)

    def one(v: Video) -> VideoUses | None:
        names = picks.get(v.hit.video_id) or []
        if v.page is None or not names:
            return None
        emit(
            {
                "type": "tool",
                "tool": "llm",
                "step": "what each phone is good at",
                "v": v.hit.video_id,
                "status": "start",
            }
        )
        prompt = user_prompt(v.page, v.transcript) + f"\n\n{cat.header}:\n" + "\n".join(f"- {n}" for n in names)
        answer, _ = llm.structured(system, prompt, schema)
        out = prove_uses(v, names, answer, cat)
        emit({"type": "uses", "v": v.hit.video_id, "found": len(out.uses)})
        return out

    with ThreadPoolExecutor(max_workers=6) as pool:
        found = [u for u in pool.map(one, run.videos) if u is not None]
    return FoundUses(model=llm.model, llm_calls=llm.calls, llm_cost_usd=round(llm.cost_usd, 6), videos=found)


class UseMention(BaseModel):
    video_id: str
    channel: str
    disclosed: bool
    labels: list[str]
    verdict: Literal["good", "weak"]
    quote: str
    meaning_en: str
    time_text: str | None
    url: str


class AreaPhone(BaseModel):
    name: str
    key: str
    good: int  # reviews praising it for this feature
    good_no_disclosure: int
    good_disclosed: int
    weak: int
    mentions: list[UseMention]


class AreaBoard(BaseModel):
    area: str
    name: str
    focus: bool  # the shopper said this matters
    reviews: int  # reviews with at least one opinion on this feature
    phones: list[AreaPhone]
    best_no_disclosure: str | None
    best_all: str | None


def tally_uses(
    videos: list[Proven], found: FoundUses, board: Board, focus: list[str], cat: Category = PHONE
) -> list[AreaBoard]:
    """Per feature: which products reviewers praise for it, split by reviewers with nothing to disclose vs a tie."""
    by_id = {v.video_id: v for v in videos}
    names = {p.key: p.name for p in board.phones}
    out: list[AreaBoard] = []
    for spec in cat.areas:
        area = spec.key
        mentions: dict[str, dict[tuple[str, str], UseMention]] = {}
        spelled: dict[str, str] = {}  # the reviewer's own spelling, for products not in the overall list
        reviews: set[str] = set()
        for vu in found.videos:
            v = by_id.get(vu.video_id)
            if v is None:
                continue
            for u in vu.uses:
                if u.area != area:
                    continue
                reviews.add(vu.video_id)
                k = phone_key(u.phone)
                spelled.setdefault(k, u.phone)
                mentions.setdefault(k, {}).setdefault(
                    (vu.video_id, u.verdict),
                    UseMention(
                        video_id=v.video_id,
                        channel=v.channel,
                        disclosed=v.label_names != [NO_DISCLOSURE],
                        labels=v.label_names,
                        verdict=u.verdict,
                        quote=u.quote,
                        meaning_en=u.meaning_en,
                        time_text=u.time_text,
                        url=u.url,
                    ),
                )
        if not mentions and area not in focus:
            continue
        phones: list[AreaPhone] = []
        for k, ms in mentions.items():
            rows = list(ms.values())
            good = [m for m in rows if m.verdict == "good"]
            phones.append(
                AreaPhone(
                    name=names.get(k, spelled[k]),
                    key=k,
                    good=len(good),
                    good_no_disclosure=sum(not m.disclosed for m in good),
                    good_disclosed=sum(m.disclosed for m in good),
                    weak=sum(m.verdict == "weak" for m in rows),
                    mentions=sorted(rows, key=lambda m: (m.verdict != "good", m.disclosed, m.channel)),
                )
            )
        phones.sort(key=lambda p: (-p.good_no_disclosure, -p.good, p.weak, p.name))
        best_nd = next((p.name for p in phones if p.good_no_disclosure), None)
        best_all = max(phones, key=lambda p: (p.good, -p.weak), default=None)
        out.append(
            AreaBoard(
                area=area,
                name=spec.name,
                focus=area in focus,
                reviews=len(reviews),
                phones=phones,
                best_no_disclosure=best_nd,
                best_all=best_all.name if best_all and best_all.good else None,
            )
        )
    out.sort(key=lambda a: (not a.focus, -a.reviews))
    return out
