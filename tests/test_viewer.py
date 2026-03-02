"""Tests for the viewer module and collect_results."""

import json

from valohai_llm import post_result
from valohai_llm.post import collect_results
from valohai_llm.viewer.__main__ import _load_csv, _load_json, _load_jsonl
from valohai_llm.viewer._app_html import generate_html


def test_collect_results(mock_ingest, api_key):
    with collect_results() as results:
        post_result(task="t1", metrics={"acc": 0.9}, labels={"model": "a"})
        post_result(task="t1", metrics={"acc": 0.8}, labels={"model": "b"})

    assert len(results) == 2
    assert results[0]["metrics"] == {"acc": 0.9}
    assert results[1]["labels"] == {"model": "b"}


def test_collect_results_nested(mock_ingest, api_key):
    with collect_results() as outer:
        post_result(task="t", metrics={"x": 1})
        with collect_results() as inner:
            post_result(task="t", metrics={"x": 2})
        post_result(task="t", metrics={"x": 3})

    assert len(inner) == 1
    assert inner[0]["metrics"] == {"x": 2}
    assert len(outer) == 2
    assert outer[0]["metrics"] == {"x": 1}
    assert outer[1]["metrics"] == {"x": 3}


def test_generate_html_contains_data():
    results = [
        {"metrics": {"accuracy": 0.95}, "labels": {"model": "gpt-4"}},
        {"metrics": {"accuracy": 0.80}, "labels": {"model": "gpt-3.5"}},
    ]
    html = generate_html(results)
    assert "<!DOCTYPE html>" in html
    assert '"accuracy"' in html
    assert "0.95" in html
    assert "gpt-4" in html
    assert "Results Viewer" in html


def test_generate_html_escapes_script_tags():
    results = [{"metrics": {}, "labels": {"x": "</script><img src=x>"}}]
    html = generate_html(results)
    assert "</script><img" not in html
    assert "<\\/script>" in html


def test_load_jsonl(tmp_path):
    p = tmp_path / "data.jsonl"
    p.write_text(
        '{"metrics":{"a":1},"labels":{"m":"x"}}\n'
        '{"metrics":{"a":2},"labels":{"m":"y"}}\n',
    )
    results = _load_jsonl(p)
    assert len(results) == 2
    assert results[0]["metrics"]["a"] == 1


def test_load_json(tmp_path):
    p = tmp_path / "data.json"
    data = [{"metrics": {"a": 1}, "labels": {"m": "x"}}]
    p.write_text(json.dumps(data))
    results = _load_json(p)
    assert len(results) == 1


def test_load_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("model,accuracy,latency\ngpt-4,0.95,150\ngpt-3.5,0.80,89\n")
    results = _load_csv(p)
    assert len(results) == 2
    assert results[0]["labels"] == {"model": "gpt-4"}
    assert results[0]["metrics"] == {"accuracy": 0.95, "latency": 150.0}
