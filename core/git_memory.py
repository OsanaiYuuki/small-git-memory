import copy
from datetime import datetime

from core.diff import show_diff
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

        self._create_root()

    def add_message(self, role: str, content: str) -> None:
        message = Message(role, content)
        self.context.append(message)
        self.commit()

    def remove_message(self, index: int) -> None:
        if len(self.context) == 0:
            print("No messages can be deleted")
            return

        real_index = index - 1

        if real_index < 0 or real_index >= len(self.context):
            print("message index out of range", index)
            return

        removed_message = self.context.pop(real_index)
        print("remove:", removed_message.role + ":", removed_message.content)

        self.validate_context()
        self.commit()

    def snapshot(self, name: str, note: str = "") -> None:
        if name in self.snapshots:
            print("The name already exists!")
            return

        self.snapshots[name] = Snapshot(
            name=name,
            node_id=self.head,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note=note,
            cached_context=copy.deepcopy(self.context),
        )
        print(f"snapshot created: {name} on node {self.head}")

    def delete_snapshot(self, name):
        if name == "__root__":
            print("root snapshot can not be deleted")
            return
        if name not in self.snapshots:
            print("snapshot not exist:", name)
            return
        del self.snapshots[name]
        print("snapshot deleted:", name)

    def auto_snapshot(self):
        index = 1
        while True:
            name = "checkpoint_" + str(index)

            if name not in self.snapshots:
                break
            index += 1
        self.snapshot(name)

    def rollback(self, node_id: int) -> None:
        if node_id not in self.commits:
            print("id is not exist", node_id)
            return

        self.head = node_id
        self.context = self._rebuild(node_id)
        self.base = copy.deepcopy(self.context)

    def rollback_snapshot(self, name: str):
        if name not in self.snapshots:
            print("no name can rollback:", name)
            return

        node_id = self.snapshots[name].node_id
        self.rollback(node_id)

    def status(self):
        print("HEAD node:", self.head)
        print("commit nodes:", len(self.commits))
        print("snapshots:", len(self.snapshots))

        drift = self.commits_since_snapshots()
        if drift == 0:
            print("current HEAD is on a snapshot")
        else:
            print(f"{drift} commits since nearest snapshot; consider creating a snapshot")

        print("current context:")
        for index, message in enumerate(self.context, start=1):
            print(" ", index, message.role + ":", message.content)

    def show_context(self):
        print("context:")

        for index, message in enumerate(self.context, start=1):
            print(index, message.role + ":", message.content)

    def log(self):
        print("snapshots:")

        for name, snapshot in self.snapshots.items():
            messages_count = len(snapshot.cached_context) if snapshot.cached_context is not None else 0
            now_time = snapshot.created_at
            note = snapshot.note

            print(f"{name} ({now_time}  {messages_count}  messages)")
            print(f"   note:{note}")

            if snapshot.node_id == self.head:
                print("now in this snapshots:", name)

    def history(self):
        print("commits:")

        for node_id, node in self.commits.items():
            marker = " "
            names = []
            for name, snapshot in self.snapshots.items():
                if snapshot.node_id == node_id:
                    names.append(name)
            if names:
                snapshot_text = ", ".join(names)
            else:
                snapshot_text = "-"
            if node_id == self.head:
                marker = "*"

            commit_id = node.id
            parent = node.parent

            print(f"{marker} id={commit_id} parent={parent} snapshots={snapshot_text}")

    def diff(self):
        names, snapshot = self._find_nearest_snapshot()
        old_context = snapshot.cached_context
        if old_context is None:
            old_context = self._rebuild(snapshot.node_id)
        new_context = self.context

        print("diff from nearest snapshot:", ", ".join(names))

        show_diff(old_context, new_context)

    def diff_snapshots(self, old_name, new_name):
        if old_name not in self.snapshots:
            print("old snapshots not exist")
            return
        if new_name not in self.snapshots:
            print("new snapshots not exists")
            return

        old_snapshot = self.snapshots[old_name]
        new_snapshot = self.snapshots[new_name]
        old_context = old_snapshot.cached_context
        if old_context is None:
            old_context = self._rebuild(old_snapshot.node_id)
        new_context = new_snapshot.cached_context
        if new_context is None:
            new_context = self._rebuild(new_snapshot.node_id)

        print("diff", old_name, "->", new_name)
        show_diff(old_context, new_context)

    def clear(self):
        self.snapshots = {}
        self.commits = {}
        self.next_id = 0
        self.base = copy.deepcopy(DEFAULT_CONTEXT)
        self.context = copy.deepcopy(DEFAULT_CONTEXT)
        self._create_root()
        print("memory cleared")

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
        if len(self.context) == 0:
            print("context is empty")
            return

        if not self.has_assistant_message():
            print("warning:context has no assistant message")

        elif not self.has_user_message():
            print("warning:context has no user message")

        for index, message in enumerate(self.context, start=1):
            if not isinstance(message.role, str):
                print("warnging:message", index, "has invalid role")

            if not isinstance(message.content, str):
                print("warnging:message", index, "has invalid content")

        print("context validation finished")

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
            print("It is already in its initial state and cannot be undone")
            return
        self.rollback(parent)
        print("undone to node", parent)

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
        show_diff(old_context, new_context)
