from __future__ import annotations

from unittest.mock import patch

import pytest

pytest.importorskip("requests")

import requests

from tests.integrations.consts import OTHER_CHAT_URL, PROXY_CHAT_URL
from valohai_llm._state import state
from valohai_llm.integrations._proxy_hook import HEADER_RUN_ID


@pytest.mark.usefixtures("_install_proxy_hook")
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
