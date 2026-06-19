from dataclasses import dataclass
from typing import Literal


Role = Literal["user", "assistant", "system"]
PatchOpName = Literal["keep", "add", "delete"]


@dataclass
class Message:
    role: Role
    content: str

    def __post_init__(self):
        if self.role not in ("user", "assistant", "system"):
            raise ValueError("message role must be user, assistant, or system")
        if not isinstance(self.content, str):
            raise TypeError("message content must be a string")

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise TypeError("message must be a dict")
        if "role" not in data or "content" not in data:
            raise ValueError("message missing role or content")
        return cls(role=data["role"], content=data["content"])


@dataclass
class KeepOp:
    op: Literal["keep"] = "keep"

    def to_dict(self):
        return {"op": self.op}


@dataclass
class AddOp:
    message: Message
    op: Literal["add"] = "add"

    def to_dict(self):
        return {
            "op": self.op,
            "message": self.message.to_dict(),
        }


@dataclass
class DeleteOp:
    message: Message
    op: Literal["delete"] = "delete"

    def to_dict(self):
        return {
            "op": self.op,
            "message": self.message.to_dict(),
        }


PatchOp = KeepOp | AddOp | DeleteOp


@dataclass
class CommitNode:
    id: int
    parent: int | None
    patch: list[PatchOp]
    created_at: str

    def __post_init__(self):
        if not isinstance(self.id, int):
            raise TypeError("commit id must be an int")
        if self.parent is not None and not isinstance(self.parent, int):
            raise TypeError("commit parent must be None or int")
        self.patch = patch_from_data(self.patch)
        if not isinstance(self.created_at, str):
            raise TypeError("commit created_at must be a string")

    def to_dict(self):
        return {
            "id": self.id,
            "parent": self.parent,
            "patch": patch_to_data(self.patch),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, CommitNode):
            return data
        if not isinstance(data, dict):
            raise TypeError("commit node must be a dict")
        return cls(
            id=data["id"],
            parent=data["parent"],
            patch=data["patch"],
            created_at=data["created_at"],
        )


def commit_from_data(data):
    return CommitNode.from_dict(data)


def commit_to_data(commit):
    return CommitNode.from_dict(commit).to_dict()


@dataclass
class Snapshot:
    name: str
    node_id: int
    created_at: str
    note: str = ""
    cached_context: list[Message] | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or self.name == "":
            raise ValueError("snapshot name must be a non-empty string")
        if not isinstance(self.node_id, int):
            raise TypeError("snapshot node_id must be an int")
        if not isinstance(self.created_at, str):
            raise TypeError("snapshot created_at must be a string")
        if not isinstance(self.note, str):
            raise TypeError("snapshot note must be a string")
        if self.cached_context is not None:
            self.cached_context = messages_from_data(self.cached_context)

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "created_at": self.created_at,
            "note": self.note,
            "cached_context": messages_to_data(self.cached_context) if self.cached_context is not None else None,
        }

    @classmethod
    def from_dict(cls, name, data):
        if isinstance(data, Snapshot):
            if data.name != name:
                raise ValueError("snapshot key and name mismatch")
            return data
        if not isinstance(data, dict):
            raise TypeError("snapshot must be a dict")
        return cls(
            name=name,
            node_id=data["node_id"],
            created_at=data["created_at"],
            note=data.get("note", ""),
            cached_context=data.get("cached_context", data.get("messages")),
        )


def snapshot_from_data(name, data):
    return Snapshot.from_dict(name, data)


def snapshot_to_data(snapshot):
    if not isinstance(snapshot, Snapshot):
        raise TypeError("snapshot must be a Snapshot")
    return snapshot.to_dict()


def message_from_data(data):
    if isinstance(data, Message):
        return data
    return Message.from_dict(data)


def messages_from_data(messages):
    if not isinstance(messages, list):
        raise TypeError("messages must be a list")
    return [message_from_data(message) for message in messages]


def messages_to_data(messages):
    return [message_from_data(message).to_dict() for message in messages]


def patch_op_from_data(data):
    if isinstance(data, (KeepOp, AddOp, DeleteOp)):
        return data
    if not isinstance(data, dict):
        raise TypeError("patch op must be a dict")

    op = data.get("op")
    if op == "keep":
        return KeepOp()
    if op == "add":
        return AddOp(message_from_data(data.get("message")))
    if op == "delete":
        return DeleteOp(message_from_data(data.get("message")))
    raise ValueError("unknown patch op")


def patch_from_data(patch):
    if not isinstance(patch, list):
        raise TypeError("patch must be a list")
    return [patch_op_from_data(op) for op in patch]


def patch_to_data(patch):
    return [patch_op_from_data(op).to_dict() for op in patch]
