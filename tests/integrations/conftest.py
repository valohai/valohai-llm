from __future__ import annotations

import dataclasses

import httpx
import pytest
import respx

import valohai_llm.integrations._proxy_hook as proxy_hook_mod
from valohai_llm.integrations._proxy_hook import install_proxy_hook

from .consts import FAKE_ANTHROPIC_RESPONSE, FAKE_COMPLETIONS_RESPONSE, PROXY_BASE


def _unhook_cls(cls, method_name, orig_attr="_valohai_original_send"):
    """Restore original method and remove hook markers from *cls*."""
    if (original := getattr(cls, orig_attr, None)) is not None:
        setattr(cls, method_name, original)
        delattr(cls, orig_attr)
    if hasattr(cls, "_valohai_proxy_hooked"):
        delattr(cls, "_valohai_proxy_hooked")


@pytest.fixture(autouse=True)
def _clean_proxy_hooks():
    """Remove hook flags and restore originals so each test starts fresh."""
    yield
    proxy_hook_mod._proxy_host = None
    for cls in (httpx.Client, httpx.AsyncClient):
        _unhook_cls(cls, "send")

    try:
        import requests

        _unhook_cls(requests.Session, "send")
    except ImportError:
        pass

    try:
        import aiohttp

        _unhook_cls(aiohttp.ClientSession, "_request", "_valohai_original_request")
    except ImportError:
        pass


@pytest.fixture
def _install_proxy_hook(monkeypatch):
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", PROXY_BASE)
    install_proxy_hook()


@dataclasses.dataclass(frozen=True)
class ProxyRespxMockResult:
    base_url: str
    messages_route: respx.Route
    completions_route: respx.Route


@pytest.fixture
def proxy_respx_mock(
    _install_proxy_hook,
    mock_ingest,
    respx_mock,
) -> ProxyRespxMockResult:
    messages_route = respx_mock.post(f"{PROXY_BASE}/v1/messages").mock(
        return_value=httpx.Response(200, json=FAKE_ANTHROPIC_RESPONSE),
    )
    completions_route = respx_mock.post(f"{PROXY_BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETIONS_RESPONSE),
    )
    return ProxyRespxMockResult(
        base_url=PROXY_BASE,
        messages_route=messages_route,
        completions_route=completions_route,
    )
