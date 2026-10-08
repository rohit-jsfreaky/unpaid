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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from unpaid.agent import NotABuyingQuestion, Workspace, ask
from unpaid.board import Showcase
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
            events.put({"type": "result", "showcase": show.model_dump(mode="json")})
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


@app.post("/ask")
def ask_route(body: AskBody) -> StreamingResponse:
    return StreamingResponse(stream(body), media_type="application/x-ndjson")


@app.get("/showcase")
def showcase() -> dict[str, Any]:
    """The recorded demo run, plus the numbers `uv run verify` computed from it."""
    board = SHOWCASE_DIR / "board.json"
    if not board.exists():
        raise HTTPException(404, "run: uv run unpaid board")
    numbers = EVIDENCE_DIR / "numbers.json"
    return {
        "showcase": Showcase.model_validate_json(board.read_text(encoding="utf-8")).model_dump(mode="json"),
        "numbers": json.loads(numbers.read_text(encoding="utf-8")) if numbers.exists() else None,
    }


@app.get("/account")
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
