from core.models import messages_to_data
from core.patch import make_patch, apply_patch, undo


def check_patch(title, old, new):
    patch = make_patch(old, new)

    rebuilt = apply_patch(old, patch)
    assert messages_to_data(rebuilt) == new, "apply_patch failed"

    reverted = undo(new, patch)
    assert messages_to_data(reverted) == old, "undo failed"

    print(title, "yes")


def test_add():
    old = [
        {"role": "user", "content": "nihao1"}
    ]
    new = [
        {"role": "user", "content": "nihao1"},
        {"role": "assistant", "content": "nihao"}
    ]
    check_patch("add", old, new)


def test_delete():
    old = [
        {"role": "user", "content": "nihao1"},
        {"role": "assistant", "content": "nihao"}
    ]
    new = [
        {"role": "user", "content": "nihao1"}
    ]
    check_patch("delete", old, new)


def test_change():
    old = [
        {"role": "user", "content": "nihao1"},
        {"role": "assistant", "content": "nihao"}
    ]
    new = [
        {"role": "user", "content": "nihao1"},
        {"role": "assistant", "content": "no bad"}
    ]
    check_patch("change", old, new)


def test_keep():
    old = [
        {"role": "user", "content": "nihao1"}
    ]
    new = [
        {"role": "user", "content": "nihao1"}
    ]
    check_patch("keep", old, new)
