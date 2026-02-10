import secrets

import httpx
import pytest

from valohai_llm import _state
from valohai_llm.compat import uuid7


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state before each test."""
    _state.state._run_id = None
    _state.state._metadata = None
    yield


@pytest.fixture
def base_url() -> str:
    return _state.state.base_url


@pytest.fixture
def ingest_url(base_url) -> str:
    return f"{base_url}/api/ingest/"


@pytest.fixture
def api_key(monkeypatch) -> str:
    monkeypatch.setattr(_state.state, "api_key", secrets.token_urlsafe(32))
    return _state.state.api_key


@pytest.fixture
def mock_ingest(respx_mock, ingest_url):
    """Mock the ingest endpoint to return success."""
    return respx_mock.post(ingest_url).mock(
        return_value=httpx.Response(200, json={"id": str(uuid7()), "created": True}),
    )
