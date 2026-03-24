from __future__ import annotations

import pytest

from valohai_llm._state import state
from valohai_llm.integrations._proxy_hook import HEADER_RUN_ID

openai = pytest.importorskip("openai")


def test_openai_sdk(proxy_respx_mock):
    route = proxy_respx_mock.completions_route
    client = openai.OpenAI(api_key="sk-fake", base_url=f"{proxy_respx_mock.base_url}/v1")
    client.chat.completions.create(model="fake", messages=[{"role": "user", "content": "hi"}])
    assert route.calls[0].request.headers.get(HEADER_RUN_ID) == state.get_run_id()
