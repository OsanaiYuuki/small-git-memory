from core.models import messages_to_data
from core.patch import apply_patch, make_patch, undo


def assert_patch_roundtrip(old, new):
    patch = make_patch(old, new)

    rebuilt = apply_patch(old, patch)
    assert messages_to_data(rebuilt) == new

    reverted = undo(new, patch)
    assert messages_to_data(reverted) == old


def test_make_patch_add_message():
    old = [
        {"role": "user", "content": "你好"},
    ]
    new = [
        {"role": "user", "content": "你好"},
        {"role": "user", "content": "帮我写代码"},
    ]

    assert_patch_roundtrip(old, new)


def test_make_patch_delete_message():
    old = [
        {"role": "user", "content": "你好"},
        {"role": "user", "content": "再见"},
    ]
    new = [
        {"role": "user", "content": "你好"},
    ]

    assert_patch_roundtrip(old, new)


def test_make_patch_change_message_as_delete_add():
    old = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "A"},
    ]
    new = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "B"},
    ]

    assert_patch_roundtrip(old, new)


def test_make_patch_keep_all_messages():
    old = [
        {"role": "user", "content": "你好"},
    ]
    new = [
        {"role": "user", "content": "你好"},
    ]

    assert_patch_roundtrip(old, new)
