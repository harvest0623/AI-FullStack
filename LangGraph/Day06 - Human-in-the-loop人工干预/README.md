# Day06 - Human-in-the-loop 人工干预

> 让工作流在关键步骤"停下来等人拍板"，再把控制权交还给流程。安全审阅与业务操作的标配。

## 本章简介

Day05 我们获得了"把状态存下来"的能力，那是地基；本章在这块地基上盖起最关键的一层——**Human-in-the-loop（HITL，人在回路）**。

真正负责的 AI 应用不会让模型在**没有监督**的情况下直接对外执行敏感操作：发钱要确认、发布内容要审阅、高风险结论要复核。LangGraph 给出的解法是让图在特定节点**暂停**，把"问题"抛给外部，等人给出**决策后再恢复**。整个过程的状态都由 Checkpointer 兜底，可停可续、可反复验证。

本章聚焦框架本身：三种实现模式、核心的 `interrupt()` 函数、恢复执行的 `Command(resume=)`，以及一个可直接复用的**人工审批工作流**。完整 Agent 系统的实现留待后续独立板块。

---

## 学习目标

完成本章后，你应能：

- 说清 HITL 是什么、为什么需要、它如何依赖 Day05 的 Checkpointer
- 区分三种 HITL 实现模式，知道各自适用场景
- 熟练使用 `interrupt()` 在指定节点暂停并向外部抛出问题
- 用 `Command(resume=...)` 把人工决策注入并恢复执行
- 用 `get_state()` 检查图当前停在哪个节点、读取待审内容
- 独立实现一个内容审批工作流并复用到其他业务

---

## 理论知识

### 一、Human-in-the-loop 概念

**定义**：工作流在特定节点**暂停**，等待人类**批准 / 修正 / 提供信息**后继续。

**为什么需要**：

| 场景 | 说明 |
|------|------|
| 安全审阅 | 高风险内容不能自动放行 |
| 财务/业务确认 | 转账、下单、删除前需要人点头 |
| 纠错 | 模型结论可疑时人工修正 |
| 补信息 | 缺参数时停下来问用户 |

**关键依赖**：它**依赖 Checkpointer**——暂停需要把状态持久化，恢复才能从断点继续。所以 `compile(checkpointer=...)` 是前提。

### 二、三种实现模式

| 模式 | 机制 | 适用场景 |
|------|------|----------|
| **中断 `interrupt()`** | 内置函数暂停，把问题返回外部，等 resume | 审批、需结构化确认的业务 |
| **等待外部输入** | 图在外部循环中被反复调用，人工操作在调用间隙发生 | 交互式聊天、Agent 工具确认 |
| **检查状态 + 更新** | 用 `get_state`/`update_state` 判断是否需要人工再决策 | 无需真正暂停，人工只做状态修订 |

> 本章重点在第一种：`interrupt()`。它最贴合"审核门"这类结构化业务。

### 三、interrupt() 函数（重点）

```python
from langgraph.types import interrupt

def human_node(state):
    approved = interrupt({"question": "是否批准?", "payload": state})
    return {"approved": approved}
```

要点：

- 执行到 `interrupt()` 时图**暂停**，把参数（问题）返回给外部调用方；
- 此时**图未完成（未到 END）**，状态已保存在 Checkpointer；
- `interrupt()` 的**返回值** = 之后外部 `Command(resume=...)` 传入的值；
- 恢复后，节点从 `interrupt()` 那一行**继续执行**，返回值照常写入状态。

### 四、恢复执行 Command(resume=)

```python
from langgraph.types import Command

graph.invoke(Command(resume=True), config=thread_config)
```

要点：

- `resume` 的值会作为上一个 `interrupt()` 的**返回值**注入节点；
- 必须在**同一个 `thread_id`** 的 config 下恢复，否则找不到挂起的上下文；
- 多次 `interrupt` 需要**多次 `Command(resume=)`** 依次推进。

### 五、完整流程

```
1. 图执行 → 遇到 interrupt() 暂停（图未完成，状态入 Checkpointer）
2. 外部用 graph.get_state(config) 获取问题与待审内容
3. 人工审阅 / 决策
4. graph.invoke(Command(resume=决策结果), config=同一thread)
5. 图从暂停处继续执行直到 END
```

### 六、审阅 / 编辑工具调用

对涉及工具调用的链路，同样可在"工具即将执行"前 `interrupt` 工具参数让人确认，之后再 `resume`，从而实现"人工同意才真正调用工具"的护栏。

### 七、审批工作流示例（重点）

- **内容审核**：安全检测 → 高风险需人工打回 → 人工批准 / 拒绝 → 放行 / 拦截
- **交易流程**：确认金额 → 人工确认 → 完成

两类本质相同：**关键决策点插入 `interrupt`，接收人审结果决定走向**。本章 `03_approval_flow.py` 即为可直接复用的 `ApprovalWorkflow` 模式。

### 八、常见坑

| 坑 | 说明 |
|----|------|
| 忘配 Checkpointer | `interrupt()` 必须依赖它，否则无法挂起/恢复 |
| resume 在不同 thread | 只有同一 `thread_id` 才能恢复挂起的进程 |
| 异步配合 | 用 `ainvoke` 时需对应 `Command` 同步语义，注意 await 链 |
| resume 值类型 | 要与 `interrupt()` 内部期望的类型一致（如 dict / bool） |

---

## 代码文件说明

| 文件 | 说明 |
|------|------|
| `Code/01_interrupt_basics.py` | `interrupt()` 打断与恢复：MemorySaver 配置、暂停图、`get_state` 捕获打断态、`Command(resume)` 恢复，完整中断恢复循环 |
| `Code/02_command_resume.py` | `Command` 恢复执行：`resume` 值注入、多处 `interrupt` 依次恢复、先检查中断状态再决策。封装 `ResumeFlow`，含多线程演示 |
| `Code/03_approval_flow.py` | 人工审批工作流：内容分析 → 需人工审计 → `interrupt` 暂停 → 批准/拒绝 → 放行/拦截。封装可复用 `ApprovalWorkflow` |

---

## 关键知识点总结

### interrupt 语法速查

```python
from langgraph.types import interrupt, Command

val = interrupt(payload)          # 节点内暂停，payload 给外部
graph.invoke(Command(resume=val), config=cfg)   # 外部恢复
```

### Command(resume) 恢复流程

```
invoke(...) 停在 interrupt
   └> get_state 查看
   └> Command(resume=决策)  继续
      └> 反复直到 END
```

### 三种模式对比

| 模式 | 是否真正暂停 | 典型 API |
|------|--------------|----------|
| interrupt 中断 | 是 | `interrupt()` / `Command(resume=)` |
| 外部输入循环 | 否（在调用间隙人工介入） | 反复 invoke |
| 检查状态+更新 | 否（只改写状态） | `get_state` / `update_state` |

### 常见坑

- 忘配 Checkpointer
- resume 跨 thread 失败
- 异步调用时未正确 await

---

## 实战练习

### 练习 1：模拟转账确认

把 `interrupt()` 改写为"确认转账金额"的设计：`interrupt({"amount": 1000, "to": "0x…"})`，人工 `resume=True/False` 后继续或中止转账。

### 练习 2：双中断审批

在 `02_command_resume.py` 基础上加第三个 `interrupt`（如"操作台账确权"），观察每次 `Command(resume=)` 怎样逐级推进挂起点。

### 练习 3：带意见的审批

改写 `03_approval_flow.py`，让批准/拒绝时都**必须携带 `comment`**，并在最终 `report` 中展示完整审批意见链，体会 HITL 的可审计性。