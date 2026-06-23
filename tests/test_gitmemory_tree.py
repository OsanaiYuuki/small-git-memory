import pytest

from core.git_memory import GitMemory


def test_children_by_parent_after_branching():
    m = GitMemory()

    m.add_message("user", "a")
    m.rollback(0)
    m.add_message("assistant", "b")

    assert m.children_by_parent()[0] == [1, 2]


def test_snapshots_by_node_groups_names():
    m = GitMemory()

    m.add_message("user", "a")
    node1 = m.head

    snapshot = m.snapshot("point1-1")
    m.snapshot("point1-2")

    assert snapshot.name == "point1-1"
    assert snapshot.node_id == node1
    assert m.snapshots_by_node()[node1] == ["point1-1", "point1-2"]


def test_get_context_at_returns_copy():
    m = GitMemory()

    m.add_message("user", "a")
    node1 = m.head
    context = m.get_context_at(node1)

    assert context[-1].role == "user"
    assert context[-1].content == "a"

    context.append("bad")

    assert len(m.get_context_at(node1)) == 3


def test_history_tree_data_marks_head_and_snapshots():
    memory = GitMemory()

    memory.add_message("user", "a")
    first_node = memory.head

    memory.snapshot("mark")

    memory.add_message("assistant", "b")
    second_node = memory.head

    memory.rollback(first_node)
    memory.add_message("user", "branch")
    branch_node = memory.head

    tree = memory.history_tree_data()

    assert tree["head"] == branch_node
    assert tree["roots"] == [0]

    nodes = tree["nodes"]

    assert nodes[0]["snapshots"] == ["__root__"]
    assert nodes[first_node]["snapshots"] == ["mark"]

    assert nodes[first_node]["children"] == [second_node, branch_node]

    assert nodes[branch_node]["is_head"] is True
    assert nodes[second_node]["is_head"] is False
    assert nodes[first_node]["is_head"] is False

    assert nodes[first_node]["message_count"] == 3
    assert nodes[second_node]["message_count"] == 4
    assert nodes[branch_node]["message_count"] == 4


def test_diff_nodes_compares_two_node_contexts():
    memory = GitMemory()

    memory.add_message("user", "a")
    first_node = memory.head

    memory.add_message("assistant", "b")
    second_node = memory.head

    diff = memory.diff_nodes(first_node, second_node)

    assert diff["from"] == first_node
    assert diff["to"] == second_node
    assert diff["changes"] == [
        {"op": "add", "role": "assistant", "content": "b"},
    ]


def test_diff_nodes_rejects_missing_node():
    memory = GitMemory()

    with pytest.raises(ValueError):
        memory.diff_nodes(0, 999)


def test_snapshot_log_data_includes_note():
    memory = GitMemory()

    memory.snapshot("mark", "a tiny note")

    snapshots = memory.snapshot_log_data()

    assert snapshots[-1]["name"] == "mark"
    assert snapshots[-1]["note"] == "a tiny note"
    assert snapshots[-1]["is_head"] is True


def test_status_data_returns_summary_and_context():
    memory = GitMemory()

    memory.add_message("user", "a")

    status = memory.status_data()

    assert status["head"] == memory.head
    assert status["commit_count"] == len(memory.commits)
    assert status["snapshot_count"] == len(memory.snapshots)
    assert status["commits_since_snapshot"] == 1
    assert status["context"][-1] == {
        "index": 3,
        "role": "user",
        "content": "a",
    }


def test_context_data_returns_message_dicts():
    memory = GitMemory()

    assert memory.context_data() == [
        {"index": 1, "role": "user", "content": "comeback"},
        {"index": 2, "role": "assistant", "content": "ok go"},
    ]


def test_snapshot_rejects_duplicate_name():
    memory = GitMemory()
    memory.snapshot("mark")

    with pytest.raises(ValueError, match="snapshot already exists"):
        memory.snapshot("mark")


