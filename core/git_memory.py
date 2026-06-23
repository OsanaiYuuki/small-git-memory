import copy
from datetime import datetime

from core.diff import diff_data
from core.models import CommitNode, Message, Snapshot
from core.patch import apply_patch, make_patch


DEFAULT_CONTEXT = [
    Message("user", "comeback"),
    Message("assistant", "ok go"),
]


class GitMemory:
    def __init__(self):
        self.snapshots = {}
        self.commits = {}
        self.next_id = 0
        self.base = copy.deepcopy(DEFAULT_CONTEXT)
        self.context = copy.deepcopy(DEFAULT_CONTEXT)
        self.branches = {}
        self.current_branch = "main"

        self._create_root()

    def add_message(self, role: str, content: str) -> None:
        message = Message(role, content)
        self.context.append(message)
        self.commit()

    def remove_message(self, index: int) -> Message:
        if len(self.context) == 0:
            raise ValueError("no messages can be deleted")

        real_index = index - 1

        if real_index < 0 or real_index >= len(self.context):
            raise ValueError("message index out of range")

        removed_message = self.context.pop(real_index)
        self.commit()
        return removed_message

    def snapshot(self, name: str, note: str = "") -> Snapshot:
        if name in self.snapshots:
            raise ValueError("snapshot already exists")

        snapshot = Snapshot(
            name=name,
            node_id=self.head,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note=note,
            cached_context=copy.deepcopy(self.context),
        )
        self.snapshots[name] = snapshot
        return snapshot

    def delete_snapshot(self, name) -> str:
        if name == "__root__":
            raise ValueError("root snapshot can not be deleted")
        if name not in self.snapshots:
            raise ValueError("snapshot not exist")
        del self.snapshots[name]
        return name

    def auto_snapshot(self):
        index = 1
        while True:
            name = "checkpoint_" + str(index)

            if name not in self.snapshots:
                break
            index += 1
        return self.snapshot(name)

    def rollback(self, node_id: int) -> int:
        if node_id not in self.commits:
            raise ValueError("node id does not exist")

        self.head = node_id
        self.context = self._rebuild(node_id)
        self.base = copy.deepcopy(self.context)
        return self.head

    def rollback_snapshot(self, name: str) -> int:
        if name not in self.snapshots:
            raise ValueError("snapshot not exist")

        node_id = self.snapshots[name].node_id
        return self.rollback(node_id)

    def branch(self, name: str) -> dict:
        if name == "":
            raise ValueError("branch name must be non-empty")

        if name in self.branches:
            raise ValueError("branch already exists")

        self.branches[name] = self.head
        return {
            "name": name,
            "head": self.head,
            "is_current": name == self.current_branch,
        }

    def checkout(self, name: str) -> int:
        if name not in self.branches:
            raise ValueError("branch not exist")

        self.current_branch = name
        return self.rollback(self.branches[name])

    def branches_data(self) -> list[dict]:
        return [
            {
                "name": name,
                "head": head,
                "is_current": name == self.current_branch,
            }
            for name, head in sorted(self.branches.items())
        ]

    def status(self):
        return self.status_data()

    def status_data(self):
        return {
            "head": self.head,
            "current_branch": self.current_branch,
            "commit_count": len(self.commits),
            "snapshot_count": len(self.snapshots),
            "commits_since_snapshot": self.commits_since_snapshots(),
            "context": self.context_data(),
        }

    def show_context(self):
        return self.context_data()

    def context_data(self):
        return [
            {
                "index": index,
                "role": message.role,
                "content": message.content,
            }
            for index, message in enumerate(self.context, start=1)
        ]

    def log(self):
        return self.snapshot_log_data()

    def snapshot_log_data(self):
        result = []

        for name, snapshot in self.snapshots.items():
            messages_count = len(snapshot.cached_context) if snapshot.cached_context is not None else 0

            result.append(
                {
                    "name": name,
                    "node_id": snapshot.node_id,
                    "created_at": snapshot.created_at,
                    "note": snapshot.note,
                    "message_count": messages_count,
                    "is_head": snapshot.node_id == self.head,
                }
            )

        return result

    def history(self):
        nodes = []

        for node_id, node in self.commits.items():
            names = []
            for name, snapshot in self.snapshots.items():
                if snapshot.node_id == node_id:
                    names.append(name)

            nodes.append(
                {
                    "id": node.id,
                    "parent": node.parent,
                    "snapshots": names,
                    "is_head": node_id == self.head,
                }
            )

        return nodes

    def diff(self):
        names, snapshot = self._find_nearest_snapshot()
        old_context = snapshot.cached_context
        if old_context is None:
            old_context = self._rebuild(snapshot.node_id)
        new_context = self.context

        return {
            "from": names,
            "changes": diff_data(old_context, new_context),
        }

    def diff_snapshots(self, old_name, new_name):
        if old_name not in self.snapshots:
            raise ValueError("old snapshot not exist")
        if new_name not in self.snapshots:
            raise ValueError("new snapshot not exist")

        old_snapshot = self.snapshots[old_name]
        new_snapshot = self.snapshots[new_name]
        old_context = old_snapshot.cached_context
        if old_context is None:
            old_context = self._rebuild(old_snapshot.node_id)
        new_context = new_snapshot.cached_context
        if new_context is None:
            new_context = self._rebuild(new_snapshot.node_id)

        return {
            "from": old_name,
            "to": new_name,
            "changes": diff_data(old_context, new_context),
        }

    def clear(self):
        self.snapshots = {}
        self.commits = {}
        self.branches = {}
        self.current_branch = "main"
        self.next_id = 0
        self.base = copy.deepcopy(DEFAULT_CONTEXT)
        self.context = copy.deepcopy(DEFAULT_CONTEXT)
        self._create_root()
        return self.status_data()

    def has_user_message(self):
        for message in self.context:
            if message.role == "user":
                return True
        return False

    def has_assistant_message(self):
        for message in self.context:
            if message.role == "assistant":
                return True
        return False

    def validate_context(self):
        return self.validate_context_data()

    def validate_context_data(self):
        errors = []
        warnings = []

        if len(self.context) == 0:
            errors.append("context is empty")

        if not self.has_assistant_message():
            warnings.append("context has no assistant message")

        elif not self.has_user_message():
            warnings.append("context has no user message")

        for index, message in enumerate(self.context, start=1):
            if not isinstance(message.role, str):
                errors.append(f"message {index} has invalid role")

            if not isinstance(message.content, str):
                errors.append(f"message {index} has invalid content")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "message_count": len(self.context),
        }

    def commit(self):
        if self.base == self.context:
            return

        patch = make_patch(self.base, self.context)

        new_id = self.next_id
        self.commits[new_id] = CommitNode(
            id=new_id,
            parent=self.head,
            patch=patch,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        self.next_id += 1
        self.head = new_id
        self.branches[self.current_branch] = self.head
        self.base = copy.deepcopy(self.context)

    def _create_root(self):
        root_id = self.next_id

        self.commits[root_id] = CommitNode(
            id=root_id,
            parent=None,
            patch=[],
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.next_id += 1
        self.head = root_id
        self.branches[self.current_branch] = root_id

        self.snapshots["__root__"] = Snapshot(
            name="__root__",
            node_id=root_id,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note="System Root Node",
            cached_context=copy.deepcopy(DEFAULT_CONTEXT),
        )

    def _find_snapshot_by_node(self, node_id):
        for snap in self.snapshots.values():
            if node_id == snap.node_id and snap.cached_context is not None:
                return copy.deepcopy(snap.cached_context)
        return None

    def _rebuild(self, node_id):
        patches = []
        current = node_id

        while True:
            start_state = self._find_snapshot_by_node(current)
            if start_state is not None:
                break
            node = self.commits[current]
            patches.append(node.patch)
            current = node.parent

        patches.reverse()

        state = start_state
        for patch in patches:
            state = apply_patch(state, patch)

        return state

    def undo(self):
        parent = self.commits[self.head].parent
        if parent is None:
            raise ValueError("already at root node")
        return self.rollback(parent)

    def commits_since_snapshots(self):
        current = self.head
        count = 0
        while True:
            snap = self._find_snapshot_by_node(current)
            if snap is not None:
                return count
            count += 1
            current = self.commits[current].parent

    def _find_nearest_snapshot(self):
        current = self.head

        while True:
            names = []
            found_snapshot = None

            for name, snapshot in self.snapshots.items():
                if current == snapshot.node_id:
                    names.append(name)
                    found_snapshot = snapshot

            if names:
                return names, found_snapshot
            current = self.commits[current].parent

    def children_by_parent(self) -> dict[int | None, list[int]]:
        children = {}

        for node_id, node in self.commits.items():
            parent = node.parent

            if parent not in children:
                children[parent] = []

            children[parent].append(node_id)

        for child_ids in children.values():
            child_ids.sort()

        return children

    def snapshots_by_node(self) -> dict[int, list[str]]:
        result = {}

        for name, snapshot in self.snapshots.items():
            node_id = snapshot.node_id

            if node_id not in result:
                result[node_id] = []

            result[node_id].append(name)

        for names in result.values():
            names.sort()
        return result

    def get_context_at(self, node_id: int) -> list[Message]:
        if node_id not in self.commits:
            raise ValueError("node_id does not exist")
        return copy.deepcopy(self._rebuild(node_id))

    def history_tree_data(self) -> dict:
        children = self.children_by_parent()
        snapshots = self.snapshots_by_node()

        nodes = {}

        for node_id, node in self.commits.items():
            context = self.get_context_at(node_id)

            nodes[node_id] = {
                "id": node.id,
                "parent": node.parent,
                "children": children.get(node_id, []),
                "snapshots": snapshots.get(node_id, []),
                "is_head": node_id == self.head,
                "message_count": len(context),
                "created_at": node.created_at,
            }

        return {
            "head": self.head,
            "roots": children.get(None, []),
            "nodes": nodes,
        }

    def diff_nodes(self, old_id: int, new_id: int):
        old_context = self.get_context_at(old_id)
        new_context = self.get_context_at(new_id)
        return {
            "from": old_id,
            "to": new_id,
            "changes": diff_data(old_context, new_context),
        }
