
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


def get_lcs(old,new):
    dp=lcs_table(old,new)

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

def show_diff(old_context,new_context):
        lcs=get_lcs(old_context,new_context)

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



