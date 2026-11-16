"""Offline tests for the optional usage-event sink. No server, no network."""

import asyncio
import json
import threading
import time

import httpx
import pytest

from openfisca_mcp import analytics
from openfisca_mcp.analytics import LoomSink, classify_result
from openfisca_mcp.errors import ValidationError
from mcp.types import TextContent

SITUATION = {"persons": {"Alice": {"salary": {"2026-01": 4321}}}, "households": {"h": {"adults": ["Alice"]}}}


class Recorder:
    def __init__(self, status=202, delay=0.0, fail=False):
        self.requests = []
        self.status, self.delay, self.fail = status, delay, fail

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise httpx.ConnectError("collector down")
        self.requests.append(request)
        return httpx.Response(self.status, json={"ok": True})


def sink(recorder, **kwargs):
    return LoomSink(
        url="http://loom.internal:8080",
        tenant="rules-test",
        secret="s3cret",
        transport=httpx.MockTransport(recorder),
        **kwargs,
    )


def run_in_fresh_context(fn):
    """Each MCP session runs in its own task context; mirror that."""
    import contextvars

    return contextvars.copy_context().run(fn)


def test_disabled_without_url_or_tenant():
    assert not LoomSink(url="", tenant="x").enabled
    assert not LoomSink(url="http://x", tenant="").enabled
    off = LoomSink(url="", tenant="")
    off.session_started({})
    off.tool_called("calculate", "ok", 3, {})  # no worker, no error


def test_session_and_tool_events_shape_and_privacy():
    rec = Recorder()
    s = sink(rec)
    headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1", "user-agent": "SomeAgent/1.0"}

    def session():
        s.session_started(headers)
        s.tool_called("calculate", "ok", 12.7, headers)

    run_in_fresh_context(session)
    assert s.flush()
    assert len(rec.requests) == 2
    start, call = (json.loads(r.content) for r in rec.requests)

    assert start["payload"]["name"] == analytics.SESSION_START
    assert call["payload"]["name"] == analytics.TOOL_CALL
    data = call["payload"]["data"]
    assert data["tool_calls_names"] == "calculate"
    assert data["outcome"] == "ok" and data["latency_ms"] == 12
    assert "error_class" not in data
    assert data["trace_id"] and data["trace_id"] == start["payload"]["data"]["trace_id"]

    req = rec.requests[1]
    assert str(req.url) == "http://loom.internal:8080/collect"
    assert req.headers["x-loom-tenant"] == "rules-test"
    assert req.headers["x-loom-source"] == "rules-test"
    assert req.headers["x-loom-auth"] == "s3cret"
    assert req.headers["x-forwarded-for"] == "203.0.113.9"
    # The client address travels only as a header for the collector's salted hash.
    for r in rec.requests:
        assert b"203.0.113.9" not in r.content


def test_source_id_defaults_to_tenant_and_can_be_set():
    assert LoomSink(url="http://x", tenant="rules-a").source_id == "rules-a"
    assert LoomSink(url="http://x", tenant="rules-a", source_id="rules-b").source_id == "rules-b"


def test_internal_traffic_marked_by_header_or_user_agent():
    rec = Recorder()
    s = sink(rec)
    run_in_fresh_context(lambda: s.session_started({"x-agora-internal": "smoke"}))
    run_in_fresh_context(lambda: s.session_started({"user-agent": "contentlibrary-rules-smoke/1"}))
    run_in_fresh_context(lambda: s.session_started({"user-agent": "Claude-User/1"}))
    assert s.flush()
    assert [r.headers["x-loom-source"] for r in rec.requests] == ["internal", "internal", "rules-test"]


def test_session_internal_flag_carries_to_tool_calls():
    rec = Recorder()
    s = sink(rec)

    def session():
        s.session_started({"x-agora-internal": "1"})
        s.tool_called("list_entities", "ok", 1, {})

    run_in_fresh_context(session)
    assert s.flush()
    assert rec.requests[-1].headers["x-loom-source"] == "internal"


def test_error_outcome_and_unknown_tool_names():
    rec = Recorder()
    s = sink(rec)
    s.tool_called("calculate", "validation_error", 2, {})
    s.tool_called("Alice's salary 4321", "ok", 2, {})
    assert s.flush()
    bad, unknown = (json.loads(r.content)["payload"] for r in rec.requests)
    assert bad["data"]["error_class"] == "validation_error"
    assert unknown["data"]["tool_calls_names"] == "unknown"
    assert "Alice" not in json.dumps(unknown)


def test_never_raises_or_blocks_when_collector_is_down_or_slow():
    for rec in (Recorder(fail=True), Recorder(delay=0.5), Recorder(status=500)):
        s = sink(rec, queue_size=2)
        started = time.perf_counter()
        for _ in range(50):
            s.tool_called("calculate", "ok", 1, {})
        assert time.perf_counter() - started < 0.2
    assert s.dropped >= 0


def test_queue_full_drops_instead_of_waiting():
    gate = threading.Event()

    def blocked(request):
        gate.wait(5)
        return httpx.Response(202)

    s = LoomSink(url="http://x", tenant="t", transport=httpx.MockTransport(blocked), queue_size=1)
    for _ in range(10):
        s.tool_called("calculate", "ok", 1, {})
    assert s.dropped >= 8
    gate.set()
    assert s.flush()


def test_classify_result_reads_only_the_error_type():
    from openfisca_mcp.server import format_error, format_result

    assert classify_result(format_result({"persons": {"Alice": {"x": 1}}})) == "ok"
    assert classify_result(format_error(ValidationError("Situation is required"))) == "validation_error"
    assert classify_result([TextContent(type="text", text="plain")]) == "ok"
    assert classify_result(None) == "ok"


def test_server_records_tool_calls_without_arguments(monkeypatch):
    from openfisca_mcp import server

    rec = Recorder()
    monkeypatch.setattr(server, "analytics", sink(rec))

    async def go():
        await server.call_tool("calculate", {"situation": {}})
        await server.call_tool("not_a_tool", {"situation": SITUATION})

    asyncio.run(go())
    assert server.analytics.flush()
    bodies = [r.content.decode() for r in rec.requests]
    assert len(bodies) == 2
    first, second = (json.loads(b)["payload"]["data"] for b in bodies)
    assert first["tool_calls_names"] == "calculate" and first["outcome"] == "validation_error"
    assert second["tool_calls_names"] == "unknown" and second["outcome"] == "validation_error"
    for body in bodies:
        for secret in ("Alice", "4321", "salary", "households"):
            assert secret not in body
