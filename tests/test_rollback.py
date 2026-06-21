import copy

import pytest

from core.git_memory import GitMemory


def build_memory_with_expected_contexts():
    memory = GitMemory()
    expected = {memory.head: copy.deepcopy(memory.context)}

    memory.add_message("user", "first message")
    expected[memory.head] = copy.deepcopy(memory.context)

    memory.add_message("assistant", "second message")
    expected[memory.head] = copy.deepcopy(memory.context)

    memory.add_message("user", "third message")
    expected[memory.head] = copy.deepcopy(memory.context)

    return memory, expected


def test_rollback_invalid_node_keeps_head_and_context():
    memory, _ = build_memory_with_expected_contexts()
    head_before = memory.head
    context_before = copy.deepcopy(memory.context)

    with pytest.raises(ValueError, match="node id does not exist"):
        memory.rollback(999)

    assert memory.head == head_before
    assert memory.context == context_before


def test_rollback_rebuilds_each_node_context_and_base():
    memory, expected = build_memory_with_expected_contexts()

    for target, expected_context in expected.items():
        rolled_back_id = memory.rollback(target)

        assert rolled_back_id == target
        assert memory.head == target
        assert memory.context == expected_context
        assert memory.base == memory.context


def test_rollback_snapshot_returns_node_id():
    memory = GitMemory()
    memory.add_message("user", "first message")
    target = memory.head
    memory.snapshot("mark")
    memory.add_message("assistant", "later message")

    rolled_back_id = memory.rollback_snapshot("mark")

    assert rolled_back_id == target
    assert memory.head == target


def test_rollback_snapshot_rejects_missing_snapshot():
    memory = GitMemory()

    with pytest.raises(ValueError, match="snapshot not exist"):
        memory.rollback_snapshot("missing")


def test_undo_returns_parent_id():
    memory = GitMemory()
    parent = memory.head
    memory.add_message("user", "first message")

    undone_id = memory.undo()

    assert undone_id == parent
    assert memory.head == parent


def test_undo_rejects_root_node():
    memory = GitMemory()

    with pytest.raises(ValueError, match="already at root node"):
        memory.undo()
