# small-git-memory

small-git-memory 是一个学习性、实验性的 Git Memory 项目。

它尝试把 Git 的版本管理思想应用到 LLM 对话上下文管理中：把一次次对话变化记录成 commit 节点，把重要状态保存成 snapshot，并允许用户 rollback、undo、查看 history。

这个项目目前还不是成熟的生产级开源项目，而是一个正在成长中的学习项目。它的目标是探索：用户能不能像操作 Git 历史一样，操作自己与大模型交互的记忆路径。

---

## Why build this?

这个项目起源于一个很朴素的想法：

> 聊天软件里的消息都能撤回，为什么和 LLM 交互时，发出去的上下文就没有后悔药？

在和大模型交流、学习、反复试错的过程中，对话上下文其实是一条不断分叉的路径：

- 有些回答不满意，想撤回模型回答，让模型重新回答。
- 有些问题问错了，想退回上一轮重新问。
- 有些状态很重要，想打一个书签以后回来。
- 有些学习路径值得可视化，而不是散落在一堆聊天记录里。

small-git-memory 想成为这样一个窗口：

> 让用户更清楚地看见、保存、回退、分叉自己与 LLM 交互的历史。

现在它还很小，也很粗糙，但这个方向是它的核心。

---

## Current Features

目前已经实现的能力：

- 添加 LLM 风格消息：`{"role": "user", "content": "..."}`
- 删除消息
- 每次上下文变化自动记录为 commit 节点
- 使用 patch 保存上下文变化
- 使用 commit tree 保存历史
- HEAD 指向当前所在节点
- rollback 到任意 commit 节点
- undo 到父节点
- 创建命名 snapshot
- 根据 snapshot 名字 rollback
- 自动创建 checkpoint snapshot
- 查看 commit history
- 查看当前 status
- 查看 diff
- 对比两个 snapshot
- 对比两个 commit node
- 保存 / 加载本地 JSON 文件
- 对 JSON 数据做基础结构校验

---

## Quick Start

运行项目：

```bash
python main.py
```

进入命令行后可以输入：

```text
help
```

查看支持的命令。

---

## Basic Demo

下面是一个简单演示：

```text
add user A
snapshot mark_A
add assistant B
history
rollback_snapshot mark_A
show
```

可能看到的历史结构：

```text
commits:
  id=0 parent=None snapshots=__root__
* id=1 parent=0 snapshots=mark_A
  id=2 parent=1 snapshots=-
```

这表示：

- `id=0` 是根节点。
- `id=1` 是添加 `A` 后的状态。
- `mark_A` 这个 snapshot 贴在节点 1 上。
- `id=2` 是添加 `B` 后的状态。
- `rollback_snapshot mark_A` 会把 HEAD 移回节点 1。

---

## Core Concepts

### Commit Node

commit node 是项目里的历史节点。

每次 context 变化后，系统会记录一个 patch，并创建一个新的 commit node。

一个节点大概长这样：

```python
{
    "id": 1,
    "parent": 0,
    "patch": [...],
    "created_at": "..."
}
```

### HEAD

HEAD 表示当前站在哪个节点上。

rollback 和 undo 本质上不是删除历史，而是移动 HEAD。

### Snapshot

snapshot 是贴在某个 commit node 上的命名书签。

它面向用户，比如：

```text
snapshot first_answer
rollback_snapshot first_answer
```

### Rollback

rollback 会移动 HEAD，并根据历史 patch 重建 context。

```text
rollback 3
```

表示回到节点 3。

### Undo

undo 是沿着 parent 回退一步。

如果当前历史是：

```text
0 -> 1 -> 2
```

当前 HEAD 在 2，那么：

```text
undo
```

会回到 1。

### Branching

如果 rollback 到旧节点后继续添加消息，就会自然产生分叉。

例如：

```text
0
`-- 1
    |-- 2
    `-- 3
```

这表示节点 2 和节点 3 都是从节点 1 分出来的不同历史路径。

---

## Commands

当前 CLI 支持：

```text
add <role> <content>              add a message
remove <index>                    remove message by index
snapshot <name>                   create a named snapshot
delete_snapshot <name>            delete a snapshot
auto                              auto create a checkpoint snapshot
rollback <node_id>                rollback to a commit node
rollback_snapshot <name>          rollback to a snapshot
undo                              undo to parent node
show                              show current context
status                            show current status
log                               show snapshots
history                           show commit tree nodes
tree                              show commit tree
save                              save data to JSON
load                              load data from JSON
clear                             clear memory in current session
all_clear                         clear memory and save
validate                          validate current context
diff                              compare nearest snapshot and current context
diff_snapshot <old> <new>         compare two snapshots
diff_nodes <old_id> <new_id>      compare two commit nodes
exit                              quit
```

---

## Storage

当前项目使用本地 JSON 文件保存数据。

保存的数据包括：

- current context
- base context
- HEAD
- commit tree
- snapshots
- next id
- storage version

项目已经做了一些基础校验，例如：

- `head` 必须指向存在的 commit node
- commit node 必须有 `id / parent / patch / created_at`
- commit node 的 parent 必须存在
- snapshot 的 `node_id` 必须指向存在的 commit node
- JSON 读取后会把 commit key 从字符串转回整数

当前存储仍然很简单，还不是生产级存储。

---

## Project Status

当前状态：实验性学习项目。

已经具备一个小型 Git-like memory kernel，但还不成熟。

目前限制：

- 只支持本地 CLI
- 使用单文件 JSON 存储
- 没有并发保护
- 没有原子写文件
- 没有真实接入 LLM API
- `GitMemory` 类目前承担了较多职责，后续需要拆分
- CLI 命令体验还比较粗糙

---

## Roadmap

接下来可能会做：

- [x] 把现有测试整理成 pytest
- [x] 给存储数据增加 version 字段
- [ ] 完善 README 和使用演示
- [ ] 实现原子保存，避免 JSON 写坏
- [ ] 优化 CLI 命令命名和错误提示
- [ ] 把 commit / snapshot 抽成更清晰的数据模型
- [ ] 拆分 `GitMemory` 的职责
- [ ] 增加 token 统计
- [ ] 支持导入 / 导出 OpenAI 或 Claude 风格 messages
- [ ] 接入真实 LLM provider
- [ ] 未来探索可视化历史树

---

## Learning Notes

这个项目的主要目的不是一开始就做成成熟产品，而是在真实问题里学习后端开发：

- 数据模型设计
- 状态管理
- 增量 patch
- 树结构
- 持久化
- 数据校验
- CLI 交互
- 重构
- 测试

它还很小，但正在一步步长大。
