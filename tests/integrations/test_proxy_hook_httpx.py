from __future__ import annotations

import pytest

pytest.importorskip("httpx")


import httpx

from tests.integrations.consts import OTHER_CHAT_URL, PROXY_CHAT_URL
from valohai_llm import eval_scope
from valohai_llm._state import state
from valohai_llm.integrations._proxy_hook import HEADER_RUN_ID, HEADER_TRACE_ID


@pytest.mark.usefixtures("_install_proxy_hook")
@pytest.mark.parametrize(("url", "expect_header"), [(PROXY_CHAT_URL, True), (OTHER_CHAT_URL, False)])
def test_httpx_run_id_header_injection(respx_mock, url, expect_header):
    route = respx_mock.post(url).mock(return_value=httpx.Response(200, json={"ok": True}))
    with httpx.Client() as client:
        client.post(url, json={})
    sent_request = route.calls[0].request
    if expect_header:
        assert sent_request.headers[HEADER_RUN_ID] == state.get_run_id()
    else:
        assert HEADER_RUN_ID not in sent_request.headers


@pytest.mark.usefixtures("_install_proxy_hook")
def test_httpx_trace_id_header_injection(respx_mock):
    route = respx_mock.post(PROXY_CHAT_URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    with eval_scope() as trace_id:
        with httpx.Client() as client:
            client.post(PROXY_CHAT_URL, json={})
    sent_request = route.calls[0].request
    assert sent_request.headers[HEADER_TRACE_ID] == trace_id
    assert state.get_trace_id() is None
