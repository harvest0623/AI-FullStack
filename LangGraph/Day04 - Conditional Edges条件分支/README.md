# Day04 - Conditional Edges 条件分支

条件边让图能**根据状态动态决策去向**，是实现路由和循环的基础。有了它，一个图就不再是「一条直线跑到底」，而是能够像真正的程序一样 `if/else`、按语义分流、按风险等级做决策。本章讲透 `add_conditional_edges` 的语法与语义，介绍规则路由、语义路由等设计模式，并强调无条件 fallback 的重要性——避免图走进死胡同。

## 学习目标

- 理解条件边与普通边的区别
- 掌握 `add_conditional_edges` 的完整语法与参数含义
- 会写多种 `path_map`（直接返节点名 / if-else / 返回节点名列表）
- 掌握路由节点的三种设计模式：规则路由、语义路由、分类路由
- 设计无条件的 fallback，保证任何输入都有下一个节点
- 避开常见坑（路径名不一致、参数位置错误、死胡同）

---

## 一、条件边概念

- **普通边**：无条件 `a → b`，只要 a 执行完必定流向 b
- **条件边**：a 执行后，**根据状态/返回值动态选择去哪个节点**

```
                ┌──> node_a
  source ────────┤   （由 route(state) 的返回决定）
                └──> node_b
```

---

## 二、add_conditional_edges 语法

```python
graph.add_conditional_edges(
    source_node,            # 源节点名
    path_map,               # 路径映射函数：state -> 下一个节点名（或列表）
    {                       # 可选：路径名 -> 实际节点名映射
        "route_a": "node_a",
        "route_b": "node_b",
    }
)
```

三个要点：

1. `source_node`：以哪个节点为源（当它执行完就检查条件）
2. `path_map`：一个函数，接收 state（或该节点返回值），**返回路径名**或路径名列表
3. 映射字典（可选）：把 path_map 返回的路径名映射到**实际节点名**

> 若省略映射字典，则要求 `path_map` 直接返回节点名。

---

## 三、path_map 的几种写法

### 3.1 state 作为入参

```python
def route(state: State) -> str:
    return "a" if state["x"] else "b"

g.add_conditional_edges("source", route, {"a": "node_a", "b": "node_b"})
```

### 3.2 使用节点返回的特殊字段

先由节点写入一个字段（如 `content_type` / `risk_level`），条件边读取它路由：

```python
def classify(state): return {"content_type": "product"}   # 分类节点写字段

def route(state):
    return state["content_type"]        # 读取字段决策
```

### 3.3 返回节点名列表 → 并行出发（fan-out）

`path_map` 返回**列表**时，会同时进入多个节点并行执行：

```python
def route(state):
    if state["both"]:
        return ["node_x", "node_y"]    # 并行扇出
    return ["node_x"]
```

---

## 四、路由节点设计模式

### 4.1 规则路由

用明确的规则（关键字、阈值）判定：

```python
def route(state):
    if "退货" in state["text"]: return "after_sale"
    if "投诉" in state["text"]: return "complaint"
    return "default"
```

适用：字段含义清晰、可硬编码规则。

### 4.2 语义路由

用 LLM 判断类别，再做结构化输出并路由（`03_llm_router.py`）：

```python
classify_result = llm_with_parser.invoke(...)   # 返回结构化对象
return {"verdict": "approved"/"review"/"block"}
```

适用：需要理解语义、无法用简单规则拆分的场景。

### 4.3 分类路由

先分类再映射——用一个节点产出「类别」，条件边按类别映射到处理链。把**分类**与**路由**解耦，清晰易维护（`02_router_pattern.py`）。

---

## 五、无条件 fallback

**确保任何情况都有下一个节点**，避免 dead end。两种保障手段：

```python
# 1) 在 path_map 里提供兜底返回
def route(state):
    if state["x"] == "a": return "node_a"
    return "default_node"     # 兜底

# 2) 在映射字典里保证全覆盖，未命中也能落到 END 或默认处理
mapping = {"a": "node_a", "default": "default_node"}
```

