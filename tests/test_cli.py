import builtins
from types import SimpleNamespace

from cli import run_cli


class FakeMemory:
    def __init__(self):
        self.diff_nodes_args = None
        self.diff_snapshots_args = None
        self.snapshot_args = None
        self.branch_args = None
        self.checkout_args = None

    def diff_nodes(self, old_id, new_id):
        self.diff_nodes_args = (old_id, new_id)
        return {"from": old_id, "to": new_id, "changes": []}

    def diff_snapshots(self, old_name, new_name):
        self.diff_snapshots_args = (old_name, new_name)
        return {"from": old_name, "to": new_name, "changes": []}

    def snapshot(self, name, note=""):
        self.snapshot_args = (name, note)
        return SimpleNamespace(name=name, node_id=7)

    def remove_message(self, index):
        self.remove_args = index
        return SimpleNamespace(role="user", content="hello")

    def validate_context(self):
        return {
            "is_valid": True,
            "errors": [],
            "warnings": ["context has no assistant message"],
            "message_count": 1,
        }

    def branch(self, name):
        self.branch_args = name
        return {"name": name, "head": 7, "is_current": False}

    def checkout(self, name):
        self.checkout_args = name
        return 7

    def branches_data(self):
        return [
            {"name": "main", "head": 0, "is_current": True},
            {"name": "idea", "head": 7, "is_current": False},
        ]


def test_cli_diff_nodes_parses_ids(monkeypatch):
    memory = FakeMemory()
    commands = iter(["diff_nodes 1 2", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    assert memory.diff_nodes_args == (1, 2)


def test_cli_diff_snapshot_passes_names(monkeypatch):
    memory = FakeMemory()
    commands = iter(["diff_snapshot old new", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    assert memory.diff_snapshots_args == ("old", "new")


def test_cli_snapshot_passes_note(monkeypatch):
    memory = FakeMemory()
    commands = iter(["snapshot mark_a note with spaces", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    assert memory.snapshot_args == ("mark_a", "note with spaces")


def test_cli_snapshot_prints_error(monkeypatch, capsys):
    class BrokenSnapshotMemory(FakeMemory):
        def snapshot(self, name, note=""):
            raise ValueError("snapshot already exists")

    memory = BrokenSnapshotMemory()
    commands = iter(["snapshot mark_a", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    assert "snapshot already exists" in capsys.readouterr().out


def test_cli_diff_nodes_prints_error(monkeypatch, capsys):
    class BrokenDiffNodesMemory(FakeMemory):
        def diff_nodes(self, old_id, new_id):
            raise ValueError("node_id does not exist")

    memory = BrokenDiffNodesMemory()
    commands = iter(["diff_nodes 1 999", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    assert "node_id does not exist" in capsys.readouterr().out


def test_cli_remove_prints_removed_message(monkeypatch, capsys):
    memory = FakeMemory()
    commands = iter(["remove 1", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    output = capsys.readouterr().out
    assert memory.remove_args == 1
    assert "remove: user: hello" in output


def test_cli_validate_prints_structured_result(monkeypatch, capsys):
    memory = FakeMemory()
    commands = iter(["validate", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    output = capsys.readouterr().out
    assert "warning: context has no assistant message" in output
    assert "context validation finished" in output


def test_cli_branch_creates_branch(monkeypatch, capsys):
    memory = FakeMemory()
    commands = iter(["branch idea", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    output = capsys.readouterr().out
    assert memory.branch_args == "idea"
    assert "branch created: idea on node 7" in output


def test_cli_checkout_switches_branch(monkeypatch, capsys):
    memory = FakeMemory()
    commands = iter(["checkout idea", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    output = capsys.readouterr().out
    assert memory.checkout_args == "idea"
    assert "switched to branch idea on node 7" in output


def test_cli_branches_prints_branch_list(monkeypatch, capsys):
    memory = FakeMemory()
    commands = iter(["branches", "exit"])

    monkeypatch.setattr(builtins, "input", lambda _: next(commands))

    run_cli(memory)

    output = capsys.readouterr().out
    assert "branches:" in output
    assert "* main -> 0" in output
    assert "  idea -> 7" in output
