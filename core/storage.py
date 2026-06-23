import json
import os
import tempfile

from config import DATA_FILE
from core.models import (
    commit_from_data,
    commit_to_data,
    messages_from_data,
    messages_to_data,
    snapshot_from_data,
    snapshot_to_data,
)


STORAGE_VERSION = 2


def save_memory(memory):
    data = memory_to_data(memory)
    save_data_atomic(DATA_FILE, data)

    print("saved to", DATA_FILE)


def save_data_atomic(path, data):
    directory = os.path.dirname(path) or "."
    basename = os.path.basename(path)
    temp_path = None

    try:
        fd, temp_path = tempfile.mkstemp(
            prefix=f".{basename}.",
            suffix=".tmp",
            dir=directory,
            text=True,
        )

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None and os.path.exists(temp_path):
            os.remove(temp_path)


def load_memory(memory):
    if not os.path.exists(DATA_FILE):
        print("data file not exist:", DATA_FILE)
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("data file is not valid json:", DATA_FILE)
        return

    data = migrate_data(data)

    if data is None:
        return

    if not validate_data(data):
        return

    apply_data_to_memory(memory, data)

    print("loaded from", DATA_FILE)


def validate_messages(messages):
    if not isinstance(messages, list):
        print("message is not a list:", messages)
        return False

    for message in messages:
        if not isinstance(message, dict):
            print("message is not a dict:", message)
            return False
        if "role" not in message or "content" not in message:
            print("message missing role or content", message)
            return False
    return True


def validate_data(data):
    version = get_storage_version(data)

    if version != STORAGE_VERSION:
        print("unsupported storage version:", version)
        return False

    required_keys = [
        "version",
        "context",
        "base",
        "head",
        "commits",
        "snapshots",
        "next_id",
        "branches",
        "current_branch",
    ]

    for key in required_keys:
        if key not in data:
            print("data file missing key:", key)
            return False

    if not isinstance(data["snapshots"], dict):
        print("snapshots must be a dict")
        return False

    if not isinstance(data["commits"], dict):
        print("commits must be a dict")
        return False

    if not isinstance(data["head"], int):
        print("head must be an int (node id)")
        return False

    if not isinstance(data["next_id"], int):
        print("next_id must be an int")
        return False

    if not isinstance(data["branches"], dict):
        print("branches must be a dict")
        return False

    if not isinstance(data["current_branch"], str):
        print("current_branch must be a string")
        return False

    if data["current_branch"] not in data["branches"]:
        print("current branch not exist")
        return False

    if not validate_data_commits(data):
        return False

    for name, node_id in data["branches"].items():
        if not isinstance(name, str) or name == "":
            print("branch name must be a non-empty string")
            return False
        if not isinstance(node_id, int):
            print("branch head must be an int:", name)
            return False
        if str(node_id) not in data["commits"]:
            print("branch points to missing node:", name)
            return False

    if not validate_messages(data["context"]):
        return False

    if not validate_messages(data["base"]):
        return False

    for name, snapshot in data["snapshots"].items():
        if not isinstance(snapshot, dict):
            print("snapshot should be a dict")
            return False

        required_snapshots_keys = ["created_at", "note", "node_id"]

        for key in required_snapshots_keys:
            if key not in snapshot:
                print("snapshots file missing key:", key)
                return False
        if "cached_context" not in snapshot and "messages" not in snapshot:
            print("snapshot missing cached_context:", name)
            return False
        if not isinstance(snapshot["node_id"], int):
            print("snapshot node_id must be an int:", name)
            return False

        if str(snapshot["node_id"]) not in data["commits"]:
            print("snapshot points to missing node:", name)
            return False

        cached_context = snapshot.get("cached_context", snapshot.get("messages"))
        if cached_context is not None and not validate_messages(cached_context):
            print("snapshot cached_context is invalid", snapshot)
            return False

    return True


def memory_to_data(memory):
    commits = {}
    for commit_id, node in memory.commits.items():
        commits[str(commit_id)] = commit_to_data(node)

    snapshots = {}
    for name, snapshot in memory.snapshots.items():
        snapshots[name] = snapshot_to_data(snapshot)

    return {
        "version": STORAGE_VERSION,
        "context": messages_to_data(memory.context),
        "base": messages_to_data(memory.base),
        "head": memory.head,
        "commits": commits,
        "snapshots": snapshots,
        "next_id": memory.next_id,
        "branches": memory.branches,
        "current_branch": memory.current_branch,
    }


def apply_data_to_memory(memory, data):
    memory.context = messages_from_data(data["context"])
    memory.base = messages_from_data(data["base"])
    memory.head = data["head"]
    memory.snapshots = {
        name: snapshot_from_data(name, snapshot) for name, snapshot in data["snapshots"].items()
    }
    memory.next_id = data["next_id"]
    memory.commits = {int(k): commit_from_data(v) for k, v in data["commits"].items()}
    memory.branches = {name: node_id for name, node_id in data["branches"].items()}
    memory.current_branch = data["current_branch"]


def validate_data_commits(data):
    required_commit_key = ["id", "parent", "patch", "created_at"]

    if str(data["head"]) not in data["commits"]:
        print("head node not exist")
        return False
    for commit_id, node in data["commits"].items():
        if not isinstance(node, dict):
            print("commit node must be a dict:", commit_id)
            return False

        for key in required_commit_key:
            if key not in node:
                print("commit missing key:", key)
                return False
        if not isinstance(node["id"], int):
            print("commit id must be an int:", commit_id)
            return False

        if str(node["id"]) != commit_id:
            print("commit key and id mismatch:", commit_id)
            return False

        if not isinstance(node["patch"], list):
            print("commit patch must be a list:", commit_id)
            return False

        parent = node["parent"]

        if parent is not None and not isinstance(parent, int):
            print("commit parent must be None or int:", commit_id)
            return False

        if parent is not None and str(parent) not in data["commits"]:
            print("commit parent not exist:", commit_id)
            return False

    return True


def get_storage_version(data):
    return data.get("version", 0)


def migrate_data(data):
    version = data.get("version", 0)
    migrated = dict(data)

    if version == STORAGE_VERSION:
        return migrated

    if version == 0:
        migrated["version"] = 1

        snapshots = {}
        for name, snapshot in migrated["snapshots"].items():
            new_snapshot = dict(snapshot)
            if "cached_context" not in new_snapshot and "messages" in new_snapshot:
                new_snapshot["cached_context"] = new_snapshot.pop("messages")
            snapshots[name] = new_snapshot

        migrated["snapshots"] = snapshots
        version = 1

    if version == 1:
        migrated["version"] = 2
        migrated["branches"] = {"main": migrated["head"]}
        migrated["current_branch"] = "main"

        return migrated

    print("unsupported storage version:", version)
    return None
