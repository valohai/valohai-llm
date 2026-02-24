import os
import uuid

from valohai_llm._state import state


def test_run_id_is_stable_uuid7():
    run_id1 = state.get_run_id()
    run_id2 = state.get_run_id()
    assert run_id1 == run_id2
    assert uuid.UUID(run_id1).version == 7


def test_metadata_collected():
    metadata = state.get_metadata()
    assert all(k in metadata for k in ("hostname", "system", "release", "machine", "python_version", "pid"))
    assert metadata["pid"] == os.getpid()
