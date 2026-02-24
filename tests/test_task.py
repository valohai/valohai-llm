import json

import httpx
import pytest

from valohai_llm.compat import uuid7
from valohai_llm.parsers import DatasetParseError
from valohai_llm.task import DatasetInfo, Task, get_current_task


def test_run_no_datasets(mock_ingest, api_key):
    task = Task(id=uuid7(), name="test", parameters={"model": ["gpt-4"]}, datasets=[])
    results = task.run(lambda *, params, item: {"score": 1.0})
    assert len(results) == 1


def test_run_with_datasets(respx_mock, mock_ingest, api_key):
    respx_mock.get("https://example.com/dataset.jsonl").mock(
        return_value=httpx.Response(200, content=b'{"prompt": "hello"}\n{"prompt": "world"}\n'),
    )

    task = Task(
        id=uuid7(),
        name="test",
        parameters={"model": ["gpt-4", "gpt-3.5"]},
        datasets=[DatasetInfo(id=uuid7(), name="data.jsonl", download_url="https://example.com/dataset.jsonl")],
    )

    call_log = []
    results = task.run(lambda *, params, item: (call_log.append((params, item)), {"score": 1.0})[1])

    assert len(results) == 4  # 2 models * 2 items
    assert ({"model": "gpt-4"}, {"prompt": "hello"}) in call_log
    assert ({"model": "gpt-3.5"}, {"prompt": "world"}) in call_log


def test_run_continues_on_error(mock_ingest, api_key):
    task = Task(id=uuid7(), name="test", parameters={"n": [1, 2, 3]}, datasets=[])

    def fn(*, params, item):
        if params["n"] == 2:
            raise ValueError("Intentional error")
        return {"score": params["n"]}

    results = task.run(fn)
    assert len(results) == 2  # 1 and 3 succeed, 2 fails


def test_run_fails_fast_on_parse_error(respx_mock, api_key):
    respx_mock.get("https://example.com/bad.jsonl").mock(
        return_value=httpx.Response(200, content=b"not valid json\n"),
    )

    task = Task(
        id=uuid7(),
        name="test",
        parameters={},
        datasets=[DatasetInfo(id=uuid7(), name="bad.jsonl", download_url="https://example.com/bad.jsonl")],
    )

    with pytest.raises(DatasetParseError):
        task.run(lambda *, params, item: {"score": 1})


def test_run_with_item_labels(respx_mock, mock_ingest, api_key):
    """Test that item_labels extracts fields from items as labels."""
    respx_mock.get("https://example.com/dataset.jsonl").mock(
        return_value=httpx.Response(
            200,
            content=b'{"id": "q1", "question": "What is 2+2?", "category": "math", "difficulty": "easy"}\n',
        ),
    )

    task = Task(
        id=uuid7(),
        name="test",
        parameters={"model": ["gpt-4"]},
        datasets=[DatasetInfo(id=uuid7(), name="data.jsonl", download_url="https://example.com/dataset.jsonl")],
    )

    results = task.run(lambda *, params, item: {"score": 1.0}, item_labels=["category", "difficulty"])

    assert len(results) == 1

    # Verify the posted request includes item labels
    request = mock_ingest.calls.last.request

    body = json.loads(request.content)
    assert body["labels"]["category"] == "math"
    assert body["labels"]["difficulty"] == "easy"
    assert body["labels"]["model"] == "gpt-4"


def test_run_with_item_labels_missing_key(respx_mock, mock_ingest, api_key):
    """Test that missing item_labels keys are silently skipped."""
    respx_mock.get("https://example.com/dataset.jsonl").mock(
        return_value=httpx.Response(
            200,
            content=b'{"id": "q1", "question": "What is 2+2?"}\n',
        ),
    )

    task = Task(
        id=uuid7(),
        name="test",
        parameters={},
        datasets=[DatasetInfo(id=uuid7(), name="data.jsonl", download_url="https://example.com/dataset.jsonl")],
    )

    # Request "category" label but it doesn't exist in item
    results = task.run(lambda *, params, item: {"score": 1.0}, item_labels=["category"])

    assert len(results) == 1

    # Verify "category" is NOT in labels since it's missing from the item
    request = mock_ingest.calls.last.request

    body = json.loads(request.content)
    assert "category" not in body["labels"]


def test_get_current_task(respx_mock, base_url, api_key):
    task_id = str(uuid7())

    respx_mock.get(f"{base_url}/api/current-task/").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": task_id,
                "name": "my-eval",
                "parameters": {"model": ["gpt-4"]},
                "datasets": [
                    {"id": str(uuid7()), "name": "test.jsonl", "download_url": "https://example.com/test.jsonl"},
                ],
            },
        ),
    )

    task = get_current_task()
    assert str(task.id) == task_id
    assert task.name == "my-eval"
    assert len(task.datasets) == 1
