# small-git-memory

small-git-memory 是一个学习性、实验性的 Git Memory 项目。

它把 Git 的一些核心想法借到 LLM 对话上下文管理里：每一次上下文变化都会形成一个 commit node，重要状态可以贴上 snapshot，用户可以查看历史、对比差异、回退到旧节点，也可以从旧节点继续走出新的分支。

换句话说，它不是在做一个完整的聊天产品，而是在探索一个问题：

> LLM 对话上下文能不能像 Git 历史一样被保存、比较、回退和分叉？

目前它还是一个本地 CLI 学习项目，不是生产级 memory system。但它已经有一个小而完整的 Git-like memory kernel，可以用来理解 patch、tree、snapshot、rollback、storage 和测试这些后端概念。

---

## Why

这个项目一开始来自一个很朴素的想法：

> 聊天里消息都能撤回，为什么和大模型交互时，发出去的上下文就没有后悔药？

和 LLM 一起学习、写代码、反复试错时，上下文其实不是一条直线。它更像一棵树：

- 有些回答不满意，想回到旧状态重新问。
- 有些问题问错了，想撤回几步再继续。
- 有些状态很重要，想打一个书签。
- 有些探索路径走偏了，但也不想直接删掉。

small-git-memory 想做的就是这件小事：让这条“和模型一起走过的路”能被看见、保存、回退和比较。

它还很小，但方向我挺喜欢。像是给上下文装了一个迷你时间机器。

---

## What It Can Do

当前已经支持：

- 添加 LLM 风格消息：`{"role": "user", "content": "..."}`
- 删除消息
- 每次上下文变化自动创建 commit node
- 用 patch 记录上下文增量变化
- 用 commit tree 保存历史
- 用 HEAD 表示当前所在节点
- rollback 到任意 commit node
- undo 到父节点
- 创建带 note 的 snapshot
- 根据 snapshot 名字 rollback
- 创建命名 branch
- checkout 到某个 branch 的 HEAD
- 查看所有 branch
- 导出 OpenAI messages JSON
- 导入 OpenAI messages JSON
- 导出 Markdown transcript
- 自动创建 checkpoint snapshot
- 查看 commit history
- 查看树形 history
- 查看当前 status
- 对比当前 context 和最近 snapshot
- 对比两个 snapshot
- 对比两个 commit node
- 保存 / 加载本地 JSON 文件
- 原子保存，降低 `gitmemory.json` 写坏风险
- 对存储 JSON 做基础结构校验
- 使用 pytest 覆盖核心行为

---

## Quick Start

运行：

```bash
python main.py
```

进入 CLI 后输入：

```text
help
```

查看所有命令。

运行测试：

```bash
pytest -q
```

---

## Basic Demo

```text
add user A
snapshot mark_A first stable point
add assistant B
history
log
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

含义是：

- `id=0` 是根节点。
- `id=1` 是添加 `A` 后的状态。
- `mark_A` 是贴在节点 1 上的 snapshot。
- `id=2` 是添加 `B` 后的状态。
- `rollback_snapshot mark_A` 会把 HEAD 移回节点 1。

如果你 rollback 到旧节点后继续 `add`，就会自然产生分支。

---

## Core Concepts

### Context

项目管理的是一个 LLM 风格的上下文列表：

```python
[
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": "hi"}
]
```

内部会把这些消息转换为 `Message` dataclass，方便校验、保存和 patch。

### Commit Node

commit node 是历史树里的一个节点。

每次 context 变化后，系统会比较旧 context 和新 context，生成一个 patch，并创建一个新的 commit node：

```python
{
    "id": 1,
    "parent": 0,
    "patch": [...],
    "created_at": "..."
}
```

### HEAD

HEAD 表示当前站在哪个 commit node 上。

rollback 和 undo 不会删除历史，它们只是移动 HEAD，然后根据 patch 重建当前 context。

### Snapshot

snapshot 是贴在 commit node 上的命名书签。

它可以带 note：

```text
snapshot first_answer this answer is worth keeping
```

之后可以查看：

```text
log
```

也可以回到它：

```text
rollback_snapshot first_answer
```

### Patch

patch 记录一次 context 变化里哪些消息被保留、添加或删除。

目前 patch operation 有三类：

- `keep`
- `add`
- `delete`

这不是为了追求最高性能，而是为了把“上下文如何变化”这件事讲清楚、测清楚。

---

## Commands

当前 CLI 支持：

```text
add <role> <content>              add a message
remove <index>                    remove message by index
snapshot <name> [note]            create a named snapshot with optional note
delete_snapshot <name>            delete a snapshot
auto                              auto create a checkpoint snapshot
branch <name>                     create a branch at current HEAD
checkout <name>                   switch to a branch HEAD
branches                          show all branches
export openai <file>              export current context as OpenAI messages JSON
import openai <file>              import OpenAI messages JSON
export markdown <file>            export current context as Markdown
rollback <node_id>                rollback to a commit node
rollback_snapshot <name>          rollback to a snapshot
undo                              undo to parent node
show                              show current context
status                            show current status
log                               show snapshots and notes
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

