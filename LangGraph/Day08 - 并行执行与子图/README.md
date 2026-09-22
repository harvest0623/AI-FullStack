# Day08 - 并行执行与子图

> 让多个独立节点同时跑起来提速，把复杂流程拆成可复用小图再拼装。工程扩展的两把钥匙。

## 本章简介

前面的流程图本质上是一条（或带分支的）链。当多个操作之间**互不依赖**时，串行执行就是一种浪费——比如对同一篇文章同时做安全检测、情感分析、主题分类，完全可以并行。另一方面，当我们积累了一套"单篇审核"的完整子流程，又希望在多个环节复用它时，就需要**子图**的封装能力。

本章围绕 LangGraph 两种**组合级**能力展开：

- **并行节点（fan-out/fan-in）**：一个节点分发到多个并行节点，再汇集；
- **`send` 动态并行**：执行期动态决定派发多少 worker（map-reduce）；
- **子图（Subgraph）**：把已编译的图作为节点嵌入另一张图，实现复用。

同时给出并行度的控制策略与批量处理最佳实践。基于此构建多智能体协作，留待 Agent 板块。

---

## 学习目标

完成本章后，你应能：

- 用多个出边连接多个节点，实现 fan-out/fan-in 并行
- 判断何时用普通并行、何时用 `send` 动态并行
- 用 `Send` 在执行期动态派发 worker，实现 map-reduce
- 自建并编译子图，作为节点嵌入顶层图
- 处理好子图 State 与顶层 State 的字段映射
- 控制并行度以规避限流

---

## 理论知识

### 一、并行节点（fan-out / fan-in）

```python
b.add_edge("entry", "safety")
b.add_edge("entry", "sentiment")   # fan-out：一个节点连到多个节点
b.add_edge("entry", "topic")

b.add_edge("safety", "aggregate")
b.add_edge("sentiment", "aggregate")  # fan-in：多个节点汇入一个节点
b.add_edge("topic", "aggregate")
```

要点：

- 多个出边 → **并行执行**这几个下游节点；
- **需节点间无依赖**（不读对方刚写的数据）；
- LangGraph 自动并发（图内部并发调度，多 worker 推进）；
- 讲究 DAG 语义，fan-in 节点等到所有上游完成后才运行。

### 二、send 动态并行（重点）

```python
from langgraph.types import Send

def plan_node(state):
    return [Send("worker", {"item": x}) for x in state["items"]]

graph.add_conditional_edges("planner", plan_node, ["worker"])
```

- **执行期**根据 `state["items"]` 动态决定派发多少个 worker；
- 每个 `Send` 携带**独立的参数**（`{"item": x}`）；
- 极适合**map-reduce**：map 侧 `Send` 每个 item 一个 worker，reduce 侧聚合节点汇总。

### 三、send 使用场景

| 场景 | 说明 |
|------|------|
| 批量处理大量数据项 | 每个 worker 处理一个 item |
| 每项独立处理 | worker 之间无共享状态 |
| 聚合节点收集 | 所有 worker 完成后统一汇总 |

### 四、子图（Subgraph）概念

把一个**已编译的图**当作一个节点嵌入另一个图：

```python
top_builder.add_node("sub", compiled_subgraph)
```

- 子图**独立编译**，可复用、可单测；
- 子图输入/输出与节点接口对齐——调用时传入的状态即子图输入，子图 final 状态会合并回顶层节点返回值；
- 便于把通用子流程抽离，多处复用。

### 五、子图与顶层图的状态衔接

- **子图输入**：调用时作为节点的输入传入；
- **子图输出**：子图最终状态作为该节点的返回值（部分字段）并入顶层状态；
- **字段映射**：通过自定义子图 State 决定哪些字段进入 / 流出；顶层的字段通过节点返回值赋值进顶层状态字段。

### 六、图组合方式

| 方式 | 说明 |
|------|------|
| **并行** | 多节点并发（fan-out/fan-in） |
| **子图** | 流程嵌套复用 |
| **循环** | 条件边返回上游（Day04 基础） |

三者可叠加：子图内部可又有并行，外层再按条件循环。

### 七、并行度控制

- 默认 LangGraph 管理 worker 池、自动并发；
- 高并发可能触及上游 API 限流 → 需要把并发限制在可控范围；
- 工程手段：在 worker 内做信号量/节流，或限制一次 `Send` 的数量分批处理。

---

## 代码文件说明

| 文件 | 说明 |
|------|------|
| `Code/01_parallel_nodes.py` | 并行节点：entry fan-out 到 安全检测/情感/主题 三个并行节点，fan-in 汇集到聚合节点；用 `stream_mode` 追踪每步 |
| `Code/02_send_batch.py` | send 动态并行：`Send` 动态派发多个 worker，每 worker 处理一个 item，聚合节点汇总。map-reduce 实现 |
| `Code/03_subgraph.py` | 子图组合：单篇审核子流程编译后作为顶层图节点，多次调用；演示自定义 State 字段映射与跨环节复用 |

---

## 关键知识点总结

### 并行 vs send 选择决策表

| 判断 | 用哪种 |
|------|--------|
| 并行分支数量**固定**，结构可写死 | 普通并行节点（fan-out） |
| 分支数量**执行期才确定**（依数据量） | `send` 动态并行 |
| 需要每项独立传参、独立结果 | `send` |
| 仅是图结构固定分叉 | 普通并行 |

### send 语法速查

```python
from langgraph.types import Send
return [Send("worker", {"item": x}) for x in state["items"]]
# planner -> add_conditional_edges(planner, plan_node, ["worker"])
```

### map-reduce 模式

```
planner(Send 每个 item)
  -> worker <并行 N 个>
  -> aggregator(reducer 累积 results)
```

### 子图接口对齐说明

- 编译后的图可 `add_node` 进顶层图；
- 输入 = 节点接收的状态；输出 = 子图最终状态并入节点返回值；
- 用自定义子图 State 显式声明输入输出字段，保障字段映射清晰。

### 并行度控制

- LangGraph 自动并发；
- 高并发留意限流，用批处理/节流限制一次派发规模。

---

## 实战练习

### 练习 1：固定并行的三路分析

扩充 `01_parallel_nodes.py`，再增加一个"关键词抽取"并行节点，观察 fan-in 聚合后 `summary` 是否包含四个分支的结果。

### 练习 2：带分数的批量审核

改写 `02_send_batch.py`，让每个 worker 返回 `(verdict, score)`，聚合节点按 score 排序输出，体会 map-reduce 的 reduce 汇总能力。

### 练习 3：子图 + send 结合

把 `03_subgraph.py` 的子图作为 worker，外面用 `send` 动态派发（每个 item 一个子图），实现"批量内容审核 + 每篇走完整子流程"的进阶组合，理解并行与子图的协同。