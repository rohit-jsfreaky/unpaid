from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from unpaid.agent import Intent, NotABuyingQuestion, budget_pattern, plan_from
from unpaid.collect import showcase_plan
from unpaid.config import load_settings
from unpaid.llm import LLMNotRecorded
from unpaid.serpapi import BudgetExceeded

DEMO = "best phone under 30k for camera and battery, big billion days"


def intent(**kw: Any) -> Intent:
    base: dict[str, Any] = {
        "is_buying_question": True,
        "product": "phone",
        "budget_inr": 30000,
        "sale_event": "Big Billion Days",
        "must_haves": ["camera", "battery"],
    }
    return Intent.model_validate({**base, **kw})


def test_demo_question_plans_exactly_the_recorded_searches() -> None:
    s = load_settings()
    assert plan_from(DEMO, intent(), s) == showcase_plan(s)


def test_plan_without_budget_or_sale() -> None:
    p = plan_from("good earbuds?", intent(product="Earbuds!", budget_inr=None, sale_event=None), load_settings())
    assert [(q.text, q.hl) for q in p.queries] == [("best earbuds", "en"), ("best earbuds hindi", "hi")]
    assert re.search(p.title_pattern, "Top 5 Earbuds of 2026", re.IGNORECASE)


@pytest.mark.parametrize(
    ("title", "hit"),
    [
        ("Best phone under 30k", True),
        ("Top 5 under ₹30,000", True),
        ("30000 to 35000 phones", True),
        ("30 हज़ार के अंदर", True),
        ("Best phone under 300k", False),
        ("Best phone under 20k", False),
    ],
)
def test_budget_pattern(title: str, hit: bool) -> None:
    assert bool(re.search(budget_pattern(30000), title, re.IGNORECASE)) is hit


def test_api_problems_map_to_clear_statuses() -> None:
    from unpaid.api import problem

    assert problem(NotABuyingQuestion("x"))[0] == 422
    assert problem(LLMNotRecorded("x"))[0] == 404
    assert problem(BudgetExceeded("x"))[0] == 409


def lines(text: str) -> list[dict[str, Any]]:
    return [json.loads(x) for x in text.splitlines() if x.strip()]


def test_api_replays_the_demo_question_with_no_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    import unpaid.api as api

    monkeypatch.setattr(api, "WORK_DIR", tmp_path)  # nothing cached on this laptop can help
    monkeypatch.setenv("SERPAPI_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    http = TestClient(api.app)
    events = lines(http.post("/ask", json={"question": DEMO, "replay": True}).text)
    kinds = [e["type"] for e in events]
    assert kinds[0] == "start" and kinds[-1] == "result" and "plan" in kinds and kinds.count("video") == 21
    cost = next(e for e in events if e["type"] == "cost")
    assert cost["searches_used"] == 0 and cost["llm_calls"] == 0
    show = events[-1]["showcase"]
    assert show["board"]["top_all"][0] == "Motorola Edge 70 Fusion"

    other = lines(http.post("/ask", json={"question": "best laptop under 60k", "replay": True}).text)
    assert other[-1]["type"] == "error" and other[-1]["status"] == 404
    listed = http.get("/reports").json()
    sample = next(r for r in listed if r["sample"])
    assert (sample["id"], sample["reviews"], sample["with_money_ties"]) == ("best-phone-under-30000-2026-10-08", 21, 9)
    assert sample["top_pick"] == "Motorola Edge 70 Fusion" and sample["top_pick_price"] == 25799
    got = http.get(f"/reports/{sample['id']}").json()
    assert got["sample"] and got["report"]["question"] == DEMO and len(got["report"]["reviews"]) == 21
    assert http.get("/reports/nope").status_code == 404
    assert http.get("/accuracy").json()["videos"] == 21


def test_reports_list_skips_a_report_saved_by_an_older_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    import unpaid.api as api

    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "old.json").write_text('{"id": "old", "question": "x"}', encoding="utf-8")
    monkeypatch.setattr(api, "WORK_DIR", tmp_path)
    listed = TestClient(api.app).get("/reports")
    assert listed.status_code == 200 and [r["sample"] for r in listed.json()] == [True]
