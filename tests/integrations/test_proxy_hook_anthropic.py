from __future__ import annotations

import pytest

from valohai_llm._state import state
from valohai_llm.integrations._proxy_hook import HEADER_RUN_ID

anthropic = pytest.importorskip("anthropic")


def test_anthropic_sdk(proxy_respx_mock):
    route = proxy_respx_mock.messages_route
    client = anthropic.Anthropic(api_key="sk-fake", base_url=proxy_respx_mock.base_url)
    client.messages.create(model="fake", max_tokens=1, messages=[{"role": "user", "content": "hi"}])
    assert route.calls[0].request.headers.get(HEADER_RUN_ID) == state.get_run_id()
