import copy

class GitMemory:
    def __init__(self):
        self.head=None
        self.context=[ 
            {"role":"user","content":"comeback"},
            {"role":"assistant","content":"ok go"}
        ]
        self.snapshots={}
        self.commit_count=0
    
    def add_message(self,role,content):
        message={"role":role,"content":content}
        self.context.append(message)
    
    def remove_message(self,index):
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

    
    def commit(self,name):
        if name in self.snapshots:
            print("The name already exists!")
            return
        
        self.snapshots[name]=copy.deepcopy(self.context)
        self.head=name
        self.commit_count+=1 
        
    def auto_commit(self):#自动起名字
        name="checkpoint_"+str(self.commit_count+1)
        self.commit(name)
        print("auto commit:",name)
    
    def rollback(self,name):#判断函数只返回结果 无需打印
        if name not in self.snapshots:
            print("snapshots not exist:",name)
            return
    
        self.context=copy.deepcopy(self.snapshots[name])
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
        return self.context!=self.snapshots[self.head]
    
    def log(self):#后进先出 乐事薯片
        print("snapshots:")
        for name in self.snapshots:
            print(" ",name)
            if name == self.head:
                print("now in this snapshots:",name)

    def diff(self):#这个函数是用来比较当前快照 和 context内容的区别 告诉变了什么
        if self.head is None:
            print("当前还没有创建快照,当前context都是新增内容")
            print(self.context)
            return
        
        old_context=self.snapshots[self.head]
        new_context=self.context

        print("diff from head:",self.head)
        self.show_diff(old_context,new_context)

    def diff_snapshots(self,old_name,new_name):
        if old_name not in self.snapshots:
            print("old snapshots not exist")
            return
        if new_name not in self.snapshots:
            print("new snapshots not exists")
            return
        
        old_context=self.snapshots[old_name]
        new_context=self.snapshots[new_name]

        print("diff",old_name,"->",new_name)
        self.show_diff(old_context,new_context)   

    def show_diff(self,old_context,new_context):
        lcs=self.get_lcs(old_context,new_context)

        i = j = k = 0


        if old_context == new_context:
            print("No change")
            return

        while i<len(old_context) or j<len(new_context):
            
            if k<len(lcs) and i<len(old_context) and j<len(new_context)\
                and old_context[i] == lcs[k] and new_context[j] == lcs[k]:
                    i+=1
                    j+=1
                    k+=1
            elif i < len(old_context) and (k >= len(lcs) or old_context[i] != lcs[k]):
                msg = old_context[i]
                print("-", msg["role"] + ":", msg["content"])
                i += 1         
            else:
                msg = new_context[j]
                print("+", msg["role"] + ":", msg["content"])
                j += 1


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

    @staticmethod
    def lcs_table(old,new):
        m=len(old)
        n=len(new)

        dp=[[0]*(n+1) for _ in range(m+1) ]

        for i in range(1,m+1):
            for j in range(1,n+1): 
                if old[i-1] == new[j-1]:
                    dp[i][j]=dp[i-1][j-1]+1
                else:
                    dp[i][j]=max(dp[i-1][j],dp[i][j-1])
        return dp        
    
    @staticmethod
    def get_lcs(old,new):
        dp=GitMemory.lcs_table(old,new)

        i=len(old)
        j=len(new)
        lcs=[]

        while i>0 and j>0:
            if old[i-1] == new[j-1]:
                lcs.append(old[i-1])
                i-=1
                j-=1
            elif dp[i-1][j] >= dp[i][j-1]:

                i-=1
            else:
                j-=1

        lcs.reverse()
        return lcs





    

    
