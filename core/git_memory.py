import copy
from core.diff import show_diff
from datetime import datetime
from core.models import CommitNode, Message, Snapshot
from core.patch import make_patch, apply_patch

DEFAULT_CONTEXT=[
            Message("user", "comeback"),
            Message("assistant", "ok go")
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
        message=Message(role, content)
        self.context.append(message)
        self.commit()#每次添加自动保存
    
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
        print("remove:",message.role+":",message.content)

        self.validate_context()
        self.commit()#每次删除自动存档  this is good 

    
    def snapshot(self,name:str, note:str="")->None:#这是用来创建快照的方法 小存档或者贴纸
        if name in self.snapshots:
            print("The name already exists!")
            return
        
        self.snapshots[name]=Snapshot(
            name=name,
            node_id=self.head,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note=note,
            cached_context=copy.deepcopy(self.context)
        )
        print(f"snapshot created: {name} on node {self.head}")

        
    def delete_snapshot(self,name):
        if name == "__root__":
            print("root snapshot can not be deleted")
            return
        if name not in self.snapshots:
            print("snapshot not exist:",name)
            return
        del self.snapshots[name]
        print("snapshot deleted:",name)
        
        
    def auto_snapshot(self):#自动起名字
        index=1
        while True:
            name="checkpoint_"+str(index)

            if name not in self.snapshots:
                break
            index+=1
        self.snapshot(name)
        
                    
    
    def rollback(self,node_id:int)->None:
        if node_id not in self.commits:
            print("id is not exist",node_id)
            return

        self.head=node_id#移脚
        self.context=self._rebuild(node_id)#重建
        self.base=copy.deepcopy(self.context)#重置base

    def rollback_snapshot(self,name:str):
        if name not in self.snapshots:
            print("no name can rollback:",name)
            return
        
        node_id=self.snapshots[name].node_id
        self.rollback(node_id)


    def status(self):#显示函数负责打印结果。
        print("HEAD 节点:",self.head)
        print("树节点总数:",len(self.commits))
        print("书签(snapshot)数:",len(self.snapshots))

        drift=self.commits_since_snapshots()
        if drift == 0:
            print("当前正好在一个书签上")
        else:
            print(f"距离最近的书签已经 {drift} 次 commit —— 要不要打个书签(snapshot)保存一下?")

        print("当前 context:")
        for index, message in enumerate(self.context,start=1):
            print(" ",index,message.role+":",message.content)
    
    def show_context(self):
        print("context:")

        for index, message in enumerate(self.context,start=1):
            print(index,message.role+":",message.content)



    def log(self):#后进先出
        print("snapshots:")
        
        for name,snapshot in self.snapshots.items(): 
            messages_count=len(snapshot.cached_context) if snapshot.cached_context is not None else 0
            now_time=snapshot.created_at
            note=snapshot.note
            
            print(f"{name} ({now_time}  {messages_count}  messages)")
            print(f"   note:{note}")
            
           
            
            if snapshot.node_id == self.head:
                print("now in this snapshots:",name)

    def history(self):#展示历史节点，snapshot
       
        print("commits:")

        for node_id,node in self.commits.items():
            marker=" "#显示标记
            
            names=[]#显示snapshot分组
            for name,snapshot in self.snapshots.items():
                if snapshot.node_id==node_id:
                    names.append(name)
            if names:
                snapshot_text = ", ".join(names)
            else:
                snapshot_text = "-"
            if node_id == self.head:
                marker="*"
    
            commit_id=node.id
            parent=node.parent
            
            print(f"{marker} id={commit_id} parent={parent} snapshots={snapshot_text}")


    def diff(self):
        names,snapshot=self._find_nearest_snapshot()
        old_context=snapshot.cached_context
        if old_context is None:
            old_context=self._rebuild(snapshot.node_id)
        new_context=self.context

        print("diff from nearest snapshot:", ", ".join(names))

        show_diff(old_context,new_context)


    def diff_snapshots(self,old_name,new_name):
        if old_name not in self.snapshots:
            print("old snapshots not exist")
            return
        if new_name not in self.snapshots:
            print("new snapshots not exists")
            return
        
        old_snapshot=self.snapshots[old_name]
        new_snapshot=self.snapshots[new_name]
        old_context=old_snapshot.cached_context
        if old_context is None:
            old_context=self._rebuild(old_snapshot.node_id)
        new_context=new_snapshot.cached_context
        if new_context is None:
            new_context=self._rebuild(new_snapshot.node_id)

        print("diff",old_name,"->",new_name)
        show_diff(old_context,new_context)   


    def clear(self):#直接回退至初始状态
        self.snapshots={}
        self.commits={}
        self.next_id=0
        self.base = copy.deepcopy(DEFAULT_CONTEXT)
        self.context = copy.deepcopy(DEFAULT_CONTEXT)
        self._create_root()        # 造根 head=0 根snopshat
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

        for index,message in enumerate(self.context,start=1):
            if not isinstance(message.role, str):
                print("warnging:message",index,"has invalid role")

            if not isinstance(message.content, str):
                print("warnging:message",index,"has invalid content")

        print("context validation finished")

    
    def commit(self): #commit_patch
        if self.base == self.context:return

        patch=make_patch(self.base,self.context)

        new_id=self.next_id
        self.commits[new_id]=CommitNode(
            id=new_id,
            parent=self.head,
            patch=patch,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self.next_id += 1
        self.head=new_id # HEAD 移到新节点
        self.base=copy.deepcopy(self.context)

    
    def _create_root(self):#定义最初的根
        root_id=self.next_id #0

        self.commits[root_id]=CommitNode(
            id=root_id,
            parent=None, #根没有父亲 :(
            patch=[],
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.next_id += 1 #id迭代
        self.head = root_id#HEAD站在根上

        self.snapshots["__root__"]=Snapshot(
            name="__root__",
            node_id=root_id,   #就像贴纸 贴在根节点0上 作为索引
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note="System Root Node",
            cached_context=copy.deepcopy(DEFAULT_CONTEXT)
        )


    def _find_snapshot_by_node(self,node_id):#辅助 如何找到snapshot id
        for snap in self.snapshots.values():
            if node_id == snap.node_id and snap.cached_context is not None:
                return copy.deepcopy(snap.cached_context)
        return None
    

    def _rebuild(self,node_id):
        patches=[] #往上爬时收集 patch 倒序
        current=node_id

        while True:
            start_state=self._find_snapshot_by_node(current)#文本
            if start_state is not None:
                break #找到起点 snapshot
            node=self.commits[current] #没找到 把当前的patch收起来
            patches.append(node.patch)
            current=node.parent

        patches.reverse()#反转

        state=start_state
        for patch in patches:
            state=apply_patch(state,patch)

        return state
        

    def undo(self):#undo的颗粒度是每次对话 用户的输入 模型的输出
        parent =self.commits[self.head].parent  #当前节点的父亲
        if parent is None:                         #代表当前节点是根节点
            print("It is already in its initial state and cannot be undone")
            return
        self.rollback(parent)
        print("已撤销到节点",parent)

    
    def commits_since_snapshots(self):#这就是向上找parents的函数
        current=self.head  #当前的id
        count=0
        while True:
            snap=self._find_snapshot_by_node(current)
            if snap is not None:
                return count
            count +=1
            current=self.commits[current].parent


    def _find_nearest_snapshot(self): #从当前的self.head向上爬 直到遇见最近的snopshot 返回 #找最近书签的写法
        current=self.head

        while True:
            names=[]#这里存放的是一个commit节点 可能有很多snapshot贴纸的名字
            found_snapshot=None

            for name,snapshot in self.snapshots.items(): #遍历所有的snapshots
                if current == snapshot.node_id:
                    names.append(name)
                    found_snapshot=snapshot
           
            if names:    #如果列表不为空  == if len(names)>0
                return names,found_snapshot
            current = self.commits[current].parent #拿到父节点


    def children_by_parent(self) -> dict[int | None, list[int]]:# 把 parent 指针反转成 children 列表
        children = {}

        for node_id, node in self.commits.items():
            parent = node.parent

            if parent not in children:
                children[parent] = []

            children[parent].append(node_id)

        for child_ids in children.values():
                child_ids.sort()     

        return children
    

    def snapshots_by_node(self) -> dict[int, list[str]]:#把 snapshot name 反查到 node 上
        result = {}

        for name, snapshot in self.snapshots.items():
            node_id = snapshot.node_id

            if node_id not in result:
                result[node_id] = []

            result[node_id].append(name)

        for names in result.values():
            names.sort()
        return result
    
    def get_context_at(self, node_id: int) -> list[Message]:#点击树节点时显示 messages,diff 两个节点  给 node id，恢复完整上下文
        if node_id not in self.commits:
            raise ValueError("node_id does not exist")
        return copy.deepcopy(self._rebuild(node_id)) #返回 copy，避免外部改坏内部状态
    

    def history_tree_data(self) -> dict:# 组合成 UI/CLI 能直接使用的树数据
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
                
            
        
        








        

    


    

    
