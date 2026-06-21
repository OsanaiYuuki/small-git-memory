import json

import pytest

from core.git_memory import GitMemory
from core.storage import load_memory, memory_to_data, migrate_data, save_memory, validate_data

def test_memory_to_data_has_version():
    m = GitMemory()
    data = memory_to_data(m)
    assert data["version"] == 1

def test_memory_to_data_uses_string_commit_keys():
    m = GitMemory()
    data = memory_to_data(m)
    assert "0" in data["commits"]
    assert 0 not in data["commits"]

def test_validate_memory_to_data():
    m = GitMemory()
    data = memory_to_data(m)
    assert validate_data(data)

def test_migrate_v0_messages_to_cached_context():
    old_data = {
        "context": [],
        "base": [],
        "head": 0,
        "commits": {
            "0": {
                "id": 0,
                "parent": None,
                "patch": [],
                "created_at": "time",
            }
        },
        "snapshots": {
            "__root__": {
                "messages": [],
                "created_at": "time",
                "note": "",
                "node_id": 0,
            }
        },
        "next_id": 1,
    }

    migrated = migrate_data(old_data)

    assert migrated["version"] == 1
    assert "cached_context" in migrated["snapshots"]["__root__"]
    assert "messages" not in migrated["snapshots"]["__root__"]


def test_save_memory_writes_valid_json_without_tmp_file_and_can_load(monkeypatch, tmp_path):
    data_file = tmp_path / "gitmemory.json"
    monkeypatch.setattr("core.storage.DATA_FILE", str(data_file))

    saved = GitMemory()
    saved.add_message("user", "remember this")
    saved.snapshot("important")

    save_memory(saved)

    assert data_file.exists()
    saved_data = json.loads(data_file.read_text(encoding="utf-8"))
    assert validate_data(saved_data)
    assert list(tmp_path.glob("*.tmp")) == []

    loaded = GitMemory()
    load_memory(loaded)

    assert memory_to_data(loaded) == memory_to_data(saved)


def test_failed_atomic_save_keeps_existing_file_and_cleans_temp(monkeypatch, tmp_path):
    data_file = tmp_path / "gitmemory.json"
    monkeypatch.setattr("core.storage.DATA_FILE", str(data_file))

    memory = GitMemory()
    save_memory(memory)
    original_data = json.loads(data_file.read_text(encoding="utf-8"))

    def broken_dump(data, f, **kwargs):
        f.write("{broken")
        raise RuntimeError("simulated write failure")

    memory.add_message("user", "new data that should not replace the file")
    monkeypatch.setattr("core.storage.json.dump", broken_dump)

    with pytest.raises(RuntimeError):
        save_memory(memory)

    assert json.loads(data_file.read_text(encoding="utf-8")) == original_data
    assert list(tmp_path.glob(".gitmemory.json.*.tmp")) == []
