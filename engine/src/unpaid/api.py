"""HTTP API for the board. POST /ask streams every step as one JSON line, then the result.

Replay mode (the default) needs no keys and spends nothing; it answers any question that was recorded before.
"""

from __future__ import annotations

import json
import queue
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from unpaid.agent import NotABuyingQuestion, Workspace, ask
from unpaid.board import REPORT_FILE, Showcase
from unpaid.config import CACHE_DIR, EVIDENCE_DIR, SHOWCASE_DIR
from unpaid.llm import LLMError, LLMNotRecorded, SpendLimitReached
from unpaid.serpapi import BudgetExceeded, Client, NotRecorded, SerpApiError, fetch_account

app = FastAPI(title="Unpaid")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
# Every route sits under /api: the web app calls /api/..., locally through its dev proxy and on Vercel through the
# top-level rewrite, which passes the full path on (vercel.json).
api = APIRouter(prefix="/api")
# One run at a time, so two clicks can never spend searches twice.
RUN_LOCK = threading.Lock()
WORK_DIR: Path = CACHE_DIR


class AskBody(BaseModel):
    question: str = Field(min_length=3, max_length=300)
    replay: bool = True
    # Replay only: wait this long between events so a viewer can follow the steps. Live runs are never slowed.
    pace_ms: int = Field(default=0, ge=0, le=500)


def problem(e: Exception) -> tuple[int, str]:
    """HTTP status and a plain reason for everything a run can refuse."""
    if isinstance(e, NotABuyingQuestion):
        return 422, str(e)
    if isinstance(e, NotRecorded | LLMNotRecorded | LookupError):
        return 404, "This question hasn't been recorded. Switch replay off to run it live (needs API keys)."
    if isinstance(e, BudgetExceeded | SpendLimitReached):
        return 409, str(e)
    if isinstance(e, SerpApiError | LLMError):
        return 502, str(e)
    return 500, f"{type(e).__name__}: {e}"


def stream(body: AskBody) -> Iterator[str]:
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()

    def work() -> None:
        try:
            ws = Workspace.open(replay=body.replay, root=WORK_DIR)
            events.put({"type": "start", "mode": "replay" if body.replay else "live"})
            show = ask(body.question, ws, on_event=events.put)
            save_report(show)
            events.put({"type": "result", "id": show.id, "showcase": show.model_dump(mode="json")})
        except Exception as e:  # every failure becomes one clear event
            status, detail = problem(e)
            events.put({"type": "error", "status": status, "detail": detail})
        finally:
            events.put(None)

    if not RUN_LOCK.acquire(blocking=False):
        yield json.dumps({"type": "error", "status": 429, "detail": "Another question is running. Try again soon."})
        return
    try:
        threading.Thread(target=work, daemon=True).start()
        while (event := events.get()) is not None:
            yield json.dumps(event, ensure_ascii=False) + "\n"
            if body.replay and body.pace_ms and event.get("type") in ("tool", "video"):
                time.sleep(body.pace_ms / 1000)
    finally:
        RUN_LOCK.release()


@api.post("/ask")
def ask_route(body: AskBody) -> StreamingResponse:
    return StreamingResponse(stream(body), media_type="application/x-ndjson")


def load_reports() -> dict[str, tuple[Showcase, bool]]:
    """Every report by id: the recorded sample (published evidence) and any saved from live runs."""
    out: dict[str, tuple[Showcase, bool]] = {}
    for path in sorted((WORK_DIR / "reports").glob("*.json")):
        try:
            s = Showcase.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            # Saved by an older version of Unpaid: skip it rather than break the whole list.
            continue
        out[s.id] = (s, False)
    # Recorded runs in evidence/ are the samples: the phone showcase and any other question recorded there.
    for sample in [SHOWCASE_DIR / "board.json", *sorted(EVIDENCE_DIR.glob(f"*/{REPORT_FILE}"))]:
        if not sample.exists():
            continue
        try:
            s = Showcase.model_validate_json(sample.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            continue
        out[s.id] = (s, True)
    return out


def save_report(show: Showcase) -> None:
    folder = WORK_DIR / "reports"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{show.id}.json").write_text(show.model_dump_json(indent=1), encoding="utf-8")


@api.get("/reports")
def reports() -> list[dict[str, Any]]:
    """Report cards, newest first."""
    rows = []
    for s, sample in load_reports().values():
        labelled = [v for v in s.videos if v.labels]
        top = s.board.top_all[0] if s.board.top_all else None
        low = next((p.lowest for p in s.prices if p.phone == top), None)
        rows.append(
            {
                "id": s.id,
                "question": s.question,
                "checked_at": s.checked_at.isoformat(),
                "sample": sample,
                "reviews": len(s.videos),
                "with_money_ties": len(labelled),
                "top_pick": top,
                "top_pick_price": low.price if low else None,
            }
        )
    return sorted(rows, key=lambda r: r["checked_at"], reverse=True)


@api.get("/reports/{report_id}")
def report(report_id: str) -> dict[str, Any]:
    found = load_reports().get(report_id)
    if found is None:
        raise HTTPException(404, "No report with this id.")
    s, sample = found
    return {"sample": sample, "report": s.model_dump(mode="json")}


@api.get("/accuracy")
def accuracy() -> dict[str, Any]:
    """How the labels compared with a review checked by reading every line (computed by `uv run verify`)."""
    numbers = EVIDENCE_DIR / "numbers.json"
    if not numbers.exists():
        raise HTTPException(404, "run: uv run verify")
    data = json.loads(numbers.read_text(encoding="utf-8"))
    labels = data.get("labels") or {}
    return {"videos": labels.get("videos"), "scores": labels.get("answer_key"), "per_label": labels.get("per_label")}


@api.get("/account")
def account() -> dict[str, Any]:
    """SerpApi searches left (a free call). Without a key the app runs in replay mode only."""
    client = Client.from_env()
    if client.key is None:
        return {"mode": "replay", "searches_left": None, "reason": "no SERPAPI_API_KEY: replay only"}
    try:
        info = fetch_account(client.key)
    except SerpApiError as e:
        raise HTTPException(502, str(e)) from None
    return {"mode": "live", "searches_left": info.get("total_searches_left"), "keep_at_least": client.keep_at_least}


app.include_router(api)
