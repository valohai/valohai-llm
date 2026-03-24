from __future__ import annotations

from unittest.mock import MagicMock, patch

import aiohttp
import httpx
import pytest
import requests

import valohai_llm._proxy_hook as proxy_hook_mod
from valohai_llm._proxy_hook import HEADER_RUN_ID, _parse_host, install_proxy_hook
from valohai_llm._state import state

PROXY_URL = "https://llm-proxy.example.com"
PROXY_CHAT_URL = "https://llm-proxy.example.com/v1/chat/completions"
OTHER_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def _unhook_cls(cls, method_name, orig_attr="_valohai_original_send"):
    """Restore original method and remove hook markers from *cls*."""
    if (original := getattr(cls, orig_attr, None)) is not None:
        setattr(cls, method_name, original)
        delattr(cls, orig_attr)
    for attr in ("_valohai_proxy_hooked",):
        if hasattr(cls, attr):
            delattr(cls, attr)


@pytest.fixture(autouse=True)
def _clean_hooks():
    """Remove hook flags and restore originals so each test starts fresh."""
    yield
    proxy_hook_mod._proxy_host = None
    for cls in (httpx.Client, httpx.AsyncClient):
        _unhook_cls(cls, "send")
    _unhook_cls(requests.Session, "send")
    try:
        import aiohttp  # noqa: PLC0415

        _unhook_cls(aiohttp.ClientSession, "_request", "_valohai_original_request")
    except ImportError:
        pass


@pytest.fixture
def _install(monkeypatch):
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", PROXY_URL)
    install_proxy_hook()


def test_parse_host():
    assert _parse_host("https://proxy.example.com:8443/v1") == ("proxy.example.com", 8443)
    assert _parse_host("https://proxy.example.com/v1") == ("proxy.example.com", None)
    assert _parse_host("https://Proxy.EXAMPLE.com") == ("proxy.example.com", None)


def test_no_env_var_is_noop(monkeypatch):
    monkeypatch.delenv("VALOHAI_LLM_PROXY_URL", raising=False)
    assert install_proxy_hook() is False


def test_empty_env_var_is_noop(monkeypatch):
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", "")
    assert install_proxy_hook() is False


def test_installs_with_valid_url(monkeypatch):
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", PROXY_URL)
    assert install_proxy_hook() is True


def test_idempotent(monkeypatch):
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", PROXY_URL)
    assert install_proxy_hook() is True
    assert install_proxy_hook() is True  # should not raise


@pytest.mark.usefixtures("_install")
@pytest.mark.parametrize(("url", "expect_header"), [(PROXY_CHAT_URL, True), (OTHER_CHAT_URL, False)])
def test_httpx_header_injection(respx_mock, url, expect_header):
    route = respx_mock.post(url).mock(return_value=httpx.Response(200, json={"ok": True}))
    with httpx.Client() as client:
        client.post(url, json={})
    sent_request = route.calls[0].request
    if expect_header:
        assert sent_request.headers[HEADER_RUN_ID] == state.get_run_id()
    else:
        assert HEADER_RUN_ID not in sent_request.headers


@pytest.mark.usefixtures("_install")
@pytest.mark.parametrize(("url", "expect_header"), [(PROXY_CHAT_URL, True), (OTHER_CHAT_URL, False)])
def test_requests_header_injection(url, expect_header):
    captured = {}

    def fake_adapter_send(self, request, *args, **kwargs):
        captured["headers"] = dict(request.headers)
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b"{}"
        return resp

    with patch.object(requests.adapters.HTTPAdapter, "send", fake_adapter_send):
        requests.Session().post(url)

    if expect_header:
        assert captured["headers"][HEADER_RUN_ID] == state.get_run_id()
    else:
        assert HEADER_RUN_ID not in captured["headers"]


@pytest.mark.usefixtures("_install")
@pytest.mark.anyio
@pytest.mark.parametrize(("url", "expect_header"), [(PROXY_CHAT_URL, True), (OTHER_CHAT_URL, False)])
async def test_aiohttp_header_injection(url, expect_header):

    captured = {}

    async def capturing_request(self, method, url, *args, **kwargs):
        captured.update(kwargs.get("headers", {}))
        resp = MagicMock()
        resp.release = MagicMock(return_value=None)
        return resp

    with patch.object(aiohttp.ClientSession, "_valohai_original_request", capturing_request):
        async with aiohttp.ClientSession() as session:
            await session._request("POST", url)

    if expect_header:
        assert captured[HEADER_RUN_ID] == state.get_run_id()
    else:
        assert HEADER_RUN_ID not in captured
