# ruff: noqa: PLC0415 (late imports on purpose here)
from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any

from valohai_llm._state import state

TRACE_URL_METADATA_KEY = "langfuse_last_trace_url"

try:
    from opentelemetry.sdk.trace import SpanProcessor
except ImportError:
    SpanProcessor = object

if TYPE_CHECKING:
    from langfuse._client.client import Langfuse
    from langfuse._client.resource_manager import LangfuseResourceManager
    from opentelemetry.context import Context
    from opentelemetry.sdk.trace import Span


logger = logging.getLogger(__name__)


def get_existing_client(*, public_key: str | None = None) -> Langfuse | None:
    """Return an existing ``Langfuse`` client, or ``None``.

    Mirrors the lookup logic of ``langfuse.get_client()`` but
    **never** creates a new client or resource manager.
    """
    from langfuse._client.get_client import _create_client_from_instance, _current_public_key
    from langfuse._client.resource_manager import LangfuseResourceManager

    active_instances = LangfuseResourceManager._instances
    if not public_key:
        public_key = _current_public_key.get(None)

    if public_key:
        instance = active_instances.get(public_key)
        return _create_client_from_instance(instance, public_key) if instance else None

    if len(active_instances) == 1:
        only_key = next(iter(active_instances))
        return _create_client_from_instance(active_instances[only_key], only_key)

    return None


@functools.lru_cache(maxsize=64)
def trace_id_to_langfuse_url(trace_id: int) -> str | None:
    if client := get_existing_client():
        return client.get_trace_url(trace_id=format(trace_id, "032x"))
    return None


class StashTraceURLSpanProcessor(SpanProcessor):  # NB: `SpanProcessor` could be `object`
    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        try:
            if url := trace_id_to_langfuse_url(span.context.trace_id):
                state.update_metadata({TRACE_URL_METADATA_KEY: url})
        except Exception:
            logger.debug("Failed to capture Langfuse trace URL", exc_info=True)


def add_processor_to_instance(instance: LangfuseResourceManager) -> None:
    tp = getattr(instance, "tracer_provider", None)
    if tp is None:
        return
    if getattr(tp, "_valohai_llm_hooked", False):
        return
    tp.add_span_processor(StashTraceURLSpanProcessor())
    tp._valohai_llm_hooked = True
    logger.debug("Langfuse trace-URL span processor added to %s", instance)


def install_langfuse_hook() -> bool:
    """
    Hook Langfuse to register our span processor to capture Langfuse trace URLs.

    Returns true if changes were made.
    """
    try:
        from langfuse._client.resource_manager import LangfuseResourceManager
    except ImportError:
        logger.debug("langfuse is not installed; skipping hook installation")
        return False

    if getattr(LangfuseResourceManager, "_valohai_llm_hooked", False):
        return False

    try:
        original_initialize_instance = LangfuseResourceManager._initialize_instance

        @functools.wraps(original_initialize_instance)
        def _patched_initialize_instance(self: LangfuseResourceManager, **kwargs: Any) -> None:
            original_initialize_instance(self, **kwargs)
            add_processor_to_instance(self)

        LangfuseResourceManager._initialize_instance = _patched_initialize_instance  # type: ignore[assignment]

        # Retrofit any instances that were already initialised.
        with LangfuseResourceManager._lock:
            for instance in LangfuseResourceManager._instances.values():
                add_processor_to_instance(instance)

        logger.debug("Langfuse trace-URL hook installed")
        LangfuseResourceManager._valohai_llm_hooked = True
        return True
    except Exception:
        logger.debug("Could not hook Langfuse", exc_info=True)
    return False
