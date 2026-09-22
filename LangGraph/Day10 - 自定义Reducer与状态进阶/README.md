# Day10 - 自定义Reducer与状态进阶

> 当多个节点往同一个字段写结果时，到底该"覆盖"还是"累积"？Reducer 就是状态合并的最终裁判。

## 本章简介

默认情况下，多个节点返回同一个字段时，LangGraph 采用"**后写覆盖先写**"。但真实场景往往需要更精确的合并策略：多条分析结果要**求和**、多路抽取的实体要**去重**、多段消息要**按序累积**。

Reducer 正是为此而生：通过 `Annotated[type, reducer_func]`，我们可以为每个状态字段定制自己的合并规则。本章深化 `add_messages`，并探索自定义聚合逻辑、状态嵌套与继承，最后用一个多节点合并的实战把它们串起来——让 `GraphFlow` 的多个打分节点结果能够有序、精确地合并进同一个状态字段。

---

## 学习目标

学完本章，你应该能：

- [ ] 复述默认 reducer 与 `add_messages`/`operator.add` 的差异
- [ ] 用 `Annotated[type, func]` 编写自定义 reducer 合并两个字段值
- [ ] 实现去重、取最新、取最大/最小、求和/计数、dict 合并等聚合逻辑
- [ ] 深入理解 `add_messages` 的追加 / 同 id 替换 / id 删除行为
- [ ] 用 nested TypedDict 构造嵌套字段，用 State 继承复用公共字段
- [ ] 区分 reducer 与直接赋值的差异，合理规划字段合并策略

---

## 理论知识讲解

### 一、Reducer 回顾

再次明确三种典型状态字段的合并行为：

| 定义 | 合并行为 | 典型场景 |
|------|---------|---------|
| `field: str` | 覆盖（后写覆盖先写） | 最终结论、单值结果 |
| `Annotated[list, add_messages]` | 消息追加 / 同 id 替换 | 对话消息、审核历史 |
| `Annotated[list, operator.add]` | 列表拼接 | 多轮抽取的列表累加 |

---

### 二、自定义 Reducer（重点）

#### 1. 语法语法

```python
from typing import Annotated, TypedDict

def merge_scores(left: dict, right: dict) -> dict:
    """把新旧 scores 合并。"""
    return {**left, **right}

class State(TypedDict):
    scores: Annotated[dict, merge_scores]   # 指定 reducer 函数
```

#### 2. reducer 的输入与输出

**`reducer_func(left, right) -> merged`**
- `left`：当前已有的值（旧值）
- `right`：新节点要写入的值（新值）
- 返回：合并后的最终值

要点：**无状态合并函数**，只依赖传入的 `left` / `right`，不读取外部变量。LangGraph 在每次节点写回字段时调用它。

---

### 三、自定义聚合逻辑

| 逻辑 | reducer 函数示例 |
|------|-----------------|
| **去重** | `lambda l, r: l + [x for x in r if x not in l]` |
| **取最新** | `lambda l, r: r`（等价覆盖） |
| **取最大** | `lambda l, r: max(l, r)` |
| **取最小** | `lambda l, r: min(l, r)` |
| **取平均/求和** | 数组场景：`lambda l, r: (l or []) + r` 再外部统计 |
| **dict 合并** | `lambda l, r: {**l, **r}` |
| **计数** | `lambda l, r: l + r`（数值累加） |

```python
def merge_unique(left: list, right: list) -> list:
    """在合并时去重，保持顺序。"""
    seen = set(left)
    out = list(left)
    for x in right:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out
```

---

### 四、add_messages 详解

`add_messages` 是消息累积极其核心的 reducer，行为有三类：

| 行为 | 触发条件 | 说明 |
|------|---------|------|
| **append 追加** | 消息 id 不存在 | 直接追加到列表尾部 |
| **改写 / 替换** | 消息 id 相同 | 用新消息替换同 id 的旧消息 |
| **delete 删除** | 同 id 且内容为 `RemoveMessage` | 删除指定 id 的消息 |

此外：
- 同一节点的连续性流式消息（部分 chunk）会**合并为一条完整消息**（`AIMessageChunk` 合并）。
- 消息可以带自定义字段（`additional_kwargs` 等），保持原有结构。

```python
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

# 追加：新 id
add_messages([], [HumanMessage(content="hi")])
# 同 id 替换
m = HumanMessage(content="v1", id="m1")
add_messages([m], [HumanMessage(content="v2", id="m1")])  # 结果只保留 v2
# 删除
add_messages([m], [RemoveMessage(id="m1")])               # 结果为空
```

---

### 五、状态嵌套与继承

#### 1. 字段类型可嵌套 TypedDict

