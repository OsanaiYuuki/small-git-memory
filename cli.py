from core.git_memory import GitMemory
from core.storage import load_memory, save_memory


memory = GitMemory()


def help_info():
    print("commands:")
    print("  add <role> <content>     add a message")
    print("  remove <index>           remove message by index")
    print("  validate                 validate current context")
    print("  snapshot <name>          save current context,save a snapshot")
    print("  delete_snapshot <name>   delete a snapshot")
    print("  auto                     auto create a snapshot")
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


def run_cli(memory):
    while True:
        try:
            command = input("git memory> ")
        except KeyboardInterrupt:
            print()
            print("exit")
            break
        except EOFError:
            print()
            print("exit")
            break

        command = command.strip()

        if command == "":
            continue

        parts = command.split(" ", 2)

        if command == "exit":
            break

        elif command == "show":
            memory.show_context()

        elif command == "status":
            memory.status()

        elif command == "log":
            memory.log()

        elif command == "history":
            memory.history()

        elif command == "tree":
            print_tree(memory)

        elif command == "validate":
            memory.validate_context()

        elif parts[0] == "diff":
            if len(parts) == 1:
                memory.diff()
            else:
                print("usage:diff")

        elif parts[0] == "diff_nodes":
            if len(parts) != 3:
                print("usage: diff_nodes <old_id> <new_id>")
                continue

            try:
                old_id = int(parts[1])
                new_id = int(parts[2])
            except ValueError:
                print("node id must be a number")
                continue

            memory.diff_nodes(old_id, new_id)

        elif parts[0] == "diff_snapshot":
            if len(parts) == 3:
                memory.diff_snapshots(parts[1], parts[2])
            else:
                print("usage: diff_snapshot <old_snapshot> <new_snapshot>")

        elif parts[0] == "add":
            if len(parts) < 3:
                print("usage:add<role><content>")
                continue

            role = parts[1]
            content = parts[2]
            memory.add_message(role, content)

        elif parts[0] == "remove":
            if len(parts) < 2:
                print("usage:remove<index>")
                continue

            try:
                index = int(parts[1])
            except ValueError:
                print("index must be a number")
                continue

            memory.remove_message(index)

        elif parts[0] == "snapshot":
            if len(parts) < 2:
                print("usage:snapshot<name>")
                continue

            name = parts[1]
            memory.snapshot(name)

        elif parts[0] == "delete_snapshot":
            if len(parts) < 2:
                print("usage:delete_snapshot<name>")
                continue

            name = parts[1]
            memory.delete_snapshot(name)

        elif parts[0] == "rollback":
            if len(parts) < 2:
                print("usage:rollback<node_id>")
                continue

            try:
                node_id = int(parts[1])
            except ValueError:
                print("node_id must be a number")
                continue

            memory.rollback(node_id)

        elif parts[0] == "rollback_snapshot":
            if len(parts) < 2:
                print("usage:rollback_snapshot<name>")
                continue

            name = parts[1]
            memory.rollback_snapshot(name)

        elif command == "undo":
            memory.undo()

        elif command == "save":
            save_memory(memory)

        elif command == "auto":
            memory.auto_snapshot()

        elif command == "clear":
            memory.clear()

        elif command == "all_clear":
            confirm = input("clear all memory? type yes to confirm: ")

            if confirm == "yes":
                memory.clear()
                save_memory(memory)
            else:
                print("all clear cancelled")

        elif command == "load":
            load_memory(memory)

        elif command == "help":
            help_info()

        else:
            print("unknown command:", command)
