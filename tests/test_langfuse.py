from __future__ import annotations

import pytest

pytest.importorskip("langfuse", exc_type=Exception)  # The exception will be a Pydantic error

import sys
from unittest.mock import MagicMock

from langfuse import Langfuse, observe
from langfuse._client import span_processor as span_processor_module
from langfuse._client.resource_manager import LangfuseResourceManager
from langfuse._utils.prompt_cache import PromptCacheRefreshConsumer
from langfuse.version import __version__ as langfuse_version

from valohai_llm._langfuse import TRACE_URL_METADATA_KEY, get_existing_client, install_langfuse_hook
from valohai_llm._state import state

if sys.version_info >= (3, 14) and langfuse_version.startswith("3"):
    pytest.skip("Langfuse 3.x is not compatible with Python 3.14", allow_module_level=True)


original_initialize_instance = LangfuseResourceManager._initialize_instance

LANGFUSE_BASE_URL = "http://localhost:55555"
PROJECT_ID = "fake-project-id"


@pytest.fixture(autouse=True)
def _langfuse_patch(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test-fake")
    monkeypatch.setenv("LANGFUSE_MEDIA_UPLOAD_ENABLED", "false")  # Speeds up teardown
    monkeypatch.setattr(PromptCacheRefreshConsumer, "run", lambda self: None)  # Disable prompt cache thread
    monkeypatch.setattr(span_processor_module, "OTLPSpanExporter", MagicMock())  # No actual span exporting during tests
    monkeypatch.setattr(Langfuse, "_get_project_id", lambda self: PROJECT_ID)  # Avoid API traffic
    yield
    for inst in LangfuseResourceManager._instances.values():
        inst.shutdown()
    LangfuseResourceManager._instances.clear()
    LangfuseResourceManager._initialize_instance = original_initialize_instance
    LangfuseResourceManager._valohai_llm_hooked = False


def create_langfuse(public_key: str | None = None) -> Langfuse:
    return Langfuse(
        public_key=public_key,
        secret_key="sk-test-fake",
        base_url=LANGFUSE_BASE_URL,
        tracing_enabled=True,
        flush_interval=0.1,  # Will make `_reset_state()` faster
    )


def check_trace_url() -> bool:
    try:
        trace_url = state.get_metadata()[TRACE_URL_METADATA_KEY]
    except KeyError as exc:
        raise AssertionError("Missing TRACE_URL_METADATA_KEY") from exc
    before, prefix, after = trace_url.partition(f"{LANGFUSE_BASE_URL}/project/{PROJECT_ID}/traces/")
    assert not before, "Trash before trace URL"
    assert prefix, "Did not find trace URL"
    assert after.isalnum(), "Trace URL didn't have hex suffix"
    return True


def test_get_existing_client_no_instances():
    assert get_existing_client() is None


def test_get_existing_client_single_instance():
    create_langfuse("pk-test-single")
    assert isinstance(get_existing_client(), Langfuse)


def test_get_existing_client_multiple_instances_returns_none():
    create_langfuse("pk-test-multi-1")
    create_langfuse("pk-test-multi-2")
    assert get_existing_client() is None


def test_get_existing_client_by_key():
    create_langfuse("pk-test-lookup")
    assert isinstance(get_existing_client(public_key="pk-test-lookup"), Langfuse)


def test_get_existing_client_missing_key():
    create_langfuse("pk-test-exists")
    assert get_existing_client(public_key="pk-no-such") is None


def test_span_processor_uses_url_within_observed():
    assert install_langfuse_hook()
    create_langfuse()

    @observe
    def test_func():
        check_trace_url()
        return 42

    assert test_func()


def test_span_processor_stashes_url_outside_observed():
    assert install_langfuse_hook()
    create_langfuse()

    @observe
    def test_func():
        return 9

    assert test_func()
    check_trace_url()


def test_span_processor_no_stash_if_not_observed():
    assert install_langfuse_hook()
    create_langfuse()

    def test_func():
        return 9

    assert test_func()
    with pytest.raises(AssertionError):
        check_trace_url()
