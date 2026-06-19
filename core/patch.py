from core.diff import get_lcs
from core.models import AddOp, DeleteOp, KeepOp, messages_from_data, patch_from_data


def make_patch(old_context,new_context): #op代表的是变化节点
    old_context=messages_from_data(old_context)
    new_context=messages_from_data(new_context)
    lcs=get_lcs(old_context,new_context)

    i = j = k = 0

    patch=[]

    while i<len(old_context) or j<len(new_context):

        if k<len(lcs) and i<len(old_context) and j<len(new_context)\
            and old_context[i] == lcs[k] and new_context[j] == lcs[k]:
                patch.append(KeepOp())
                i+=1
                j+=1
                k+=1


        elif i < len(old_context) and (k >= len(lcs) or old_context[i] != lcs[k]):
            msg = old_context[i]
            patch.append(DeleteOp(msg))
            i += 1
        else:
            msg = new_context[j]
            patch.append(AddOp(msg))
            j += 1

    return patch


def apply_patch(old_context,patch):
    old_context=messages_from_data(old_context)
    patch=patch_from_data(patch)
    result=[]
    i=0
    for op in patch:
        if isinstance(op, KeepOp):
            result.append(old_context[i])
            i+=1

        elif isinstance(op, AddOp):
            result.append(op.message)


        elif isinstance(op, DeleteOp):
            i+=1

    return result


def undo(new_context,patch):#undo下与apply相反
    new_context=messages_from_data(new_context)
    patch=patch_from_data(patch)
    result=[]
    i=0
    for op in patch:
        if isinstance(op, KeepOp):
            result.append(new_context[i])
            i+=1

        elif isinstance(op, AddOp):
            i+=1


        elif isinstance(op, DeleteOp):
            result.append(op.message)

    return result
