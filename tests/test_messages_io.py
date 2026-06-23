import json

import pytest

from core.messages_io import (
    messages_from_openai,
    messages_to_markdown,
    read_openai_messages,
    write_markdown_messages,
    write_openai_messages,
)
from core.models import Message


def test_write_and_read_openai_messages(tmp_path):
    path = tmp_path / "messages.json"
    messages = [
        Message("user", "hello"),
        Message("assistant", "hi"),
    ]

    write_openai_messages(path, messages)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    assert read_openai_messages(path) == messages


def test_messages_from_openai_accepts_wrapped_messages():
    messages = messages_from_openai({
        "messages": [
            {"role": "user", "content": "hello"},
        ]
    })

    assert messages == [Message("user", "hello")]


def test_messages_from_openai_rejects_unknown_dict_shape():
    with pytest.raises(ValueError, match="openai export must be a list or contain messages"):
        messages_from_openai({"bad": []})


def test_messages_to_markdown_formats_transcript():
    text = messages_to_markdown([
        Message("user", "hello"),
        Message("assistant", "hi"),
    ])

    assert text == "# GitMemory Messages\n\n## user\n\nhello\n\n## assistant\n\nhi\n"


def test_write_markdown_messages_creates_parent_directory(tmp_path):
    path = tmp_path / "exports" / "messages.md"

    write_markdown_messages(path, [Message("user", "hello")])

    assert path.read_text(encoding="utf-8") == "# GitMemory Messages\n\n## user\n\nhello\n"
