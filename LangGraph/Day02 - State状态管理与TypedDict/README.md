# Day02 - State 状态管理与 TypedDict

State 是 LangGraph 的**核心**——它是各阶段之间传递、共享的数据容器。理解了 State，你就看懂了整个图的「血液」如何流动；不理解它，别的概念都悬在半空。本章围绕 GraphFlow 工作流，深入讲解如何用 `TypedDict` 定义 State、各字段类型的选择、以及最关键的 **Reducer（汇总策略）**——它决定了当多个节点写入同一字段时该如何合并。这是你理解 LangGraph 一切高级特性的地基。

## 学习目标

- 理解 State 是什么，节点如何读取输入并返回部分更新
- 用 `TypedDict` 定义结构化 State，掌握各字段类型的选择
- 透彻理解 Reducer 概念：默认覆盖 vs `Annotated + add` 累积
- 掌握 `add_messages` 内置 reducer 做消息累积
- 理解状态初始化与 partial state（节点只返回部分字段）
- 区分可变字段与不可变字段，能做出正确的字段设计决策

---

## 一、State 概念

**State 是在图的执行过程中，在节点之间传递的数据容器。**

工作方式非常直观：

1. 图以「初始状态」开始执行
2. 每个节点**读取** State 的输入字段
3. 节点返回对 State 的**部分更新**（一个 dict）
4. 图收集节点的更新，**合并**进当前 State
5. 下一个节点拿到合并后的 State 继续执行

```
初始State ──▶ Node A ──(返回dict:{"a":1})──▶ 合并State
                     ◀──────────────────┘
```

关键点：**节点不直接修改 State，而是返回"要改哪些字段"**，由框架统一合并。这样执行顺序、并行、持久化都更可控。

---

## 二、用 TypedDict 定义 State

LangGraph 用 `typing.TypedDict` 声明 State 的字段与类型。

```python
from typing import TypedDict

class State(TypedDict):
    input_text: str
    risk_level: str
```

### 字段类型标注

```python
class State(TypedDict):
    title: str                    # str
    count: int                    # int
    score: float                  # float
    enabled: bool                 # bool
    tags: list[str]               # list
    meta: dict[str, str]          # dict
```

### 嵌套 TypedDict

把相关字段分组为结构体，让 State 更清晰：

```python
class RiskScores(TypedDict):
    violence: int
    hate: int

class State(TypedDict):
    input_text: str
    scores: RiskScores            # 嵌套 TypedDict
```

### 类型检查

`TypedDict` 天然被静态类型检查器支持（Pylance / mypy）。字段名写错、类型写错、初始化缺字段都会在**编辑阶段**被标红，这是 LangGraph 能写出健壮代码的关键。

---

## 三、State 字段类型详解

| 类型 | 定义示例 | 默认合并行为 | 典型用途 |
| --- | --- | --- | --- |
| 标量 | `risk_level: str` | 覆盖（后写覆盖先写） | 单值结果、步骤标记 |
| 列表 | `tags: list[str]` | 覆盖 | 一次性写入的标签集合 |
| 字典 | `meta: dict[str, str]` | 覆盖 | 元信息 |
| 嵌套 TypedDict | `scores: RiskScores` | 覆盖 | 分组结构 |
| 累积列表 | `msgs: Annotated[list, add_messages]` | **追加/合并** | 消息历史、分析记录 |

> 除使用 Reducer 的字段外，其余字段默认是「覆盖」语义：后来的节点返回该字段时，直接覆盖旧值。

---

## 四、Reducer 概念（重点）

### 4.1 问题

当**多个节点返回同一个字段**时，如何合并？

```python
node1 返回 {"tags": ["安全"]}
node2 返回 {"tags": ["情感"]}
# tags 最终是 ["情感"]（覆盖）还是 ["安全","情感"]（累积）？
```

### 4.2 默认行为：直接覆盖

默认情况下，后写的覆盖先写的。`list` 也不例外——**默认没有 append**，整体被覆盖。

```python
class State(TypedDict):
    tags: list[str]          # 默认覆盖
```

最终 `tags` 只保留最后一个节点写入的值。

### 4.3 Annotated + add 累积

如果你想让列表**累积**而非覆盖，用 `Annotated` 标注一个 **Reducer**：

```python
from typing import Annotated, TypedDict
from operator import add

class State(TypedDict):
    tags: Annotated[list[str], add]   # 两个标签列表自动拼接
```

此时 node1 返回 `["安全"]`、node2 返回 `["情感"]`，最终 `tags == ["安全","情感"]`。

### 4.4 Reducer 的本质

**Reducer 是一个"无状态合并函数"**：接收（旧值，新值），返回合并后的值。

```
reducer(old_value, new_value) -> merged_value

operator.add:  ["安全"] + ["情感"] -> ["安全", "情感"]   # 拼接
add_messages:  消息列表如何追加/合并（见下）
```

什么时候用哪个？
| 需求 | 写法 |
| --- | --- |
| 覆盖 | 不加 Reducer（默认） |
| 列表拼接 | `Annotated[list, add]`（或 `operator.add`） |
| 消息累积 | `Annotated[list[BaseMessage], add_messages]` |

