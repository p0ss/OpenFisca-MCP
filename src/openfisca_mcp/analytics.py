"""Optional, fire-and-forget usage events for a Loom/Umami-style collector.

Disabled unless both ``LOOM_INGEST_URL`` and ``LOOM_TENANT`` are set. When
enabled, the server records one event per MCP session start and one per tool
call: tenant, tool name, outcome and latency. Nothing else about the call.

``LOOM_SOURCE_ID`` (default: the tenant) is the engine's source id, sent as
``X-Loom-Source`` for public traffic. Use the same id as the ``utm_source`` of
any cross-site cord the engine emits (P118), so a cord's ``cord_source`` lines
up with this source in the journey graph.

Privacy rules this module enforces by construction:

* Tool arguments and results are never passed in. The public API takes a tool
  *name*, an outcome *class* and a duration; there is no parameter that could
  carry a situation, a variable value or a response body. Eligibility inputs
  describe people's circumstances and must not leave the request.
* No raw IP is stored here. The client address is forwarded to the collector
  only as ``X-Forwarded-For`` so the collector can derive its daily-salted
  visitor hash; this module keeps no copy and does not log it.
* The MCP ``session_id`` is a capability for posting messages to a live
  session, so it is never sent. Events from one session share a random
  ``trace_id`` generated here instead.

Our own traffic (smoke tests, health probes, agents) is recorded with
``source_id=internal`` instead of the engine source id so reports can exclude it. A request is internal when it
carries a non-empty ``X-Agora-Internal`` header, or its User-Agent matches
``LOOM_INTERNAL_UA_PATTERN``. Both are self-declared and so only ever used to
*exclude* traffic, never to trust it.

Delivery is best effort. Events go on a bounded in-memory queue drained by one
daemon thread; when the queue is full, or the collector is slow or down, events
are dropped. Emitting never raises and never waits on the network.
"""

from __future__ import annotations

import contextvars
import logging
import os
import queue
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

log = logging.getLogger(__name__)

SESSION_START = "agora.rules.mcpSessionStart"
TOOL_CALL = "agora.rules.mcpToolCall"
SURFACE_ID = "rules-mcp"
INTERNAL_HEADER = "x-agora-internal"
DEFAULT_INTERNAL_UA = r"agora-internal|contentlibrary-rules-smoke|ELB-HealthChecker|kube-probe"

# Per MCP session: the random trace id and whether the session opened as internal.
_session: contextvars.ContextVar[tuple[str, bool] | None] = contextvars.ContextVar(
    "openfisca_mcp_analytics_session", default=None
)


def _header(headers: Mapping[str, str] | None, name: str) -> str:
    if not headers:
        return ""
    try:
        return str(headers.get(name) or headers.get(name.title()) or "")
    except Exception:
        return ""


