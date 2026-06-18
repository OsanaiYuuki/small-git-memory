import json
import os
from config import DATA_FILE

def save_memory(memory):
    data=memory_to_data(memory)

    with open(DATA_FILE,'w',encoding="utf-8")as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

    print("saved to",DATA_FILE)

def load_memory(memory):
    if not os.path.exists(DATA_FILE):#Processing file does not exist
        print("data file not exist:",DATA_FILE)
        return
    
    try:
        with open(DATA_FILE,"r",encoding="utf-8")as f:
            data=json.load(f)
    except json.JSONDecodeError:#Processing non-valid JSON
        print("data file is not valid json:",DATA_FILE)
        return
    
    if not validate_data(data):
        return 
    
    apply_data_to_memory(memory,data)

    print("loaded from", DATA_FILE)     


def validate_messages(messages):
    if not isinstance(messages, list):
        print("message is not a list:",messages)
        return False
    
    for message in messages:
        if not isinstance(message,dict):
            print("message is not a dict:",message)
            return False
        if "role" not in message or "content" not in message:
            print("message missing role or content",message)
            return False
    return True


def validate_data(data):
    required_keys=["context","base","head","commits","snapshots","next_id"]
        #The key required for a valid JSON

    for key in required_keys:
        if key not in data:
            print("data file missing key:",key)
            return  False

    if not isinstance(data["snapshots"],dict):
        print("snapshots must be a dict")
        return False

    if not isinstance(data["commits"],dict):
        print("commits must be a dict")
        return False
    
    if not isinstance(data["head"],int):
        print("head must be an int (node id)")
        return  False

    if not isinstance(data["next_id"],int):
        print("next_id must be an int")
        return False

    if not validate_data_commits(data):
        return False

    if not validate_messages(data["context"]):
        return False

    if not validate_messages(data["base"]):
        return False

    for name,snapshot in data["snapshots"].items():
        if not isinstance(snapshot,dict):
            print("snapshot should be a dict")
            return False

        required_snapshots_keys=["messages","created_at","note","node_id"] #对应snapshots结构

        for key in required_snapshots_keys:
            if key not in snapshot:
                print("snapshots file missing key:",key)
                return False
        if not isinstance(snapshot["node_id"], int):
            print("snapshot node_id must be an int:", name)
            return False

        if str(snapshot["node_id"]) not in data["commits"]:
            print("snapshot points to missing node:", name)
            return False
            

        if not validate_messages(snapshot["messages"]):
            print("snapshots is invalid",snapshot)
            return False

    return True

def memory_to_data(memory):#把memory的属性抽象成一个dict返回 让data接收
    return{
        "context":memory.context,
        "base":memory.base,
        "head":memory.head,
        "commits":memory.commits,
        "snapshots":memory.snapshots,
        "next_id":memory.next_id
    }

def apply_data_to_memory(memory,data):#将data的数据加载到memory对象中 所以是load
    memory.context   = data["context"]
    memory.base      = data["base"]
    memory.head      = data["head"]
    memory.snapshots = data["snapshots"]
    memory.next_id   = data["next_id"]
    memory.commits   ={int(k): v for k, v in data["commits"].items()} # 只有 commits 的键要从字符串转回整数

def validate_data_commits(data):
    required_commit_key=["id","parent","patch","created_at"]

    if str(data["head"])not in data["commits"]:
        print("head node not exist")
        return False
    for commit_id,node in data["commits"].items():
        if not isinstance(node,dict):
            print("commit node must be a dict:",commit_id)
            return False
        
        for key in required_commit_key:
            if key not in node:
                print("commit missing key:",key)
                return False
        if not isinstance(node["id"], int):
            print("commit id must be an int:", commit_id)
            return False

        if str(node["id"]) != commit_id:
            print("commit key and id mismatch:", commit_id)
            return False

        if not isinstance(node["patch"], list):
            print("commit patch must be a list:", commit_id)
            return False

        parent = node["parent"]

        if parent is not None and not isinstance(parent, int):
            print("commit parent must be None or int:", commit_id)
            return False

        if parent is not None and str(parent) not in data["commits"]:
            print("commit parent not exist:", commit_id)
            return False

    return True
