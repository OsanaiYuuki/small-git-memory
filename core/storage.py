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
        return False
    
    apply_data_to_memory(memory,data)

    print("loaded from", DATA_FILE)     

def validate_data(data):
    required_keys=["context","snapshots","head","commit_count"]
        #The key required for a valid JSON
        
    for key in required_keys:
        if key not in data:
            print("data file missing key:",key)
            return  False

    if not isinstance(data["context"],list):
        print("context must be a list")
        return False
    
    
    if not isinstance(data["snapshots"],dict):
        print("snapshots must be a dict")
        return False
    
    
    if data["head"] is not None and not isinstance(data["head"],str):
        print("head must be a string or None")
        return  False

    
    if not isinstance(data["commit_count"],int):
        print("commit_count must be an int")
        return False
    
    return True

def memory_to_data(memory):#这里指 把memory的属性抽象成一个方法 直接返回一个值 让data接收
    return{
        "context":memory.context,
        "snapshots":memory.snapshots,
        "head":memory.head,
        "commit_count":memory.commit_count
    }

def apply_data_to_memory(memory,data):#将data的数据加载到memory对象中 所以是load
    memory.context = data["context"]
    memory.snapshots = data["snapshots"]
    memory.head = data["head"]
    memory.commit_count = data["commit_count"]
