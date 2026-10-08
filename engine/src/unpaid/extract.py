"""AI finds: one LLM call per video proposes disclosure sentences and the phones recommended.

Nothing here is trusted. proof.py keeps a sentence only if it is found word for word in the stored text.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from unpaid.llm import LLM
from unpaid.youtube import Transcript, VideoPage

SYSTEM = """You read one YouTube video's description and transcript. The videos are Indian phone reviews and buying
lists, in English, Hindi, Hinglish, Telugu, Malayalam or a mix.

Find two things.

A) Every place the creator states a money tie, as one of these kinds:
- paid_sponsorship: the video is sponsored by, a paid partnership with, or made in collaboration with a company
  (including a "#Collab" tag next to a company's tag). `party` = that company.
- free_unit: a company sent, provided or gave the creator the device or review unit. `party` = that company, or
  "respective brands" when the creator says it that way.
- affiliate_statement: the creator says the links are affiliate links, or that they earn a commission, or that they
  are an Amazon Associate.
- denial: the creator says the video is NOT sponsored, or that no brand paid them.
These are NOT money ties. Skip them: "for sponsorship / business / collab inquiries contact ...", "all content
provided by this channel is for educational purposes", copyright or fair-use notes, talk about other people's sponsored
ads, bank card offers and sale discounts, product tagging ("I've tagged the phones"), and the channel promoting its own
app, channel, merch or giveaway.

B) Every phone the creator recommends for the buyer, with its rank if they number their list (1 = their top pick).

Quoting rules (strict; your quotes are checked by a program and dropped if they don't match):
- Copy each quote EXACTLY from the text below: same script, same spelling, same punctuation, same capitals.
  Never translate, transliterate, fix or shorten words inside the quote.
- Use the shortest exact span that shows the point, at most 200 characters.
- A transcript quote must come from one segment [i] (it may run on into [i+1]); give that i as `segment`.
  A description quote has `segment` null.
- `meaning_en`: a plain English meaning of the quote (a translation if it isn't English).
- `phone`: the standard English "Brand Model" name, e.g. "Motorola Edge 60 Pro", "iQOO Neo 10", "Samsung Galaxy
  M36". Don't include RAM/storage or colour.
If there is nothing for a list, return an empty list. Never invent anything."""


class Claim(BaseModel):
    kind: Literal["paid_sponsorship", "free_unit", "affiliate_statement", "denial"]
    party: str | None
    source: Literal["description", "transcript"]
    segment: int | None
    quote: str
    meaning_en: str


class Pick(BaseModel):
    phone: str
    rank: int | None
    source: Literal["description", "transcript"]
    segment: int | None
    quote: str
    meaning_en: str


class Extraction(BaseModel):
    claims: list[Claim]
    picks: list[Pick]


def user_prompt(page: VideoPage, transcript: Transcript | None) -> str:
    lines = [f"TITLE: {page.title}", f"CHANNEL: {page.channel}", "", "DESCRIPTION:", page.description, ""]
    if transcript and transcript.segments:
        lines.append("TRANSCRIPT (one segment per line, [index] m:ss text):")
        lines += [f"[{i}] {s.time_text} {s.text}" for i, s in enumerate(transcript.segments)]
    else:
        lines.append("TRANSCRIPT: none available")
    return "\n".join(lines)


def extract(llm: LLM, page: VideoPage, transcript: Transcript | None) -> tuple[Extraction, str]:
    return llm.structured(SYSTEM, user_prompt(page, transcript), Extraction)
