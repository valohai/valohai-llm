"""Task runner for fetching and executing evaluation tasks."""

from __future__ import annotations

import itertools
import logging
import tempfile
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlparse
from uuid import UUID

from valohai_llm._state import state
from valohai_llm.parsers import default_items_from
from valohai_llm.post import post_result

if TYPE_CHECKING:
    from numbers import Number

logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    """Information about a dataset attached to a task."""

    id: UUID
    name: str
    download_url: str


@dataclass
class Task:
    """Represents an evaluation task fetched from the API.

    Use `get_current_task()` to fetch the current active task,
    then call `task.run(fn)` to execute your evaluation function.
    """

    id: UUID
    name: str
    parameters: dict[str, list[Any]]
    datasets: list[DatasetInfo]
    _downloaded_paths: dict[str, Path] = field(default_factory=dict, repr=False)
    _temp_dir: tempfile.TemporaryDirectory | None = field(default=None, repr=False)

    def iter_params(self) -> Iterator[dict[str, Any]]:
        """Yield cartesian product of parameter values.

        Yields:
            Dicts mapping parameter names to specific values.
        """
        if not self.parameters:
            yield {}
            return
        keys = list(self.parameters.keys())
        for values in itertools.product(*self.parameters.values()):
            yield dict(zip(keys, values))

    def download_datasets(self) -> dict[str, Path]:
        """Download all datasets to a temp directory.

        Returns:
            Dict mapping dataset name to local file path.
        """
        if self._downloaded_paths:
            return self._downloaded_paths

        if not self.datasets:
            return {}

        self._temp_dir = tempfile.TemporaryDirectory(prefix="valohai_llm_datasets_")
        temp_path = Path(self._temp_dir.name)
        client = state.get_httpx_client()

        for ds in self.datasets:
            # Extract filename from URL path to preserve the correct extension
            url_path = urlparse(ds.download_url).path
            filename = PurePosixPath(url_path).name
            local_path = temp_path / filename
            logger.info("Downloading dataset %s to %s", ds.name, local_path)
            with client.stream("GET", ds.download_url) as response:
                response.raise_for_status()
                with local_path.open("wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            self._downloaded_paths[ds.name] = local_path

        return self._downloaded_paths

    def run(
        self,
        fn: Callable[..., dict[str, Number]],
        items_from: Callable[[Path], Iterable[dict]] | None = None,
        item_labels: list[str] | None = None,
    ) -> list[dict]:
        """Run the evaluation function over all (params, item) combinations.

        For each parameter combination, for each dataset, for each item in the dataset,
        calls `fn(params=params, item=item)` and posts the result with appropriate labels.

        Args:
            fn: Evaluation function with signature `def fn(*, params: dict, item: dict) -> dict[str, Number]`.
                Must accept keyword-only arguments and return a dict of metric names to numeric values.
            items_from: Optional custom parser function. If not provided, uses `default_items_from`
                which detects format by file extension.
            item_labels: Optional list of item field names to include as labels.
                For example, `item_labels=["category"]` will add each item's
                "category" field as a label in the posted result.

        Returns:
            List of all posted result responses.

        Example:
            >>> task = get_current_task()
            >>> def evaluate(*, params, item):
            ...     result = call_llm(item["prompt"], model=params["model"])
            ...     return {"correct": 1 if result == item["expected"] else 0}
            >>> task.run(evaluate, item_labels=["category", "difficulty"])
        """
        if items_from is None:
            items_from = default_items_from

        try:
            dataset_paths = self.download_datasets()

            # Parse all datasets upfront to fail fast before invoking user code
            parsed_datasets: dict[str, list[dict]] = {}
            for ds_name, ds_path in dataset_paths.items():
                logger.debug("Parsing dataset %s from %s", ds_name, ds_path)
                parsed_datasets[ds_name] = list(items_from(ds_path))

            results = []
            for params in self.iter_params():
                if parsed_datasets:
                    for ds_name, items in parsed_datasets.items():
                        for idx, item in enumerate(items):
                            item_id = item.get("id", idx)
                            result = self._run_single(fn, params, item, ds_name, item_id, item_labels)
                            if result is not None:
                                results.append(result)
                else:
                    # No datasets - run with empty item
                    result = self._run_single(fn, params, {}, None, None, item_labels)
                    if result is not None:
                        results.append(result)

            return results
        finally:
            self.cleanup()

    def _run_single(
        self,
        fn: Callable[..., dict[str, Number]],
        params: dict[str, Any],
        item: dict,
        dataset_name: str | None,
        item_id: Any | None,
        item_labels: list[str] | None = None,
    ) -> dict | None:
        """Execute a single evaluation and post the result."""
        logger.debug(
            "Invoking %s(params=%r, item=%r) [dataset=%s, item_id=%s]",
            fn.__name__,
            params,
            item,
            dataset_name,
            item_id,
        )
        with state.eval_scope():
            try:
                t0 = time.perf_counter()
                metrics = fn(params=params, item=item)
                duration = time.perf_counter() - t0
            except Exception:
                logger.exception(
                    "Evaluation failed for params=%r, item=%r (dataset=%s)",
                    params,
                    item,
                    dataset_name,
                )
                return None

            if not isinstance(metrics, dict):
                logger.error(
                    "Evaluation function returned %s instead of dict for params=%r (dataset=%s)",
                    type(metrics).__name__,
                    params,
                    dataset_name,
                )
                return None

            # Build labels from params
            labels = {str(k): str(v) for k, v in params.items()}
            if dataset_name is not None:
                labels["dataset"] = dataset_name
            if item_id is not None:
                labels["item_id"] = str(item_id)

            # Add item labels
            if item_labels:
                for key in item_labels:
                    if key in item:
                        labels[key] = str(item[key])

            return post_result(
                task=str(self.id),
                metrics=metrics,
                labels=labels,
                metadata={"duration_seconds": duration},
            )

    def cleanup(self) -> None:
        """Clean up downloaded datasets."""
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None
            self._downloaded_paths.clear()

    def __enter__(self) -> Task:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()


def get_current_task() -> Task:
    """Fetch the current active task from the API.

    Returns:
        Task object containing task details, parameters, and dataset info.

    Raises:
        RuntimeError: If no API key is configured.
        httpx.HTTPStatusError: If the request fails (e.g., 404 if no active task).

    Example:
        >>> task = get_current_task()
        >>> print(task.name, task.parameters)
        'my-eval' {'model': ['gpt-4', 'gpt-3.5'], 'temperature': [0.0, 0.5]}
    """
    if not state.api_key:
        raise RuntimeError("API key not found in environment variable VALOHAI_LLM_API_KEY")

    url = f"{state.base_url.rstrip('/')}/api/current-task/"
    headers = {"Authorization": f"Bearer {state.api_key}"}

    response = state.request("GET", url, headers=headers)
    response.raise_for_status()
    data = response.json()

    datasets = [
        DatasetInfo(
            id=UUID(ds["id"]),
            name=ds["name"],
            download_url=ds["download_url"],
        )
        for ds in data.get("datasets", [])
    ]

    return Task(
        id=UUID(data["id"]),
        name=data["name"],
        parameters=data.get("parameters", {}),
        datasets=datasets,
    )
