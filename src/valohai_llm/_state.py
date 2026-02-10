"""Global state and configuration."""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field
from typing import Any

import httpx

from valohai_llm.compat import uuid7


@dataclass
class State:
    """Singleton holding runtime state."""

    base_url: str = field(default_factory=lambda: os.environ.get("VALOHAI_LLM_URL", "https://llm.valohai.com"))
    api_key: str | None = field(default_factory=lambda: os.environ.get("VALOHAI_LLM_API_KEY"))
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


state = State()
