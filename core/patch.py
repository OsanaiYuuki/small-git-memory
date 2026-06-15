from core.diff import get_lcs

def make_patch(old_context,new_context): #op代表的是变化节点
    lcs=get_lcs(old_context,new_context)

    i = j = k = 0

    patch=[]

    while i<len(old_context) or j<len(new_context):
        
        if k<len(lcs) and i<len(old_context) and j<len(new_context)\
            and old_context[i] == lcs[k] and new_context[j] == lcs[k]:
                patch.append({"op":"keep"})
                i+=1
                j+=1
                k+=1
                

        elif i < len(old_context) and (k >= len(lcs) or old_context[i] != lcs[k]):
            msg = old_context[i]
            patch.append({"op": "delete", "message": msg})
            i += 1         
        else:
            msg = new_context[j]
            patch.append({"op": "add",    "message": msg} )
            j += 1

    return patch

def apply_patch(old_context,patch):
    result=[]
    i=0
    for op in patch:
        if op["op"] == "keep":
            result.append(old_context[i])
            i+=1

        elif op["op"] == "add":
            result.append(op["message"])
             

        elif op["op"]== "delete":
            i+=1
    
    return result
        
def undo(new_context,patch):#undo下与apply相反
    result=[]
    i=0
    for op in patch:
        if op["op"] == "keep":
            result.append(new_context[i])
            i+=1

        elif op["op"] == "add":
            i+=1
             

        elif op["op"]== "delete":
            result.append(op["message"])
    
    return result
        