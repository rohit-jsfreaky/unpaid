"""What do reviewers recommend: all of them, and only those with no disclosure found. Code only, no LLM.

A phone counts once per video. Names the LLM wrote differently ("Realme P4 Pro 5G", "realme P4 Pro") are merged by
brand + model letters and digits; anything else stays separate rather than being guessed.
"""

from __future__ import annotations

import re
from collections import Counter

from pydantic import BaseModel

from unpaid.proof import NO_DISCLOSURE, Proven

DROP_WORDS = {"5g", "galaxy"}
BRAND_ALIASES = {"moto": "motorola"}


def phone_key(name: str) -> str:
    """ "Samsung Galaxy M56 5G" and "samsung M56" → "samsung m56"; "Nothing Phone (4a)" → "nothing phone4a"."""
    words = [w for w in re.findall(r"[a-z0-9+]+", name.lower()) if w not in DROP_WORDS]
    if not words:
        return name.lower()
    words[0] = BRAND_ALIASES.get(words[0], words[0])
    if words[0] == "motorola" and len(words) > 1 and words[1] == "moto":
        words.pop(1)
    if words[0] == "xiaomi" and len(words) > 1 and words[1] in ("redmi", "poco"):
        words.pop(0)
    return f"{words[0]} {''.join(words[1:])}".strip()


class Mention(BaseModel):
    video_id: str
    channel: str
    disclosed: bool
    labels: list[str]
    rank: int | None
    quote: str
    time_text: str | None
    url: str


class PhoneTally(BaseModel):
    key: str
    name: str
    all: int  # videos recommending it
    no_disclosure: int  # ...among videos with no disclosure found
    disclosed: int  # ...among videos with at least one label
    share_all: float
    share_no_disclosure: float
    share_disclosed: float
    best_rank: int | None
    mentions: list[Mention]


class Board(BaseModel):
    videos_with_picks: int
    no_disclosure_videos_with_picks: int
    disclosed_videos_with_picks: int
    phones: list[PhoneTally]  # by `all`, most first
    top_all: list[str]
    top_no_disclosure: list[str]


def _order(p: PhoneTally, field: str) -> tuple[int, int, int, str]:
    return (-getattr(p, field), -p.all, p.best_rank or 99, p.name)


def tally(videos: list[Proven], top: int = 3) -> Board:
    with_picks = [v for v in videos if v.picks]
    clean = [v for v in with_picks if v.label_names == [NO_DISCLOSURE]]
    paid = [v for v in with_picks if v.label_names != [NO_DISCLOSURE]]
    names: dict[str, Counter[str]] = {}
    mentions: dict[str, dict[str, Mention]] = {}
    for v in with_picks:
        disclosed = v.label_names != [NO_DISCLOSURE]
        for p in v.picks:
            k = phone_key(p.phone)
            names.setdefault(k, Counter())[p.phone] += 1
            seen = mentions.setdefault(k, {})
            m = Mention(
                video_id=v.video_id,
                channel=v.channel,
                disclosed=disclosed,
                labels=v.label_names,
                rank=p.rank,
                quote=p.quote,
                time_text=p.time_text,
                url=p.url,
            )
            old = seen.get(v.video_id)
            if old is None or (m.rank is not None and (old.rank is None or m.rank < old.rank)):
                seen[v.video_id] = m

    def share(n: int, of: int) -> float:
        return round(n / of, 3) if of else 0.0

    phones: list[PhoneTally] = []
    for k, ms in mentions.items():
        rows = list(ms.values())
        n_all = len(rows)
        n_clean = sum(not m.disclosed for m in rows)
        ranks = [m.rank for m in rows if m.rank is not None]
        # The usual spelling, preferring one without "5G".
        name = max(names[k].items(), key=lambda kv: (kv[1], "5g" not in kv[0].lower(), -len(kv[0])))[0]
        phones.append(
            PhoneTally(
                key=k,
                name=name,
                all=n_all,
                no_disclosure=n_clean,
                disclosed=n_all - n_clean,
                share_all=share(n_all, len(with_picks)),
                share_no_disclosure=share(n_clean, len(clean)),
                share_disclosed=share(n_all - n_clean, len(paid)),
                best_rank=min(ranks) if ranks else None,
                mentions=sorted(rows, key=lambda m: (m.rank or 99, m.channel)),
            )
        )
    phones.sort(key=lambda p: _order(p, "all"))
    by_clean = sorted(phones, key=lambda p: _order(p, "no_disclosure"))
    return Board(
        videos_with_picks=len(with_picks),
        no_disclosure_videos_with_picks=len(clean),
        disclosed_videos_with_picks=len(paid),
        phones=phones,
        top_all=[p.name for p in phones[:top]],
        top_no_disclosure=[p.name for p in by_clean[:top] if p.no_disclosure],
    )
