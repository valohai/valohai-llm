"""Result posting functionality."""

from __future__ import annotations

import warnings
from typing import Any
from uuid import UUID

from valohai_llm._state import state
from valohai_llm.compat import uuid7


def post_result(
    *,
    task: str | UUID,
    trace_id: str | UUID | None = None,
    metrics: dict[str, Any] | None = None,
    labels: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Post an evaluation result to the Valohai LLM server.

    Args:
        task: The task name/identifier (required)
        trace_id: The tracing ID for cost attribution (optional, potentially auto-resolved if not provided)
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

    payload: dict[str, Any] = {
        "id": str(uuid7()),
        "run_id": state.get_run_id(),
        "task": str(task),
        "metrics": metrics or {},
        "labels": labels or {},
        "metadata": merged_metadata,
    }

    if trace_id == "":
        raise ValueError("trace_id cannot be an empty string")

    resolved_trace_id = trace_id if trace_id is not None else state.get_trace_id()
    if resolved_trace_id is not None:
        payload["trace_id"] = str(resolved_trace_id)

    url = f"{state.base_url.rstrip('/')}/api/ingest/"
    headers = {
        "Authorization": f"Bearer {state.api_key}",
        "Content-Type": "application/json",
    }

    response = state.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()
