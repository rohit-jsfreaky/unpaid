from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from unpaid.config import PROBE_DIR, load_settings
from unpaid.serpapi import BudgetExceeded, Cache, Client, NotRecorded, Params, SerpApiError, receipt, request_key

KEY = "k" * 64
VIDEO: Params = {"engine": "youtube_video", "v": "abc123", "gl": "in"}


def fake_serpapi(calls: list[str], status: int = 200) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        params = dict(request.url.params)
        params.pop("api_key")
        body = {
            "search_metadata": {
                "id": "x1",
                "json_endpoint": "https://serpapi.com/searches/a/x1.json",
                "created_at": "2026-10-08 00:00:00 UTC",
            },
            "search_parameters": params,
            "title": "Test video",
        }
        return httpx.Response(status, json=body if status == 200 else {"error": "Invalid API key"})

    return httpx.MockTransport(handler)


def live_client(tmp_path: Path, calls: list[str], left: int = 200, status: int = 200) -> Client:
    return Client(
        mode="live",
        key=KEY,
        cache=Cache(write_dir=tmp_path, read_dirs=(tmp_path,)),
        account=lambda _k: {"total_searches_left": left},
        transport=fake_serpapi(calls, status),
    )


def test_request_key_ignores_api_key_and_order() -> None:
    assert request_key({"v": "a", "gl": "in", "api_key": "s"}) == request_key({"gl": "in", "v": "a"})
    assert request_key({"v": "a", "num": 2}) == request_key({"v": "a", "num": "2"})
    assert request_key({"v": "a", "hl": "en"}) != request_key({"v": "a", "hl": "hi"})


def test_record_once_then_replay_free(tmp_path: Path) -> None:
    calls: list[str] = []
    client = live_client(tmp_path, calls)
    first = client.search(VIDEO)
    again = client.search(VIDEO)
    assert (first.from_cache, again.from_cache, client.searches_used, len(calls)) == (False, True, 1, 1)
    stored = "".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*.json"))
    assert KEY not in stored and stored
    replay = Client(mode="replay", key=None, cache=Cache(write_dir=tmp_path, read_dirs=(tmp_path,)))
    assert replay.search(VIDEO).data["title"] == "Test video" and replay.searches_used == 0


def test_replay_refuses_unrecorded(tmp_path: Path) -> None:
    replay = Client(mode="replay", key=None, cache=Cache(write_dir=tmp_path, read_dirs=(tmp_path,)))
    with pytest.raises(NotRecorded):
        replay.search(VIDEO)
    with pytest.raises(NotRecorded):
        replay.check_budget(1)


def test_budget_guard_blocks_before_any_call(tmp_path: Path) -> None:
    calls: list[str] = []
    keep = load_settings().keep_at_least
    client = live_client(tmp_path, calls, left=keep + 2)
    client.keep_at_least = keep
    planned = client.missing([VIDEO, {**VIDEO, "v": "b"}, {**VIDEO, "v": "c"}])
    with pytest.raises(BudgetExceeded):
        client.check_budget(len(planned))
    assert calls == []
    assert client.check_budget(2) == keep + 2


def test_http_error_never_leaks_key(tmp_path: Path) -> None:
    client = live_client(tmp_path, [], status=401)
    with pytest.raises(SerpApiError) as err:
        client.search(VIDEO)
    assert KEY not in str(err.value) and "401" in str(err.value)


def test_cache_refuses_to_store_the_key(tmp_path: Path) -> None:
    with pytest.raises(SerpApiError):
        Cache(write_dir=tmp_path, read_dirs=(tmp_path,)).put({"v": "x"}, {"echo": f"api_key={KEY}"}, KEY)


def test_raw_probe_files_replay_as_cache() -> None:
    client = Client(mode="replay", key=None, cache=Cache(write_dir=PROBE_DIR, read_dirs=(PROBE_DIR,)))
    hit = client.search({"engine": "youtube", "search_query": "Nothing Phone 3 review", "gl": "in", "hl": "en"})
    labels = [v.get("extensions") or [] for v in hit.data["video_results"]]
    assert any("Earns commission" in x for x in labels)
    r = receipt(hit.data)
    assert r.search_id == "6ac60c83a7d78492f86839e0" and r.created_at.startswith("2026-10-07")