> 若 path_map 返回了映射字典中不存在的路径名，LangGraph 会因找不到目标节点而抛错。因此 route 的每个可能返回值都应在 mapping 中有对应项。

---

## 六、常见坑

| 坑 | 说明 | 解决 |
| --- | --- | --- |
| 路径函数返回值与节点名不一致 | path_map 返回的 key 不在 mapping / 不是节点名 | 用显式 mapping 确保一致 |
| `path_map` 位置参数放错 | 它是第 2 个参数，不是第 3 个 | `add_conditional_edges(src, path_map, mapping)` |
| 未知路由结果导致死胡同 | route 返回未知值 | 无条件 fallback + 兜底节点 |
| 忘记加 mapping | 节点名与路径名混用 | 要么统一用节点名，要么显式 mapping |

---

## 实战：文本分类路由到不同处理链

```
输入文本 → 分类节点(内容类型：商品/退换货/投诉/其他)
              │
  add_conditional_edges(顶 by content_type)
              ├→ product_chain (商品咨询)
              ├→ aftersale_chain (退换货)
              ├→ complaint_chain (投诉)
              └→ default_chain (兜底)
```

实现见 `02_router_pattern.py`。

---

## 关键知识点总结

### 1. 条件边语法速查

```python
g.add_conditional_edges(
    "source",
    route,                        # state -> 路径名
    {"路径名": "节点名", ...},     # 可选映射
)
```

### 2. path_map 写法对比表

| 写法 | 代码 | 场景 |
| --- | --- | --- |
| 直接返节点名 | `return "node_b"` | 简单、省映射表 |
| if/else 分支 | `return "a" if ... else "b"` | 规则明确 |
| 读状态字段 | `return state["ctype"]` | 分离分类与路由 |
| 返回列表 | `return ["n1","n2"]` | 并行扇出 |

### 3. 路由模式设计

| 模式 | 依据 | 适用 |
| --- | --- | --- |
| 规则路由 | 关键字/阈值 | 规则可硬编码 |
| 语义路由 | LLM + 结构化输出 | 需语义理解 |
| 分类路由 | 分类结果映射 | 解耦清晰 |

### 4. fallback 设计

- route 每个可能返回值都映射到真实节点
- 提供「兜底节点」承接未命中分支
- 绝不让未知结果把图带向 undefined

### 5. 常见坑清单

1. 路径名 ≠ 节点名（漏 mapping）
2. path_map 放错参数位置
3. 未知路径导致死路
4. 忘记兜底

---

## 代码文件说明

| 文件 | 内容 |
| --- | --- |
| `01_conditional_edges.py` | 条件边基础，按 risk_level 路由到通过/人工审核 |
| `02_router_pattern.py` | 规则路由模式，按内容类型分发到多条处理链 + fallback |
| `03_llm_router.py` | LLM 语义路由 + Pydantic 结构化输出，判定违规→通过/复核/拦截 |

---

## 分支调试技巧

- 用 `get_graph().print_ascii()` 先看清条件边的目标分支
- 用 `stream_mode="updates"` 逐节点观察实际走了那条分支
- 条件边报错「No node ... returned」通常是 mapping 缺失，先核对 path_map 返回值集合
- 各种输入都跑一遍，验证 fallback 兜底真实触发

---

## 实战练习

### 练习 1：扩展条件分支
在 `01_conditional_edges.py` 中为 `risk_level="medium"` 增加一个「直接拦截」分支，更新 route 与 mapping，跑通三种路径。

### 练习 2：语义路由调优
修改 `03_llm_router.py` 的判定逻辑，让「疑似违规但程度低」走 `review` 而不是直接 `block`，验证 LLM 分类 + 条件边的联动。

### 练习 3：返回列表做并行
在 `02_router_pattern.py` 中新增一个「同时命中商品+退换货」的情形，让 route 返回列表并发两条处理链，观察 fan-out 并行。

---

## 下一步

完成本章，你已掌握阶段一「图基础」的核心——State、Node、Edge、Conditional Edge。这四块足以搭建绝大多数工作流骨架。接下来进入阶段二，为图注入生产能力：Day05 用 **Checkpointer** 让图具备持久化与断点恢复能力。