from core.git_memory import GitMemory
from core.storage import save_memory, load_memory

def help_info():
    print("commands:")
    print("  add <role> <content>     add a message")
    print("  remove <index>           remove message by index")
    print("  validate                 validate current context")
    print("  commit <name>            save current context")
    print("  auto                     auto commit current context")
    print("  rollback <node_id>       rollback to a commit node")
    print("  undo                     undo to parent node (撤销上一步)")
    print("  show                     show current context")
    print("  status                   show current status")
    print("  log                      show snapshots")
    print("  save                     save data to file")
    print("  clear                    Only clear memory")
    print("  all_clear                clear all memory")
    print("  load                     load data from file")
    print("  diff                     compare HEAD and context")
    print("  exit                     quit")


def run_cli(memory):
    while True:
        try:
            command=input("git memory> ")
        
        except KeyboardInterrupt:
            print()
            print("exit")
            break
        
        except EOFError:
            print()
            print("exit")
            break

        command=command.strip()#清洗输入的作用 去除字符串首尾的空白字符
        
        if command=="":
            continue

        parts=command.split(" ",2)

        if command =="exit":
            break

        elif command == "show":
            memory.show_context()

        elif command == "status":
            memory.status()   

        elif command == "log":
            memory.log()

        elif command == "validate":
            memory.validate_context()


        elif parts[0]=="diff": #the current workspace and HEAD.
            if len(parts) == 1:
                memory.diff()
            elif len(parts) == 3: #two historical snapshots
                memory.diff_snapshots(parts[1],parts[2])
            else:
                print("usage:diff[old_snapshot new_snapshot]")


        elif parts[0]=="add":
            if len(parts)<3:
                print("usage:add<role><content>")
                continue

            role=parts[1]
            content=parts[2]
            memory.add_message(role,content)

        elif parts[0] == "remove":
            if len(parts)<2:
                print("usage:remove<index>")
                continue

            try:
                index=int(parts[1])
            except ValueError:
                print("index must be a number")
                continue

            memory.remove_message(index)

        elif parts[0]=="commit":
            if len(parts)<2:
                print("usage:commit<name>")
                continue
            
            name=parts[1]
            memory.snapshot(name)

        elif parts[0]=="rollback":
            if len(parts)<2:
                print("usage:rollback<node_id>")
                continue

            try:
                node_id=int(parts[1])
            except ValueError:
                print("node_id must be a number")
                continue

            memory.rollback(node_id)

        elif command == "undo":
            memory.undo()

        elif command == "save":
            save_memory(memory)
        
        elif command == "auto":
            memory.auto_commit()

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
            print("unknown command:",command)