```python
class AuditMeta(TypedDict):
    risk_level: str
    score: Annotated[int, lambda a, b: max(a, b)]

class State(TypedDict):
    meta: AuditMeta           # 字段类型本身就是结构化的
```

#### 2. State 类可继承（叠加字段）

```python
class BaseState(TypedDict):
    input_text: str

class AuditState(BaseState):          # 继承 BaseState 的字段
    risk_level: str
    messages: Annotated[list, add_messages]
```

> `AuditState` 同时拥有 `input_text`、`risk_level`、`messages`，便于在多个子图间复用公共字段 —— 这就是 `BaseState` 的复用价值。

---

### 六、reducer 与直接赋值的差异

- 节点直接返回某字段 → 走 reducer（若无 reducer 则默认覆盖）。
- 有些场合希望**覆盖 reducer**，可用 `Command` 精确更新：

```python
from langgraph.types import Command

def node(state):
    return Command(update={"messages": [final_msg]})  # 强制以该值注入
```

> 实战准则：**默认用 reducer 表达合并意图；确需打破规则时用 `Command` 显式覆盖**，并加注释说明原因。

---

### 七、实战：多条分析结果按规则合并

- 多节点返回 `scores` → 用均值/求和 reducer 合并。
- 多节点提取 `entities` → 去重合并。
- 多节点产生 `messages` → `add_messages` 有序累积。

```python
def merge_entities(left: list, right: list) -> list:
    return list(dict.fromkeys(left + right))   # 去重保序

class State(TypedDict):
    entities: Annotated[list, merge_entities]
    total_score: Annotated[int, lambda a, b: a + b]
    messages: Annotated[list, add_messages]
```

---

## 代码文件说明

| 文件 | 类 | 说明 |
|------|-----|------|
| `Code/01_custom_reducer.py` | `CustomReducer` | 自定义 Reducer：`Annotated[type, func]`、新旧值合并、去重/取最大/取平均聚合；多个打分节点合并总分 |
| `Code/02_add_messages_depth.py` | `AddMessagesDepth` | add_messages 深度：追加 / 同 id 替换 / 删除 / chunk 合并 / 自定义消息字段；节点消息有序累积 |
| `Code/03_state_inheritance.py` | `StateInheritance` | 状态继承与嵌套：类继承叠加字段、嵌套 TypedDict、复杂结构化状态、BaseState 复用 |
| `Code/README.md` | - | Reducer 进阶指南：自定义 reducer 教程、聚合模板、add_messages 全解、状态设计、性能考虑 |

---

## 关键知识点总结

### 自定义 reducer 语法速查

```python
Annotated[type, reducer_func]
def reducer_func(left, right) -> merged: ...
```

| reducer | 作用 |
|---------|------|
| `merge_unique` | 合并去重 |
| `max` / `min` | 取极值 |
| `lambda a, b: a + b` | 求和/计数 |
| `lambda a, b: {**a, **b}` | dict 合并 |
| `add_messages` | 消息累积 |

### add_messages 行为对比

| 操作 | 结果 |
|------|------|
| 新 id 消息 | 追加到尾部 |
| 同 id 消息 | 替换旧消息 |
| `RemoveMessage(id)` | 删除该消息 |
| 流式 chunk | 自动合并为一条完整消息 |

### 状态继承模式

```python
class BaseState(TypedDict): ...
class AuditState(BaseState): ...   # 叠加字段,复用公共结构
```

### reducer 使用决策表

| 需求 | 推荐写法 |
|------|---------|
| 单值最终结果 | 直接 `field: str`（覆盖） |
| 多轮消息 | `Annotated[list, add_messages]` |
| 列表拼接 | `Annotated[list, operator.add]` |
| 去重 | 自定义 `merge_unique` |
| 极值/求和 | 自定义（`max`、`a+b`） |
| 覆盖某次累积 | `Command(update={...})` |

---

## 实战练习

1. **多节点打分合并**：让 `GraphFlow` 的三个分析节点（内容安全 / 情绪 / 主题）分别产出 0-10 分，用 reducer 计算总分与平均分写入 `summary` 字段。
2. **实体去重聚合**：创建三个抽取节点（人名 / 组织 / 地点），用去重 reducer 汇总进统一实体列表并保序输出。
3. **状态复用重构**：把 `GraphFlow` 拆成 `BaseAuditState`（涉及输入文本与消息）+ `ExtendedState`（风险分/实体），用继承消除重复字段。

---

## 参考阅读

- [LangGraph 官方文档 - Reducers](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers)
- [LangGraph 官方文档 - Messaging](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/)
- [LangChain 官方文档 - Messages](https://python.langchain.com/docs/concepts/messages/)