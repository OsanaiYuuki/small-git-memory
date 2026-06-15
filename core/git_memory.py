import copy
from core.diff import show_diff
from datetime import datetime
from core.patch import make_patch

DEFAULT_CONTEXT=[ 
            {"role":"user","content":"comeback"},
            {"role":"assistant","content":"ok go"}
        ]

class GitMemory:
    def __init__(self):
        
       
        self.snapshots={} #书签
        
        self.commits={}#树容器
        self.next_id=0#id 发送器
        self.base=copy.deepcopy(DEFAULT_CONTEXT)
        self.context=copy.deepcopy(DEFAULT_CONTEXT)

        self._create_root()   

    
    def add_message(self,role:str,content:str)->None:
        message={"role":role,"content":content}
        self.context.append(message)
    
    def remove_message(self,index:int)->None:
        if len(self.context) == 0:
            print("No messages can be deleted")
            return

        real_index=index-1

        if real_index <0 or real_index >=len(self.context):
            print("message index out of range",index)
            return
        
        removed_message=self.context.pop(real_index)
        message=removed_message
        print("remove:",message["role"]+":",message["content"])

        self.validate_context()

    
    def snapshot(self,name:str, note:str="")->None:
        if name in self.snapshots:
            print("The name already exists!")
            return
        
        self.snapshots[name]={
            "messages": copy.deepcopy(self.context),
            "created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note":note,
            "node_id":self.head
        }
        
        
        
    def auto_commit(self):#自动起名字
        name="checkpoint_"+str(len(self.snapshots))
        self.snapshot(name)
        print("auto commit:",name)
    
    def rollback(self,name:str)->None:#判断函数只返回结果 无需打印
        if name not in self.snapshots:
            print("snapshots not exist:",name)
            return
    
        self.context=copy.deepcopy(self.snapshots[name]["messages"])
        self.head=name

    def status(self):#显示函数负责打印结果。
        print("head",self.head)
        print("context",self.context)

        if self.is_dirty():
            print("偏离")
            self.diff()
        else:
            print("没偏离")
    
    def show_context(self):
        print("context:")

        for index, message in enumerate(self.context,start=1):
            print(index,message["role"]+":",message["content"])



    def is_dirty(self): #is_dirty的意思是 true为偏离 
                #is_dirty的意思是判断当前context有无偏离head指向的快照
        if self.head is None:
            return len(self.context)>0
        return self.context!=self.snapshots[self.head]["messages"]
    
    def log(self):#后进先出
        print("snapshots:")
        
        for name in self.snapshots:
            snapshot=self.snapshots[name]
            messages_count=len(snapshot["messages"])
            now_time=snapshot["created_at"]
            note=snapshot["note"]
            
            print(f"{name} ({now_time}  {messages_count}  messages)")
            print(f"   note:{note}")
            
           
            
            if name == self.head:
                print("now in this snapshots:",name)

    def diff(self):#这个函数是用来比较当前快照 和 context内容的区别 告诉变了什么
        if self.head is None:
            print("当前还没有创建快照,当前context都是新增内容")
            print(self.context)
            return
        
        old_context=self.snapshots[self.head]["messages"]
        new_context=self.context

        print("diff from head:",self.head)
        show_diff(old_context,new_context)


    def diff_snapshots(self,old_name,new_name):
        if old_name not in self.snapshots:
            print("old snapshots not exist")
            return
        if new_name not in self.snapshots:
            print("new snapshots not exists")
            return
        
        old_context=self.snapshots[old_name]["messages"]
        new_context=self.snapshots[new_name]["messages"]

        print("diff",old_name,"->",new_name)
        show_diff(old_context,new_context)   


    def clear(self):
        self.head=None
        self.context=[]
        self.snapshots={}
        self.commit_count=0
        print("memory cleared")

    def has_user_message(self):
        for message in self.context:
            if message.get("role") == "user":
                return True
        return False

    def has_assistant_message(self):
        for message in self.context:
            if message.get("role") == "assistant":
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

        for index,message in enumerate(self.context,start=1):
            if "role" not in message:
                print("warnging:message",index,"has no role")
            
            if "content" not in message:
                print("warnging:message",index,"has no content")

        print("context validation finished")

    
    def commit(self): #commit_patch
        if self.base == self.context:return

        patch=make_patch(self.base,self.context)

        new_id=self.next_id
        self.commits[new_id]={
            "id": new_id,
            "parent":self.head,
            "patch":patch,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.next_id += 1
        self.head=new_id # HEAD 移到新节点
        self.base=copy.deepcopy(self.context)

    
    def _create_root(self):
        root_id=self.next_id #0

        self.commits[root_id]={
            "id":root_id,
            "parent":None, #根没有父亲 :(
            "patch":[],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.next_id += 1 #id迭代
        self.head = root_id#HEAD站在根上

        self.snapshots["__root__"]={
            "messages":copy.deepcopy(DEFAULT_CONTEXT),
            "created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note":"System Root Node",
            "node_id":root_id   #就像贴纸 贴在根节点0上 作为索引
        }



        

    


    

    
