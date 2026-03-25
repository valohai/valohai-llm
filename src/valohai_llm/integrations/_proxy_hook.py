# ruff: noqa: PLC0415 (late imports on purpose here)
"""Monkey-patch HTTP libraries to inject correlation headers for the Valohai LLM proxy."""

from __future__ import annotations

import functools
import logging
import os
from typing import Any
from urllib.parse import urlparse

from valohai_llm._config import PROXY_URL_ENVVAR
from valohai_llm._state import state

logger = logging.getLogger(__name__)

HEADER_RUN_ID = "X-VH-Run-Id"
HEADER_TRACE_ID = "X-VH-Trace-Id"

_proxy_host: tuple[str, int | None] | None = None


def _parse_host(url: str) -> tuple[str, int | None]:
    """Extract (lowercase hostname, port or None) from a URL."""
    parsed = urlparse(url)
    return (parsed.hostname or "").lower(), parsed.port


def _get_proxy_headers(request_host: str, request_port: int | None) -> dict[str, str] | None:
    """Return headers to inject if the request targets the proxy, or None."""
    if _proxy_host is None:
        return None
    if request_host.lower() != _proxy_host[0] or request_port != _proxy_host[1]:
        return None

    headers = {HEADER_RUN_ID: state.get_run_id()}

    trace_id = state.get_trace_id()
    if trace_id is not None:
        headers[HEADER_TRACE_ID] = trace_id

    return headers


# -- httpx -------------------------------------------------------------------


def _patch_httpx() -> None:
    import httpx

    for cls in (httpx.Client, httpx.AsyncClient):
        if getattr(cls, "_valohai_proxy_hooked", False):
            continue

        original_send = cls.send
        cls._valohai_original_send = original_send  # type: ignore[attr-defined]

        @functools.wraps(original_send)
        def _patched_send(self: Any, request: Any, *args: Any, _orig: Any = original_send, **kwargs: Any) -> Any:
            try:
                if headers := _get_proxy_headers(request.url.host or "", request.url.port):
                    request.headers.update(headers)
            except Exception:  # pragma: no cover
                logger.exception("httpx proxy hook failed")
            return _orig(self, request, *args, **kwargs)

        cls.send = _patched_send  # type: ignore[assignment]
        cls._valohai_proxy_hooked = True  # type: ignore[attr-defined]

    logger.debug("httpx proxy header hook installed")


# -- requests -----------------------------------------------------------------


def _patch_requests() -> None:
    import requests

    cls = requests.Session
    if getattr(cls, "_valohai_proxy_hooked", False):
        return

    original_send = cls.send
    cls._valohai_original_send = original_send  # type: ignore[attr-defined]

    @functools.wraps(original_send)
    def _patched_send(self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            if headers := _get_proxy_headers(*_parse_host(request.url)):
                request.headers.update(headers)
        except Exception:  # pragma: no cover
            logger.exception("requests proxy hook failed")
        return original_send(self, request, *args, **kwargs)

    cls.send = _patched_send  # type: ignore[assignment]
    cls._valohai_proxy_hooked = True  # type: ignore[attr-defined]
    logger.debug("requests proxy header hook installed")


# -- aiohttp ------------------------------------------------------------------


def _patch_aiohttp() -> None:
    import aiohttp

    cls = aiohttp.ClientSession
    if getattr(cls, "_valohai_proxy_hooked", False):
        return

    cls._valohai_original_request = cls._request  # type: ignore[attr-defined]

    @functools.wraps(cls._request)
    async def _patched_request(self: Any, method: str, str_or_url: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            if headers := _get_proxy_headers(*_parse_host(str(str_or_url))):
                # Could be a CIMultiDict or plain dict; make a mutable copy
                existing = kwargs.get("headers") or {}
                kwargs["headers"] = {**existing, **headers}
        except Exception:  # pragma: no cover
            logger.exception("aiohttp proxy hook failed")
        return await type(self)._valohai_original_request(self, method, str_or_url, *args, **kwargs)

    cls._request = _patched_request  # type: ignore[assignment]
    cls._valohai_proxy_hooked = True  # type: ignore[attr-defined]
    logger.debug("aiohttp proxy header hook installed")


# -- public entry point -------------------------------------------------------


def install_proxy_hook() -> bool:
    """Install header-injection hooks for HTTP libraries targeting the proxy.

    Returns True if any hooks were installed.
    """
    global _proxy_host  # noqa: PLW0603

    proxy_url = os.environ.get(PROXY_URL_ENVVAR)
    if not proxy_url:
        return False

    parsed = _parse_host(proxy_url)
    if not parsed[0]:
        logger.warning("Could not parse hostname from %s=%s", PROXY_URL_ENVVAR, proxy_url)
        return False

    _proxy_host = parsed

    installed = False
    for patcher in (_patch_httpx, _patch_requests, _patch_aiohttp):
        try:
            patcher()
            installed = True
        except ImportError:
            logger.debug("%s not available, skipping proxy hook", patcher.__name__)
        except Exception:
            logger.debug("Failed to install %s", patcher.__name__, exc_info=True)

    return installed
