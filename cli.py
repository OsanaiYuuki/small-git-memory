from core.git_memory import GitMemory
from core.storage import load_memory, save_memory
from cli_render import (
    help_info,
    print_context,
    print_diff,
    print_history,
    print_branches,
    print_snapshot_log,
    print_status,
    print_tree,
    print_validation,
)


memory = GitMemory()


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
            print_context(memory)

        elif command == "status":
            print_status(memory)

        elif command == "log":
            print_snapshot_log(memory)

        elif command == "history":
            print_history(memory)

        elif command == "tree":
            print_tree(memory)

        elif command == "branches":
            print_branches(memory)

        elif command == "validate":
            print_validation(memory.validate_context())

        elif parts[0] == "diff":
            if len(parts) == 1:
                diff = memory.diff()
                print("diff from nearest snapshot:", ", ".join(diff["from"]))
                print_diff(diff["changes"])
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

            try:
                diff = memory.diff_nodes(old_id, new_id)
            except ValueError as error:
                print(error)
                continue
            print("diff", diff["from"], "->", diff["to"])
            print_diff(diff["changes"])

        elif parts[0] == "diff_snapshot":
            if len(parts) == 3:
                try:
                    diff = memory.diff_snapshots(parts[1], parts[2])
                except ValueError as error:
                    print(error)
                    continue
                print("diff", diff["from"], "->", diff["to"])
                print_diff(diff["changes"])
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

            try:
                removed_message = memory.remove_message(index)
            except ValueError as error:
                print(error)
                continue
            print("remove:", removed_message.role + ":", removed_message.content)

        elif parts[0] == "snapshot":
            if len(parts) < 2:
                print("usage:snapshot<name>[note]")
                continue

            name = parts[1]
            note = parts[2] if len(parts) == 3 else ""
            try:
                snapshot = memory.snapshot(name, note)
            except ValueError as error:
                print(error)
                continue
            print(f"snapshot created: {snapshot.name} on node {snapshot.node_id}")

        elif parts[0] == "branch":
            if len(parts) < 2:
                print("usage:branch<name>")
                continue

            try:
                branch = memory.branch(parts[1])
            except ValueError as error:
                print(error)
                continue
            print(f"branch created: {branch['name']} on node {branch['head']}")

        elif parts[0] == "checkout":
            if len(parts) < 2:
                print("usage:checkout<name>")
                continue

            try:
                node_id = memory.checkout(parts[1])
            except ValueError as error:
                print(error)
                continue
            print(f"switched to branch {parts[1]} on node {node_id}")

        elif parts[0] == "delete_snapshot":
            if len(parts) < 2:
                print("usage:delete_snapshot<name>")
                continue

            name = parts[1]
            try:
                memory.delete_snapshot(name)
            except ValueError as error:
                print(error)
                continue
            print("snapshot deleted:", name)

        elif parts[0] == "rollback":
            if len(parts) < 2:
                print("usage:rollback<node_id>")
                continue

            try:
                node_id = int(parts[1])
            except ValueError:
                print("node_id must be a number")
                continue

            try:
                memory.rollback(node_id)
            except ValueError as error:
                print(error)

        elif parts[0] == "rollback_snapshot":
            if len(parts) < 2:
                print("usage:rollback_snapshot<name>")
                continue

            name = parts[1]
            try:
                memory.rollback_snapshot(name)
            except ValueError as error:
                print(error)

        elif command == "undo":
            try:
                node_id = memory.undo()
            except ValueError as error:
                print(error)
                continue
            print("undone to node", node_id)

        elif command == "save":
            save_memory(memory)

        elif command == "auto":
            snapshot = memory.auto_snapshot()
            print(f"snapshot created: {snapshot.name} on node {snapshot.node_id}")

        elif command == "clear":
            memory.clear()
            print("memory cleared")

        elif command == "all_clear":
            confirm = input("clear all memory? type yes to confirm: ")

            if confirm == "yes":
                memory.clear()
                save_memory(memory)
                print("memory cleared")
            else:
                print("all clear cancelled")

        elif command == "load":
            load_memory(memory)

        elif command == "help":
            help_info()

        else:
            print("unknown command:", command)
