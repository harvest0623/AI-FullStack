# Day10 Code 说明 —— Reducer 进阶实战

本章用 `GraphFlow` 演示自定义 Reducer 与状态进阶。

## 文件导航

| 文件 | 类 | 演示内容 | 运行 |
|------|-----|---------|------|
| `01_custom_reducer.py` | `CustomReducer` | 自定义 reducer：去重/取最大/求和；多节点打分合并总分平均分 | `python 01_custom_reducer.py` |
| `02_add_messages_depth.py` | `AddMessagesDepth` | add_messages：追加/同 id 替换/RemoveMessage/Chunk 合并/自定义字段 | `python 02_add_messages_depth.py` |
| `03_state_inheritance.py` | `StateInheritance` | State 继承叠加字段、嵌套 TypedDict、BaseState 复用 | `python 03_state_inheritance.py` |

> 本目录示例不调用真实 LLM，可零 API Key 直接运行。

## 核心要点

### 1. 自定义 Reducer

```python
from typing import Annotated, TypedDict

def merge_unique(left: list, right: list) -> list:
    seen = set(left); out = list(left)
    for x in right:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

class State(TypedDict):
    entities: Annotated[list, merge_unique]
    total: Annotated[int, lambda a, b: a + b]
```

- reducer 签名固定为 `(left, right) -> merged`，必须无副作用。
- 多个节点写同一字段时都会被调用，实现精确合并。

### 2. add_messages 三种行为

| 行为 | 写法 | 结果 |
|------|------|------|
| 追加 | 新 id | 尾部追加 |
| 替换 | 同 id | 覆盖旧消息 |
| 删除 | `RemoveMessage(id)` | 移除该消息 |

### 3. 状态继承与嵌套

```python
class BaseState(TypedDict):
    input_text: str
    messages: Annotated[list, add_messages]

class AuditState(BaseState):        # 继承 -> 叠加字段
    risk: RiskInfo                  # 嵌套 TypedDict
    tags: list
```

## 进阶思考

1. 参数为 `left`/`right` 的 reducer 是"二元合并"，如何实现需要全局信息的"平均分"？参考示例里用`总分+数量`两字段的复合方案。
2. 思考 reducer 是纯函数的好处：便于测试、可复用、免外部状态。
3. 大量字段叠加时，优先考虑用继承 + 模块化 State 定义，保持清晰。