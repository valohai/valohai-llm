from __future__ import annotations

from valohai_llm.integrations._proxy_hook import _parse_host, install_proxy_hook

from .consts import PROXY_BASE


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
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", PROXY_BASE)
    assert install_proxy_hook() is True


def test_idempotent(monkeypatch):
    monkeypatch.setenv("VALOHAI_LLM_PROXY_URL", PROXY_BASE)
    assert install_proxy_hook() is True
    assert install_proxy_hook() is True  # should not raise
