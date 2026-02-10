import json
import uuid

import httpx

from valohai_llm import post_result
from valohai_llm.compat import uuid7


def test_payload_structure(respx_mock, ingest_url, api_key):
    route = respx_mock.post(ingest_url).mock(
        return_value=httpx.Response(200, json={"id": str(uuid7()), "message": "Success"}),
    )

    resp = post_result(
        task="eval-task",
        metrics={"accuracy": 0.95, "recall": 0.88},
        labels={"model": "gpt-4"},
    )
    assert resp

    assert uuid.UUID(resp["id"]).version == 7

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {api_key}"

    payload = json.loads(route.calls.last.request.content)

    assert payload["task"] == "eval-task"
    assert uuid.UUID(payload["run_id"])
    assert payload["metrics"] == {"accuracy": 0.95, "recall": 0.88}
    assert payload["labels"] == {"model": "gpt-4"}
    assert "metadata" in payload
    assert "hostname" in payload["metadata"]
