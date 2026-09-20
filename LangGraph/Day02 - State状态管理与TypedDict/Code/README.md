# Day02 Code - State 状态管理与 TypedDict

本目录包含 Day02「State 状态管理与 TypedDict」的配套脚本：定义多种字段的 State、演示默认覆盖 vs Reducer 累积、验证 `add_messages` 消息累积。

## 环境准备

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
```

> 本章脚本不调用 LLM，无需 API Key。

## 文件说明

| 文件 | 用途 | 关键概念 |
| --- | --- | --- |
| `01_state_definition.py` | TypedDict 定义各种字段类型并初始化 | 标量/列表/字典/嵌套 TypedDict、Optional |
| `02_reducer_basics.py` | 对比默认覆盖与累积 | 默认覆盖、`Annotated[list, add]`、reducer |
| `03_message_state.py` | 消息列表累积 | `add_messages`、消息追加 vs 覆盖 |

## 运行方式

```bash
python 01_state_definition.py
python 02_reducer_basics.py
python 03_message_state.py
```

## 核心代码速览

### 1. 定义 State 与嵌套 TypedDict

```python
from typing import TypedDict

class RiskScores(TypedDict):
    violence: int
    hate: int

class State(TypedDict):
    input_text: str
    tags: list[str]
    scores: RiskScores
```

### 2. Reducer 累积列表

```python
from typing import Annotated
from operator import add

class State(TypedDict):
    tags: Annotated[list[str], add]   # ["安全"] + ["情感"] -> ["安全","情感"]
```

### 3. add_messages 消息累积

```python
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # 自动追加
```

## 常见问题

- **期望累积却只得到最后一项** → 确认字段写了 `Annotated[..., add]` 或 `add_messages`
- **列表被整体覆盖** → 默认就是覆盖语义，需累积必须显式标注 reducer
- **嵌套 TypedDict 不知道怎么写** → 见 `01` 的 `RiskScores` 示例

## 下一步

理解状态合并后，进入 Day03 学习 Node（节点）与 Edge（边）如何共同构成图的骨架。