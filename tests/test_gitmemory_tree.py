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

    m.snapshot("point1-1")
    m.snapshot("point1-2")

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


def test_diff_nodes_compares_two_node_contexts(capsys):
    memory = GitMemory()

    memory.add_message("user", "a")
    first_node = memory.head

    memory.add_message("assistant", "b")
    second_node = memory.head

    memory.diff_nodes(first_node, second_node)

    output = capsys.readouterr().out

    assert "+ assistant: b" in output


def test_diff_nodes_rejects_missing_node():
    memory = GitMemory()

    with pytest.raises(ValueError):
        memory.diff_nodes(0, 999)
