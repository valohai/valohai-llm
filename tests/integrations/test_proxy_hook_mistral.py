from __future__ import annotations

import pytest

from valohai_llm._state import state
from valohai_llm.integrations._proxy_hook import HEADER_RUN_ID

pytest.importorskip("mistralai")


def test_mistral_sdk(proxy_respx_mock):
    from mistralai.client import Mistral

    client = Mistral(api_key="fake-key", server_url=proxy_respx_mock.base_url)
    client.chat.complete(model="fake", messages=[{"role": "user", "content": "hi"}])
    assert proxy_respx_mock.completions_route.calls[0].request.headers.get(HEADER_RUN_ID) == state.get_run_id()