def headers_from_scope(scope: Mapping[str, Any]) -> dict[str, str]:
    """Lower-cased request headers from an ASGI scope. Never raises."""
    try:
        return {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers") or []}
    except Exception:
        return {}


class LoomSink:
    """Bounded, non-blocking event sink. Construct with ``from_env()``."""

    def __init__(
        self,
        url: str,
        tenant: str,
        secret: str = "",
        source_id: str = "",
        internal_ua_pattern: str = DEFAULT_INTERNAL_UA,
        queue_size: int = 512,
        timeout: float = 2.0,
        transport: Any = None,
    ) -> None:
        self.url = url.rstrip("/") + "/collect" if url else ""
        self.tenant = tenant
        self.source_id = source_id or tenant
        self.secret = secret
        self.timeout = timeout
        self.enabled = bool(self.url and self.tenant)
        try:
            self._internal_ua = re.compile(internal_ua_pattern, re.IGNORECASE) if internal_ua_pattern else None
        except re.error:
            log.warning("analytics: invalid LOOM_INTERNAL_UA_PATTERN; using the default")
            self._internal_ua = re.compile(DEFAULT_INTERNAL_UA, re.IGNORECASE)
        self._queue: queue.Queue = queue.Queue(maxsize=max(1, queue_size))
        self._transport = transport
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.dropped = 0

    @classmethod
    def from_env(cls) -> "LoomSink":
        return cls(
            url=os.getenv("LOOM_INGEST_URL", "").strip(),
            tenant=os.getenv("LOOM_TENANT", "").strip(),
            secret=os.getenv("LOOM_INGEST_SECRET", ""),
            source_id=os.getenv("LOOM_SOURCE_ID", "").strip(),
            internal_ua_pattern=os.getenv("LOOM_INTERNAL_UA_PATTERN", DEFAULT_INTERNAL_UA),
        )

    # ---- classification ------------------------------------------------

    def is_internal(self, headers: Mapping[str, str] | None) -> bool:
        try:
            if _header(headers, INTERNAL_HEADER).strip():
                return True
            ua = _header(headers, "user-agent")
            return bool(ua and self._internal_ua and self._internal_ua.search(ua))
        except Exception:
            return False

    # ---- public event API ----------------------------------------------

    def session_started(self, headers: Mapping[str, str] | None) -> None:
        """Call at the start of an SSE session, before ``server.run``."""
        try:
            internal = self.is_internal(headers)
            _session.set((uuid.uuid4().hex, internal))
            if self.enabled:
                self._emit(SESSION_START, "/mcp/sse", headers, internal, {"outcome": "ok"})
        except Exception:
            log.debug("analytics: session_started failed", exc_info=True)

    def tool_called(
        self,
        tool: str,
        outcome: str,
        latency_ms: float,
        headers: Mapping[str, str] | None,
    ) -> None:
        """Record one tool call. ``tool`` is the tool name only, never arguments."""
        if not self.enabled:
            return
        try:
            session = _session.get()
            internal = (session[1] if session else False) or self.is_internal(headers)
            name = str(tool)[:64] if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", str(tool)) else "unknown"
            data = {
                "outcome": str(outcome)[:64],
                "latency_ms": max(0, int(latency_ms)),
                "tool_calls_names": [name],
                "tool_calls_count": 1,
            }
            if outcome != "ok":
                data["error_class"] = str(outcome)[:64]
            self._emit(TOOL_CALL, f"/mcp/tool/{name}", headers, internal, data)
        except Exception:
            log.debug("analytics: tool_called failed", exc_info=True)

    # ---- delivery ------------------------------------------------------

    def _emit(
        self,
        event_kind: str,
        route: str,
        headers: Mapping[str, str] | None,
        internal: bool,
        data: dict[str, Any],
    ) -> None:
        session = _session.get()
        envelope = {
            "type": "event",
            "payload": {
                "website": self.tenant,
                "url": route,
                "title": "",
                "referrer": "",
                "name": event_kind,
                "data": {
                    "surface_id": SURFACE_ID,
                    "event_kind": event_kind,
                    "trace_id": session[0] if session else "",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **data,
                },
            },
        }
        forwarded_for = _header(headers, "x-forwarded-for").split(",")[0].strip()
        out_headers = {
            "Content-Type": "application/json",
            "X-Loom-Tenant": self.tenant,
            "X-Loom-Source": "internal" if internal else self.source_id,
            "X-Forwarded-For": forwarded_for,
            "User-Agent": _header(headers, "user-agent")[:512],
        }
        if self.secret:
            out_headers["X-Loom-Auth"] = self.secret
        try:
            self._queue.put_nowait((envelope, out_headers))
        except queue.Full:
            self.dropped += 1
            return
        self._ensure_worker()

    def _ensure_worker(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name="loom-sink", daemon=True)
                self._thread.start()

    def _run(self) -> None:
        import httpx

        with httpx.Client(timeout=self.timeout, transport=self._transport, follow_redirects=False) as client:
            while True:
                envelope, headers = self._queue.get()
                try:
                    client.post(self.url, json=envelope, headers=headers)
                except Exception:
                    self.dropped += 1
                finally:
                    self._queue.task_done()

    def flush(self, timeout: float = 5.0) -> bool:
        """Wait for queued events to be attempted. For tests and shutdown only."""
        deadline = time.monotonic() + timeout
        while self._queue.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.01)
        return not self._queue.unfinished_tasks


def classify_result(result: Any) -> str:
    """Outcome class from a tool's formatted result, without reading values.

    Tool handlers return errors as a JSON object ``{"error": {"type": ...}}``.
    Only that top-level ``type`` string is read; anything else is ``ok``.
    """
    try:
        import json

        if result and getattr(result[0], "text", "").startswith('{\n  "error"'):
            error = json.loads(result[0].text).get("error") or {}
            kind = error.get("type")
            if isinstance(kind, str) and re.fullmatch(r"[a-z_]{1,64}", kind):
                return kind
            return "error"
    except Exception:
        return "error"
    return "ok"
