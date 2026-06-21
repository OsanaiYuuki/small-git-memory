import copy

from core.git_memory import GitMemory
from core.patch import apply_patch


def test_commit_without_changes_does_not_create_node():
    memory = GitMemory()

    memory.commit()

    assert len(memory.commits) == 1
    assert memory.head == 0


def test_add_message_auto_commits_and_advances_base():
    memory = GitMemory()
    before_base = copy.deepcopy(memory.base)

    memory.add_message("user", "help me write code")

    assert len(memory.commits) == 2
    assert memory.base == memory.context
    rebuilt = apply_patch(before_base, memory.commits[memory.head].patch)
    assert rebuilt == memory.context


def test_remove_message_auto_commits_and_advances_base():
    memory = GitMemory()
    memory.add_message("user", "help me write code")
    before_base = copy.deepcopy(memory.base)

    memory.remove_message(1)

    assert len(memory.commits) == 3
    assert memory.base == memory.context
    rebuilt = apply_patch(before_base, memory.commits[memory.head].patch)
    assert rebuilt == memory.context


def test_commit_after_no_new_change_does_not_create_extra_node():
    memory = GitMemory()
    memory.add_message("user", "help me write code")
    memory.remove_message(1)

    memory.commit()

    assert len(memory.commits) == 3
