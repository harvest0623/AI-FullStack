# Day03 - Node 节点与 Edge 边

Node 执行操作，Edge 定义流转——节点和边共同构成图的**骨架**。任何一个 LangGraph 程序，你都可以把它拆成一张「节点做什么、边怎么走」的表：节点是工作的执行者，边是工作的交接者。本章逐个拆解节点的定义规范（纯函数 / 调用 LLM / async / 返回部分字段），讲透普通边与入口/出口（`START` / `END`）的用法，并引入 **fan-out（扇出）** 与 **fan-in（扇入）** 的并行与汇集行为。

## 学习目标

- 掌握 Node 的标准签名与返回值约定，写出规范的节点函数
- 能定义纯函数节点、调用 LLM 的节点、async 节点
- 理解并正确使用 `add_edge` / `set_entry_point` / `set_finish_point` 以及 `START` / `END`
- 理解节点返回值的合并规则与 partial state
- 掌握 fan-out（并行扇出）与 fan-in（汇集扇入）的行为
- 理解图中节点执行顺序的确定性与可观测性

---

## 一、Node 定义

**Node 是一个接收 `state`、返回 `dict` 的函数**，这个 dict 表示对 State 的部分更新。

### 1.1 标准签名

```python
def node(state: State) -> dict:
    ...
    return {"some_field": value}   # 部分更新
```

约定：
- 参数：一个 `state`（`State` 类型）
- 返回：`dict`（通常是 State 的部分字段），核心是「尽量返回 dict」
- 也可以返回 `Command` 做更复杂的控制（后续 Day 详解）

### 1.2 节点涵盖的工作

| 工作 | 说明 | 示例 |
| --- | --- | --- |
| 调用 LLM | 让模型产出内容 | `llm.invoke(...)` |
| 调用工具/外部 API | 检索、计算、联网 | 搜索、查库 |
| 处理逻辑 | 清洗、过滤、格式化、规则判断 | 敏感词匹配 |
| 路由决策 | 返回字段给条件边使用（Day04） | 写 `risk_level` |

### 1.3 节点可绑定 LLM

节点内部可以直接使用 ChatModel：

```python
def sentiment_node(state: State) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini")
    resp = llm.invoke(f"判断情感：{state['input_text']}")
    return {"sentiment": resp.content}
```

### 1.4 四种常见写法

```python
# 纯函数（同步）
def rule_node(state): return {"x": 1}

# 调 LLM
def llm_node(state):
    r = llm.invoke(state["text"])
    return {"out": r.content}

# async 函数
async def async_node(state):
    r = await llm.ainvoke(state["text"])
    return {"out": r.content}

# 只返回部分字段（partial state）
def partial_node(state): return {"only_this": True}
```

---

## 二、Edge 类型（重点）

### 2.1 四种声明方式

| API | 作用 | 等价写法 |
| --- | --- | --- |
| `add_edge(a, b)` | 普通定向边，无条件流转 | 无 |
| `add_conditional_edges(...)` | 条件边，根据状态选下一个节点 | Day04 详讲 |
| `set_entry_point(node)` | 设置入口节点 | `add_edge(START, node)` |
| `set_finish_point(node)` | 设置出口节点 | `add_edge(node, END)` |

```python
graph.set_entry_point("a")        # 等价 add_edge(START, "a")
graph.add_edge("a", "b")          # 普通边
graph.set_finish_point("b")       # 等价 add_edge("b", END)
```

### 2.2 特殊节点：START 与 END

- `START`：图的入口，只能作为边的「起点」
- `END`：图的结束，只能作为边的「终点」

```python
from langgraph.graph import StateGraph, START, END
g.add_edge(START, "a")
g.add_edge("z", END)
```

---

## 三、节点返回值的合并

- 节点返回 dict → 图按**字段**合并到 State
- 可只返回部分字段（partial state），未返回字段保持原值
- 合并策略由字段是否带 **Reducer** 决定（Day02）：标量默认覆盖，累积字段走 reducer

```
节点返回 {"a": 1, "b": 2}  →  合并进 State（a、b 被更新或累积）
未返回的字段 c 保持原值
```

---

## 四、fan-out（扇出）与 fan-in（扇入）

### 4.1 fan-out：一个节点多个出边

一个节点有**多条出边**时，目标节点**并行执行**。