项目默认把数据保存到：

```text
gitmemory.json
```

保存内容包括：

- current context
- base context
- HEAD
- commit tree
- snapshots
- branches
- current branch
- next id
- storage version

保存时会先写入同目录临时文件，然后用 `os.replace()` 原子替换正式文件。这样可以减少写入中断时把 `gitmemory.json` 写坏的风险。

读取时会做基础结构校验，例如：

- `head` 必须指向存在的 commit node
- commit node 必须包含 `id / parent / patch / created_at`
- commit node 的 parent 必须存在
- snapshot 的 `node_id` 必须指向存在的 commit node
- commit key 从 JSON 读取后会从字符串转回整数

---

## Project Structure

```text
core/
  diff.py          LCS diff and display
  git_memory.py    main memory kernel
  messages_io.py   import/export helpers for OpenAI JSON and Markdown
  models.py        dataclasses and data conversion
  patch.py         make/apply/undo patch
  storage.py       JSON storage, migration, validation, atomic save

tests/
  test_cli.py
  test_gitmemory_tree.py
  test_make_patch.py
  test_messages_io.py
  test_patch.py
  test_record.py
  test_rollback.py
  test_storage.py

cli.py             interactive command parser
cli_render.py      CLI output rendering helpers
main.py            entry point
config.py          local config
```

---

## Project Status

当前状态：实验性学习项目。

已经比较完整的部分：

- Git-like commit tree
- named branch
- import / export messages
- snapshot / rollback / undo
- patch 生成与回放
- 本地 JSON 存储
- 存储版本字段和迁移
- 原子保存
- pytest 测试

还比较粗糙的部分：

- CLI 交互体验还很朴素
- `GitMemory` 类职责偏多，后续可以继续拆
- 目前还没有真实接入 LLM provider
- 还没有图形化 history tree
- 没有并发写入保护

---

## Roadmap

接下来可能会做：

- [x] 整理 pytest 测试
- [x] 给存储数据增加 version 字段
- [x] 实现原子保存，避免 JSON 写坏
- [x] snapshot 支持 note，并在 log 中显示
- [x] 支持简单 named branch / checkout
- [x] 支持导入 / 导出 OpenAI 风格 messages
- [x] 支持导出 Markdown transcript
- [ ] 优化 CLI 命令命名和错误提示
- [ ] 拆分 `GitMemory` 的职责
- [ ] 支持 Claude 风格 messages
- [ ] 接入真实 LLM provider
- [ ] 探索可视化历史树

---

## Notes

这个项目不是为了从第一天就变成成熟产品。

它更像一个练习场：用一个真实的小问题，把数据模型、状态管理、patch、树结构、持久化、校验、CLI、重构和测试都串起来。

小小的，但会继续长大。
