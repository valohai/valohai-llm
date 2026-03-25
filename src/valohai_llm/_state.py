"""Global state and configuration."""

from __future__ import annotations

import contextlib
import logging
import os
import platform
import sys
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

from valohai_llm._config import API_KEY_ENVVAR, URL_ENVVAR
from valohai_llm.compat import uuid7

if TYPE_CHECKING:
    from httpx._types import HeaderTypes, QueryParamTypes

logger = logging.getLogger(__name__)


@dataclass
class State:
    """Singleton holding runtime state."""

    base_url: str = field(default_factory=lambda: os.environ.get(URL_ENVVAR, "https://llm.valohai.com"))
    api_key: str | None = field(default_factory=lambda: os.environ.get(API_KEY_ENVVAR))
    _run_id: str | None = field(default=None, repr=False)
    _trace_id_stack: list[str] = field(default_factory=list, repr=False)
    _system_metadata: dict[str, Any] | None = field(default=None, repr=False)
    _metadata: dict[str, Any] = field(default_factory=dict, repr=False)
    _httpx_client: httpx.Client | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if os.environ.get("VALOHAI_LLM_REQUIRE_API_KEY") and not self.api_key:  # pragma: no cover
            raise RuntimeError("API key not found in environment variable VALOHAI_LLM_API_KEY, and is required")

    def get_run_id(self) -> str:
        if self._run_id is None:
            self._run_id = str(uuid7())
        return self._run_id

    def get_trace_id(self) -> str | None:
        return self._trace_id_stack[-1] if self._trace_id_stack else None

    def start_eval(self) -> str:
        """
        Start an evaluation scope for cost tracing and return the trace ID.

        Automatically called if using `task.run()` or `with eval_scope()`.
        """
        trace_id = str(uuid7())
        self._trace_id_stack.append(trace_id)
        return trace_id

    def finish_eval(self) -> None:
        """
        Finish the current evaluation scope.

        Automatically called if using `task.run()` or `with eval_scope()`.
        """
        if self._trace_id_stack:
            self._trace_id_stack.pop()

    @contextlib.contextmanager
    def eval_scope(self) -> Generator[str, None, None]:
        """
        Mark a code section where triggered LLM API calls are considered to
        be part of the same evaluation for cost tracing.

        Usage:
        ```
        # inside the scope, trace id is auto-resolved
        with valohai_llm.eval_scope():
            response = client.chat(...)
            post_result(task="my-task", metrics={...})

        # outside the scope, you pass trace id manually
        with valohai_llm.eval_scope() as trace_id:
            response = client.chat(...)
        post_result(task="my-task", trace_id=trace_id, metrics={...})
        ```
        """
        trace_id = self.start_eval()
        try:
            yield trace_id
        finally:
            self.finish_eval()

    def reset(self) -> None:
        """Only for test use."""
        self._httpx_client = None
        self._metadata = {}
        self._run_id = None
        self._trace_id_stack.clear()
        self._system_metadata = None

    def get_metadata(self) -> dict[str, Any]:
        if self._system_metadata is None:
            uname = platform.uname()
            self._system_metadata = {
                "hostname": uname.node,
                "machine": uname.machine,
                "pid": os.getpid(),
                "python_version": sys.version,
                "release": uname.release,
                "system": uname.system,
            }
        return {**self._system_metadata, **self._metadata}

    def update_metadata(self, metadata: dict[str, Any]) -> None:
        self._metadata.update(metadata)

    def get_httpx_client(self) -> httpx.Client:
        if self._httpx_client is None:
            self._httpx_client = httpx.Client(timeout=5)
        return self._httpx_client

    def request(
        self,
        method: str,
        url: str,
        *,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        """Make an HTTP request with retry on transient failures (5xx, transport errors)."""
        client = self.get_httpx_client()
        response: httpx.Response | None = None
        for attempt in range(max_retries):
            is_last = attempt >= max_retries - 1
            try:
                response = client.request(method, url, json=json, params=params, headers=headers)
                if response.status_code < 500 or is_last:
                    break
                delay = 2**attempt
                logger.warning("Server error %s from %s, retrying in %ss...", response.status_code, url, delay)
            except httpx.TransportError:
                if is_last:
                    raise
                delay = 2**attempt
                logger.warning("Request to %s failed, retrying in %ss...", url, delay, exc_info=True)
            time.sleep(delay)
        assert response is not None  # noqa: S101 – unreachable: max_retries >= 1
        return response


state = State()