def test_delete_snapshot_rejects_root_and_missing_names():
    memory = GitMemory()

    with pytest.raises(ValueError, match="root snapshot can not be deleted"):
        memory.delete_snapshot("__root__")

    with pytest.raises(ValueError, match="snapshot not exist"):
        memory.delete_snapshot("missing")


def test_delete_snapshot_removes_existing_snapshot():
    memory = GitMemory()
    memory.snapshot("mark")

    deleted_name = memory.delete_snapshot("mark")

    assert deleted_name == "mark"
    assert "mark" not in memory.snapshots


def test_auto_snapshot_returns_created_snapshot():
    memory = GitMemory()

    snapshot = memory.auto_snapshot()

    assert snapshot.name == "checkpoint_1"
    assert snapshot.node_id == memory.head


def test_query_methods_return_data_without_printing(capsys):
    memory = GitMemory()
    memory.snapshot("mark")
    memory.add_message("user", "a")

    assert memory.show_context() == memory.context_data()
    assert memory.status() == memory.status_data()
    assert memory.log() == memory.snapshot_log_data()
    assert memory.history()[-1]["is_head"] is True
    assert memory.diff()["changes"] == [
        {"op": "add", "role": "user", "content": "a"},
    ]

    assert capsys.readouterr().out == ""


def test_validate_context_data_returns_structured_result():
    memory = GitMemory()

    result = memory.validate_context_data()

    assert result == {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "message_count": 2,
    }


def test_validate_context_data_reports_missing_assistant():
    memory = GitMemory()
    memory.remove_message(2)

    result = memory.validate_context_data()

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["warnings"] == ["context has no assistant message"]


def test_clear_returns_status_data_without_printing(capsys):
    memory = GitMemory()
    memory.add_message("user", "a")

    status = memory.clear()

    assert status == memory.status_data()
    assert status["head"] == 0
    assert status["commit_count"] == 1
    assert capsys.readouterr().out == ""


def test_initializes_main_branch_at_root():
    memory = GitMemory()

    assert memory.current_branch == "main"
    assert memory.branches == {"main": 0}
    assert memory.branches_data() == [
        {"name": "main", "head": 0, "is_current": True},
    ]


def test_branch_creates_branch_at_current_head_without_checkout():
    memory = GitMemory()
    memory.add_message("user", "a")
    head = memory.head

    branch = memory.branch("idea")

    assert branch == {"name": "idea", "head": head, "is_current": False}
    assert memory.current_branch == "main"
    assert memory.branches["idea"] == head


def test_branch_rejects_duplicate_name():
    memory = GitMemory()

    with pytest.raises(ValueError, match="branch already exists"):
        memory.branch("main")


def test_branch_rejects_empty_name():
    memory = GitMemory()

    with pytest.raises(ValueError, match="branch name must be non-empty"):
        memory.branch("")


def test_checkout_moves_head_and_current_branch():
    memory = GitMemory()
    memory.add_message("user", "a")
    idea_head = memory.head
    memory.branch("idea")
    memory.add_message("assistant", "b")

    checked_out_id = memory.checkout("idea")

    assert checked_out_id == idea_head
    assert memory.head == idea_head
    assert memory.current_branch == "idea"
    assert memory.context[-1].content == "a"


def test_checkout_rejects_missing_branch():
    memory = GitMemory()

    with pytest.raises(ValueError, match="branch not exist"):
        memory.checkout("missing")


def test_current_branch_moves_when_new_commit_is_created():
    memory = GitMemory()
    memory.add_message("user", "a")
    memory.branch("idea")
    memory.checkout("idea")

    memory.add_message("assistant", "b")

    assert memory.branches["idea"] == memory.head


def test_rollback_does_not_move_branch_pointer_until_next_commit():
    memory = GitMemory()
    memory.add_message("user", "a")
    old_head = memory.head
    memory.add_message("assistant", "b")
    branch_head = memory.head

    memory.rollback(old_head)

    assert memory.head == old_head
    assert memory.branches["main"] == branch_head

    memory.add_message("user", "branch from old head")

    assert memory.branches["main"] == memory.head
    assert memory.commits[memory.head].parent == old_head
