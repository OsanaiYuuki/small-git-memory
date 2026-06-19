from core.git_memory import GitMemory
from core.storage import memory_to_data , validate_data , migrate_data

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