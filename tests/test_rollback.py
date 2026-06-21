import copy

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

    memory.rollback(999)

    assert memory.head == head_before
    assert memory.context == context_before


def test_rollback_rebuilds_each_node_context_and_base():
    memory, expected = build_memory_with_expected_contexts()

    for target, expected_context in expected.items():
        memory.rollback(target)

        assert memory.head == target
        assert memory.context == expected_context
        assert memory.base == memory.context
