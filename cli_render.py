def help_info():
    print("commands:")
    print("  add <role> <content>     add a message")
    print("  remove <index>           remove message by index")
    print("  validate                 validate current context")
    print("  snapshot <name> [note]   save current context,save a snapshot")
    print("  delete_snapshot <name>   delete a snapshot")
    print("  auto                     auto create a snapshot")
    print("  branch <name>            create a branch at current HEAD")
    print("  checkout <name>          switch to a branch HEAD")
    print("  branches                 show all branches")
    print("  rollback <node_id>       rollback to a commit node")
    print("  rollback_snapshot <name> rollback to a snapshot")
    print("  undo                     undo to parent node")
    print("  show                     show current context")
    print("  status                   show current status")
    print("  log                      show snapshots")
    print("  history                  show commit tree nodes")
    print("  tree                     show commit tree")
    print("  save                     save data to file")
    print("  clear                    only clear memory")
    print("  all_clear                clear all memory")
    print("  load                     load data from file")
    print("  diff                     compare HEAD and context")
    print("  diff_snapshot <old> <new> compare two snapshots")
    print("  diff_nodes <old_id> <new_id>  compare two commit nodes")
    print("  exit                     quit")


def print_tree(memory):
    tree = memory.history_tree_data()
    nodes = tree["nodes"]

    def format_node(node_id):
        node = nodes[node_id]
        labels = []

        if node["is_head"]:
            labels.append("HEAD")
        if node["snapshots"]:
            labels.append("snapshot: " + ", ".join(node["snapshots"]))

        label_text = ""
        if labels:
            label_text = " [" + " | ".join(labels) + "]"

        return f"{node_id}{label_text} ({node['message_count']} messages)"

    def walk(node_id, prefix="", is_last=True, is_root=False):
        if is_root:
            print(format_node(node_id))
            child_prefix = ""
        else:
            connector = "`-- " if is_last else "|-- "
            print(prefix + connector + format_node(node_id))
            child_prefix = prefix + ("    " if is_last else "|   ")

        children = nodes[node_id]["children"]
        for index, child_id in enumerate(children):
            walk(child_id, child_prefix, index == len(children) - 1)

    for index, root_id in enumerate(tree["roots"]):
        walk(root_id, "", index == len(tree["roots"]) - 1, is_root=True)


def print_context(memory):
    print("context:")

    for message in memory.context_data():
        print(message["index"], message["role"] + ":", message["content"])


def print_status(memory):
    data = memory.status_data()

    print("HEAD node:", data["head"])
    print("current branch:", data["current_branch"])
    print("commit nodes:", data["commit_count"])
    print("snapshots:", data["snapshot_count"])

    if data["commits_since_snapshot"] == 0:
        print("current HEAD is on a snapshot")
    else:
        print(f"{data['commits_since_snapshot']} commits since nearest snapshot; consider creating a snapshot")

    print("current context:")
    for message in data["context"]:
        print(" ", message["index"], message["role"] + ":", message["content"])


def print_snapshot_log(memory):
    print("snapshots:")

    for snapshot in memory.snapshot_log_data():
        print(f"{snapshot['name']} ({snapshot['created_at']}  {snapshot['message_count']}  messages)")
        print(f"   note:{snapshot['note']}")

        if snapshot["is_head"]:
            print("now in this snapshots:", snapshot["name"])


def print_history(memory):
    print("commits:")

    for node in memory.history():
        marker = "*" if node["is_head"] else " "
        snapshot_text = ", ".join(node["snapshots"]) if node["snapshots"] else "-"
        print(f"{marker} id={node['id']} parent={node['parent']} snapshots={snapshot_text}")


def print_diff(changes):
    if not changes:
        print("No change")
        return

    for change in changes:
        prefix = "+" if change["op"] == "add" else "-"
        print(prefix, change["role"] + ":", change["content"])


def print_validation(result):
    for error in result["errors"]:
        print("error:", error)

    for warning in result["warnings"]:
        print("warning:", warning)

    print("context validation finished")


def print_branches(memory):
    print("branches:")

    for branch in memory.branches_data():
        marker = "*" if branch["is_current"] else " "
        print(f"{marker} {branch['name']} -> {branch['head']}")
