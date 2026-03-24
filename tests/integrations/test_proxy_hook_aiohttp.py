from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("aiohttp")

import aiohttp

from tests.integrations.consts import OTHER_CHAT_URL, PROXY_CHAT_URL
from valohai_llm._state import state
from valohai_llm.integrations._proxy_hook import HEADER_RUN_ID


@pytest.mark.usefixtures("_install_proxy_hook")
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
