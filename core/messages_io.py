import json
from pathlib import Path

from core.models import message_from_data, messages_from_data, messages_to_data


def messages_to_openai(messages):
    return messages_to_data(messages)


def messages_from_openai(data):
    if isinstance(data, dict):
        if "messages" not in data:
            raise ValueError("openai export must be a list or contain messages")
        data = data["messages"]

    return messages_from_data(data)


def read_openai_messages(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return messages_from_openai(data)


def write_openai_messages(path, messages):
    data = messages_to_openai(messages)
    _ensure_parent_directory(path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def messages_to_markdown(messages):
    lines = ["# GitMemory Messages", ""]

    for message in messages:
        message = message_from_data(message)
        lines.append(f"## {message.role}")
        lines.append("")
        lines.append(message.content)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_markdown_messages(path, messages):
    _ensure_parent_directory(path)

    with open(path, "w", encoding="utf-8") as f:
        f.write(messages_to_markdown(messages))


def _ensure_parent_directory(path):
    parent = Path(path).parent
    if str(parent) != ".":
        parent.mkdir(parents=True, exist_ok=True)