---

## 五、消息累积

对话历史、多步骤分析记录这类「反复追加」的场景，是 LangGraph 最常遇到的。内置的 **`add_messages` reducer** 专门处理消息列表。

```python
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # 追加/合并
```

```python
node1 返回 {"messages": ["[安全检测] 通过"]}
node2 返回 {"messages": ["[情感分析] 正面"]}
node3 返回 {"messages": ["[报告] 自动通过"]}
最终 messages == ["[安全检测] 通过", "[情感分析] 正面", "[报告] 自动通过"]
```

**add_messages 做了什么**：当返回的消息带的 `id` 与已有消息相同则**替换**，否则**追加**。即便后续我们换成 `list[BaseMessage]`（LangChain 消息对象），它也能按 id 正确合并。对 GraphFlow 而言，各分析步骤各自追加一条记录，最后汇总成完整的处理日志。

---

## 六、状态初始化与 partial state

### 6.1 初始化

在执行时传入初始状态：

```python
result = app.invoke({"input_text": "部分字段可省略",
                     "risk_level": "", "tags": []})
```

留给节点的空默认值通常是你的设计选择。

### 6.2 partial state（节点只返回部分字段）

节点**不必返回所有字段**，只返回它需要更新的字段即可：

```python
def detect_node(state: State) -> dict:
    return {"risk_level": "low"}     # 只返回部分字段
```

未返回的字段保持原值不变。

---

## 七、可变字段 vs 不可变字段

| 字段类型 | 语义 | 设计建议 |
| --- | --- | --- |
| 简单类型（str/int/bool/float） | 一次写入、后覆盖先 | 作单值结果、状态标记 |
| 列表 / 字典 | 默认覆盖；用 Reducer 累积 | 明确「覆盖 or 累积」后再选 |
| 需累积的列表 | `Annotated[list, add]` | 多处写同一列表时用 |
| 消息列表 | `Annotated[list, add_messages]` | 记录历史/日志时用 |

**设计建议**：动手前先想清楚每个字段是"谁写、写几次、要不要累积"，再决定是否加 Reducer。这能避免大量运行时困惑。

---

## 关键知识点总结

### 1. State 字段类型速查表

| 类型 | 定义 | 合并 |
| --- | --- | --- |
| 标量 | `x: str` | 覆盖 |
| 列表 | `x: list[str]` | 覆盖 |
| 字典 | `x: dict` | 覆盖 |
| 嵌套 | `x: RiskScores` | 覆盖 |
| 累积 | `Annotated[list, add]` | 拼接 |
| 消息 | `Annotated[list, add_messages]` | 追加/合并 |

### 2. 默认行为 vs Reducer 对比表

| | 默认 | 用 Reducer |
| --- | --- | --- |
| 声明 | `tags: list[str]` | `Annotated[list[str], add]` |
| 两节点各写1个 | `["情感"]`（覆盖） | `["安全","情感"]`（累积） |
| 适用 | 单次结果 | 多处累积 |

### 3. Annotated 语法速查

```python
from typing import Annotated
from operator import add
from langgraph.graph.message import add_messages

tags: Annotated[list[str], add]
messages: Annotated[list, add_messages]
# Annotated[类型, 合并函数]
```

### 4. add_messages 说明

- 追加未见过的消息；按 `id` 替换已存在的消息
- 最常用于 `messages: Annotated[list[BaseMessage], add_messages]` 记录对话/日志
- 可直接用于纯 `str` 列表（无 id 时全部追加）

---

## 代码文件说明

| 文件 | 内容 |
| --- | --- |
| `01_state_definition.py` | 用 TypedDict 定义含多种字段的 State 并演示初始化 |
| `02_reducer_basics.py` | 对比默认覆盖与 `Annotated+add` 累积 |
| `03_message_state.py` | `add_messages` 消息累积 vs 默认覆盖 |

---

## 常见坑

- **以为 list 默认会 append**：不会，默认整体覆盖
- **忘了加 `Annotated`**：需求是累积却写成 `tags: list[str]`，静默被覆盖
- **在非 reducer 字段里想要累积**：必须显式标注 reducer
- **TypedDict 字段名不一致**：静态检查器会立刻提示，善用编辑器

---

## 实战练习

### 练习 1：把标量字段设计成累积
GraphFlow 有多个分析节点都想「追加一句话结论」。先写出默认覆盖版本观察丢失，再改用 `Annotated[list, add]` 修改 `01` 中的 analysis 处理方式。

### 练习 2：记录消息日志
在 `03_message_state.py` 中新增第 4 个节点「存档 node」，也往 `messages` 追加一条，运行确认四条消息全部累积保留。

### 练习 3：给消息列表加 id 观察替换
把 `messages` 的元素换成带 `id` 的对象（或构造含 `id` 的 dict），验证 `add_messages` 在 id 相同时是「替换」而不是「再追加」。

---

## 下一步

状态是灵魂，节点与边是骨架。Day03 深入 **Node 与 Edge**——怎样定义一个执行操作/调用 LLM 的节点，以及如何用边组织它们的流转（含扇入扇出）。