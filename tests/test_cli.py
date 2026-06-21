import builtins
from types import SimpleNamespace

from cli import run_cli


class FakeMemory:
    def __init__(self):
        self.diff_nodes_args = None
        self.diff_snapshots_args = None
        self.snapshot_args = None

    def diff_nodes(self, old_id, new_id):
        self.diff_nodes_args = (old_id, new_id)
        return {"from": old_id, "to": new_id, "changes": []}

    def diff_snapshots(self, old_name, new_name):
        self.diff_snapshots_args = (old_name, new_name)
        return {"from": old_name, "to": new_name, "changes": []}

    def snapshot(self, name, note=""):
        self.snapshot_args = (name, note)
        return SimpleNamespace(name=name, node_id=7)


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
