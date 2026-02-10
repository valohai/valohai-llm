import pytest

from valohai_llm.parsers import DatasetParseError, default_items_from


def test_jsonl(tmp_path):
    path = tmp_path / "data.jsonl"
    path.write_text('{"a": 1}\n\n{"a": 2}\n')  # includes blank line
    assert list(default_items_from(path)) == [{"a": 1}, {"a": 2}]


def test_csv(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("name,value\nalice,10\nbob,20\n")
    assert list(default_items_from(path)) == [{"name": "alice", "value": "10"}, {"name": "bob", "value": "20"}]


def test_tsv(tmp_path):
    path = tmp_path / "data.tsv"
    path.write_text("name\tvalue\nalice\t10\n")
    assert list(default_items_from(path)) == [{"name": "alice", "value": "10"}]


def test_json_array(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('[{"id": 1}, {"id": 2}]')
    assert list(default_items_from(path)) == [{"id": 1}, {"id": 2}]


def test_json_not_array_raises(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"not": "array"}')
    with pytest.raises(DatasetParseError, match="Expected JSON array"):
        list(default_items_from(path))


def test_unknown_extension_raises(tmp_path):
    path = tmp_path / "data.xyz"
    path.write_text("some data")
    with pytest.raises(DatasetParseError, match="Unknown dataset format"):
        list(default_items_from(path))
