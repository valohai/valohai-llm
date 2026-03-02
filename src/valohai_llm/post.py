"""Result posting functionality."""

from __future__ import annotations

import warnings
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

from valohai_llm._state import state
from valohai_llm.compat import uuid7

_active_collector: list[dict[str, Any]] | None = None


@contextmanager
def collect_results() -> Generator[list[dict[str, Any]], None, None]:
    """Context manager that captures result payloads as they are posted.

    Yields a list that accumulates the raw payload dicts sent to the server.
    This is useful for feeding results to the viewer::

        with valohai_llm.collect_results() as results:
            task.run(my_fn)
        valohai_llm.viewer.serve(results=results)
    """
    global _active_collector  # noqa: PLW0603
    results: list[dict[str, Any]] = []
    prev = _active_collector
    _active_collector = results
    try:
        yield results
    finally:
        _active_collector = prev


def post_result(
    *,
    task: str | UUID,
    metrics: dict[str, Any] | None = None,
    labels: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Post an evaluation result to the Valohai LLM server.

    Args:
        task: The task name/identifier (required)
        metrics: Numeric metrics that can be aggregated (e.g., {"accuracy": 0.85, "latency_ms": 150})
        labels: String dimensions for grouping (e.g., {"model": "gpt-4", "dataset": "mmlu"})
        metadata: Per-result metadata merged with global metadata (e.g., {"duration_seconds": 1.5})

    Returns:
        Response from the server including the result ID and whether it was newly created.

    Example:
        >>> import valohai_llm
        >>> valohai_llm.post_result(
        ...     task="summarization-eval",
        ...     metrics={"accuracy": 0.85, "recall": 0.92},
        ...     labels={"model": "gpt-4", "dataset": "cnn-dailymail"},
        ... )
        {'id': '0190a1b2-...', 'created': True}
    """
    if not state.api_key:
        warnings.warn("API key not found in environment variable VALOHAI_LLM_API_KEY.", UserWarning, stacklevel=2)
        return None

    merged_metadata = {**state.get_metadata(), **(metadata or {})}

    payload = {
        "id": str(uuid7()),
        "run_id": state.get_run_id(),
        "task": task,
        "metrics": metrics or {},
        "labels": labels or {},
        "metadata": merged_metadata,
    }

    if _active_collector is not None:
        _active_collector.append(payload)

    url = f"{state.base_url.rstrip('/')}/api/ingest/"
    headers = {
        "Authorization": f"Bearer {state.api_key}",
        "Content-Type": "application/json",
    }

    response = state.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()
