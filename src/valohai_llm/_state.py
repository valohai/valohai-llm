"""Global state and configuration."""

from __future__ import annotations

import logging
import os
import platform
import sys
import time
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
    _metadata: dict[str, Any] | None = field(default=None, repr=False)
    _httpx_client: httpx.Client | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if os.environ.get("VALOHAI_LLM_REQUIRE_API_KEY") and not self.api_key:  # pragma: no cover
            raise RuntimeError("API key not found in environment variable VALOHAI_LLM_API_KEY, and is required")

    def get_run_id(self) -> str:
        if self._run_id is None:
            self._run_id = str(uuid7())
        return self._run_id

    def get_metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            uname = platform.uname()
            self._metadata = {
                "hostname": uname.node,
                "machine": uname.machine,
                "pid": os.getpid(),
                "python_version": sys.version,
                "release": uname.release,
                "system": uname.system,
            }
        return self._metadata

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
        assert response is not None  # unreachable: max_retries >= 1
        return response


state = State()
