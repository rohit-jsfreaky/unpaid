"""The agent: a shopper's question → a plan → SerpApi tools → labels → the board, with every step as an event.

The LLM only reads the question into fields (product, budget, sale, must-haves). Code turns those fields into the
YouTube queries and the title filter, so the same question always gets the same plan.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from unpaid.board import Showcase, assemble, ranked, top_phones
from unpaid.category import category_for
from unpaid.collect import Plan, Query, collect
from unpaid.config import CACHE_DIR, EVIDENCE_DIR, SHOWCASE_DIR, Settings, load_settings
from unpaid.label import label_all
from unpaid.links import LinkBook
from unpaid.llm import LLM
from unpaid.prices import prices
from unpaid.serpapi import Cache, Client
from unpaid.uses import find_uses

Event = dict[str, Any]
OnEvent = Callable[[Event], None]

INTENT_SYSTEM = """You read a shopper's question and fill in search settings for finding YouTube review videos in
India. Don't answer the question.

- is_buying_question: true only if they want help choosing a product to buy.
- product: the kind of product in one or two plain lowercase English words, singular ("phone", "earbuds",
  "laptop", "smartwatch"). Use the shopper's own word when it's a common one: "phone" stays "phone".
- budget_inr: the most they want to spend, in whole rupees ("30k" = 30000, "1.5 lakh" = 150000), or null.
- sale_event: the sale they mention, lowercase ("big billion days", "great indian festival"), or null.
- must_haves: short lowercase features they care about ("camera", "battery", "gaming"), or an empty list."""


class Intent(BaseModel):
    is_buying_question: bool
    product: str
    budget_inr: int | None
    sale_event: str | None
    must_haves: list[str]


def _clean(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9+]+", text.lower()))


def budget_pattern(budget: int) -> str:
    """Titles that name this budget: 30000 → "30k", "30,000", "₹30", "30 हज़ार"."""
    k = budget // 1000
    return rf"{k}\s?k\b|{k},?000|₹\s?{k}\b|{k}\s?(?:हज़ार|हजार)"


def plan_from(question: str, intent: Intent, s: Settings) -> Plan:
    product = " ".join(_clean(intent.product).split()[:3]) or "phone"
    if intent.budget_inr and 1_000 <= intent.budget_inr <= 1_000_000:
        base = f"best {product} under {intent.budget_inr}"
        pattern = budget_pattern(intent.budget_inr)
    else:
        base = f"best {product}"
        pattern = rf"\b{re.escape(product)}"
    queries = [Query(text=base, hl="en")]
    event = _clean(intent.sale_event or "")
    if event:
        queries.append(Query(text=f"{base} {event}", hl="en"))
    if "hi" in s.languages:
        queries.append(Query(text=f"{base} hindi", hl="hi"))
    must = [w for w in (" ".join(_clean(m).split()[:3]) for m in intent.must_haves) if w][:5]
    return Plan(
        question=question,
        queries=queries,
        title_pattern=pattern,
        window_days=s.window_days,
        max_videos=s.max_videos,
        must_haves=must,
        product=product,
    )


def normalise_question(question: str) -> str:
    """'Best phone under 30k?' and 'best phone  under 30k' are one question, so they share one recorded run."""
    return " ".join(question.split()).casefold().rstrip(" .?!")


def read_question(llm: LLM, question: str) -> Intent:
    intent, _ = llm.structured(INTENT_SYSTEM, question.strip(), Intent)
    return intent


@dataclass
class Workspace:
    """Where one run reads and writes. Recorded evidence is always readable, so the showcase replays for free."""

    client: Client
    llm: LLM
    links: LinkBook

    @classmethod
    def open(cls, replay: bool, root: Path = CACHE_DIR, llm_dir: Path | None = None) -> Workspace:
        """`llm_dir` saves new LLM answers somewhere else, e.g. into the showcase evidence when recording it."""
        client = Client.from_env("replay" if replay else None)
        client.cache = Cache(write_dir=root, read_dirs=(root, EVIDENCE_DIR))
        write = llm_dir or root / "llm"
        # Every recorded run in evidence/ is readable, so any question asked before replays for free.
        recorded = sorted(p.parent for p in EVIDENCE_DIR.glob("*/llm/*.json"))
        llm = LLM.from_env(
            write_dir=write,
            read_dirs=tuple(dict.fromkeys((write, root / "llm", SHOWCASE_DIR / "llm", *recorded))),
            mode="replay" if replay else None,
        )
        books = tuple(sorted(EVIDENCE_DIR.glob("*/links.json")))
        links = LinkBook(root / "links.json", live=not replay, also_read=books)
        return cls(client=client, llm=llm, links=links)


class NotABuyingQuestion(ValueError):
    pass


def ask(question: str, ws: Workspace, on_event: OnEvent | None = None) -> Showcase:
    emit = on_event or (lambda _e: None)
    s = load_settings()
    question = normalise_question(question)
    emit({"type": "tool", "tool": "llm", "step": "read the question", "status": "start"})
    intent = read_question(ws.llm, question)
    emit({"type": "tool", "tool": "llm", "step": "read the question", "status": "done", "intent": intent.model_dump()})
    if not intent.is_buying_question:
        raise NotABuyingQuestion("Ask about something to buy, e.g. 'best phone under 30k for camera'.")
    plan = plan_from(question, intent, s)
    cat = category_for(plan.product, plan.must_haves, ws.llm)
    plan = plan.model_copy(update={"category": cat})
    emit({"type": "plan", "plan": plan.model_dump(), "must_haves": intent.must_haves})

    run = collect(ws.client, plan, s.gl, on_event=emit)
    emit({"type": "tool", "tool": "links", "step": "follow description links", "status": "start"})
    labelled = label_all(run, ws.llm, ws.links, on_event=emit, cat=cat)
    uses = find_uses(run, labelled.videos, ws.llm, on_event=emit, cat=cat)
    board, areas, _ = ranked(run, labelled, uses)
    phones = top_phones(board, areas)
    for p in phones:
        emit({"type": "tool", "tool": "google_shopping", "q": p, "status": "start"})
    found = prices(ws.client, phones)
    for pp in found:
        emit({"type": "tool", "tool": "google_shopping", "q": pp.phone, "status": "done", "offers": len(pp.offers)})
    show = assemble(question, run, labelled, uses, found)
    emit(
        {
            "type": "cost",
            "searches_used": ws.client.searches_used,
            "llm_calls": ws.llm.calls,
            "llm_cached": ws.llm.cached,
        }
    )
    return show