```
        ┌── safety 节点 ──┐
classify ─┤               ├──▶ ...   # safety、sentiment 并行
        └── sentiment 节点┘
```

```python
g.add_edge("classify", "safety")
g.add_edge("classify", "sentiment")   # 同一个源节点 -> 并行
```

### 4.2 fan-in：多个节点汇集到同一节点

多个节点连到同一节点时，**等所有上游都完成**后才执行该节点（汇集屏障）。

```python
g.add_edge("safety", "report")
g.add_edge("sentiment", "report")     # 都汇到 report，report 最后执行
```

### 4.3 观察行为

用 `stream_mode="updates"` 逐节点查看，或用总耗时验证并行（并行总耗时≈最慢分支，而非各分支之和）。在 `03_fan_out_in.py` 中，安全检测 0.3s、情感分析 0.7s，并行下总耗时≈0.7s。

---

## 五、节点执行顺序的确定性

- **线性图**：严格按边顺序执行
- **分支图**：fan-out 的分支按计划并行执行，fan-in 节点在所有入边就绪后执行
- **可观测**：`stream_mode` 的 `values`/`updates` 可逐节点观察每步状态

LangGraph 的调度是确定性的——给定相同的输入和状态，节点的执行与结果可复现，利于调试与持久化。

---

## 关键知识点总结

### 1. Node 签名速查

```python
def node(state: State) -> dict:
    """读取 state 的输入字段，返回对 state 的部分更新。"""
    return {"字段": 值}
# 支持同步、async；内部可调 LLM / 工具 / 纯逻辑
```

### 2. Edge 类型速查表

| API | 功能 | 等价 |
| --- | --- | --- |
| `add_edge(a, b)` | 无条件 a→b | — |
| `add_conditional_edges(...)` | 条件路由 | Day04 |
| `set_entry_point(a)` | 入口 | `add_edge(START, a)` |
| `set_finish_point(z)` | 出口 | `add_edge(z, END)` |

### 3. fan-out / fan-in 速查

| 模式 | 触发 | 行为 |
| --- | --- | --- |
| 扇出 fan-out | 一个节点多个出边 | 下一层并行执行 |
| 扇入 fan-in | 多节点连同一节点 | 上游全就绪后再汇入 |

### 4. 图构建步骤速查

```
① StateGraph(State)  ② add_node ③ add_edge/set_entry_point/set_finish_point ④ compile()
```

---

## 代码文件说明

| 文件 | 内容 |
| --- | --- |
| `01_node_basics.py` | 纯函数/调 LLM/async 节点，部分字段返回 |
| `02_edge_types.py` | 普通边、入口/出口、`START`/`END` 等价写法 |
| `03_fan_out_in.py` | 扇出并行 + 扇入汇集的执行可观测 |

---

## 图构建最佳实践

- 优先用 `START`/`END` 常量而非 `set_entry_point`/`set_finish_point`（更直白、推荐）
- 节点函数保持**单一职责**：一个节点只做一类事，便于复用与并发
- 用 `stream_mode="updates"` 调试节点顺序与状态
- 需要并行时善用 fan-out（一个源节点多条出边）

## 常见误区

- **以为多个父节点连到同一子节点=多次执行**：实际上是 fan-in 汇集，等全部上游完成只执行一次
- **以为单通道一条直线就是全部**：`add_conditional_edges` 才是动态路由的关键（下一章）
- **节点直接改 state 而不返回**：会用不到；必须通过返回 dict 让框架合并

---

## 实战练习

### 练习 1：给产物加一个纯处理节点
在 `02_edge_types.py` 的「报告」后加一个「格式化节点」，以纯函数把 `log` 拼成一行字符串输出，观察新边。

### 练习 2：验证并行的收益
运行 `03_fan_out_in.py`，把 sentiment 的 `sleep` 改成 1.2s，对比串行估算耗时，确认实际总耗时≈1.2s 而非 1.5s，解释原因。

### 练习 3：async 节点
在 `01_node_basics.py` 的 async 图中再增加一个 async 节点（如「异步存档」），串在 recheck 之后，确认链路完整执行。

---

## 下一步

普通边无条件流转，而真正的智能在于**根据状态动态选择去哪**。Day04 深入学习 `add_conditional_edges` 条件边——用它实现按内容类型路由、按风险等级分流，为图的「动态决策」装上引擎。