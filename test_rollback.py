import sys
sys.stdout.reconfigure(encoding="utf-8")

import copy
from core.git_memory import GitMemory

m = GitMemory()
print("初始 head:", m.head)                       # 0 (根)
print("初始 commits:", list(m.commits.keys()))     # [0]
print()

# --- 准备：边造节点，边把每一步的「真实 context」记下来当标准答案 ---
expected = {}
expected[0] = copy.deepcopy(m.context)   # 根(节点0)的状态 = DEFAULT_CONTEXT

m.add_message("user", "第一句")
m.commit()                               # 造出节点1
expected[m.head] = copy.deepcopy(m.context)

m.add_message("assistant", "第二句")
m.commit()                               # 造出节点2
expected[m.head] = copy.deepcopy(m.context)

m.add_message("user", "第三句")
m.commit()                               # 造出节点3
expected[m.head] = copy.deepcopy(m.context)

print("造完 commits:", list(m.commits.keys()))     # [0,1,2,3]
print("现在 head:", m.head)                         # 3
print("各节点应有的消息数:", {k: len(v) for k, v in expected.items()})
print()

# --- 测试1：rollback 非法节点，head 与 context 都不变 ---
head_before = m.head
ctx_before = copy.deepcopy(m.context)
m.rollback(999)
print("[测试1] rollback(999) 非法")
print("  head 不变:", m.head == head_before, "✅" if m.head == head_before else "❌")
print("  context 不变:", m.context == ctx_before, "✅" if m.context == ctx_before else "❌")
print()

# --- 测试2：逐个 rollback 到每个节点，验证重建出的 context == 标准答案 ---
print("[测试2] 逐个 rollback，验证重建内容正确")
for target in [0, 1, 2, 3]:
    m.rollback(target)
    ok_head = m.head == target
    ok_ctx = m.context == expected[target]
    ok_base = m.base == m.context        # 铁律：base 跟 context 同步
    mark = "✅" if (ok_head and ok_ctx and ok_base) else "❌"
    print(f"  rollback({target}): head={m.head} 内容对={ok_ctx} base同步={ok_base} {mark}")
    if not ok_ctx:
        print("     期望:", [x["content"] for x in expected[target]])
        print("     实际:", [x["content"] for x in m.context])
