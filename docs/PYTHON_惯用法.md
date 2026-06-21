# Python 惯用法

## 1. `__name__ == "__main__"`

用于区分文件是被直接运行，还是被其他模块 import。

```python
def main():
    print("hello")


if __name__ == "__main__":
    main()
```

直接运行该文件时会执行 `main()`；被 import 时不会自动执行。

## 2. 用函数包住入口逻辑

推荐把脚本入口写进 `main()`：

```python
def main():
    ...


if __name__ == "__main__":
    main()
```

这样方便测试，也避免 import 时产生副作用。

## 3. 小步提交

一个 commit 尽量只表达一件事：

- 修一个 bug
- 加一个小功能
- 重构一个局部
- 补一组测试

这样以后看历史会更清楚。

## 4. 先写清楚数据结构

当项目开始变复杂时，先把数据结构写清楚：

```python
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str
```

数据结构稳定后，逻辑会更容易测试。

## 5. 用测试保护行为

当一个功能已经能工作时，尽快写测试保护它。

尤其适合测试的地方：

- 保存 / 加载
- rollback
- diff
- patch apply / undo
- CLI 参数解析

## 6. 不急着抽象

一开始可以先写直白一点。

等重复出现、职责变清楚之后，再抽函数、拆模块、加类。

太早抽象容易把还没想明白的东西固定住。
