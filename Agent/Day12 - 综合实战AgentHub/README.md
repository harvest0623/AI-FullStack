# Day12 - 综合实战 AgentHub

## 今日目标

把前 11 天的核心机制组装成一个**完整可运行的小型 Agent 框架——AgentHub**。这是收官之战：不再学新概念，而是把学过的东西连成整体。

```
┌─────────────────────── AgentHub 架构 ───────────────────────┐
│                                                              │
│  用户输入                                                    │
│     │                                                        │
│     ▼                                                        │
│  [输入护栏] 注入检测（Day09）                                 │
│     │                                                        │
│     ▼                                                        │
│  [规划器] 任务分解（Day05）                                   │
│     │                                                        │
│     ▼                                                        │
│  [ReAct 循环]（Day02）                                       │
│    ├── 思考 -> [LLM 模拟器]                                  │
│    ├── 行动 -> [工具注册表]（Day03）                          │
│    │      └── [行为护栏] 白名单/参数校验/熔断（Day09）        │
│    │      └── [审批门] 高危操作人工确认（Day09）              │
│    ├── 观察 -> [错误处理] 重试/降级（Day06）                  │
│    └── 记忆 -> [工作记忆 + 长期记忆]（Day04）                 │
│     │                                                        │
│     ▼                                                        │
│  [输出护栏] 脱敏（Day09）                                     │
│     │                                                        │
│     ▼                                                        │
│  最终回答 + [轨迹日志]（Day10）                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

学完今天，你将能够：

1. 看懂一个 Agent 框架的完整骨架
2. 理解各模块如何协作（而非孤立的知识点）
3. 用 AgentHub 跑通三个实战场景
4. 知道下一步该往哪深入（框架源码阅读路线）

---

## 一、代码结构

```
Code/
├── agenthub.py           # 核心框架（约 400 行，所有模块组装）
├── 01_quickstart.py      # 最小用例：3 步跑通一个 Agent
├── 02_tools_memory.py    # 进阶：自定义工具 + 记忆
├── 03_full_pipeline.py   # 实战：护栏拦截 + 审批 + 日志全流程
└── README.md
```

`agenthub.py` 是今日主角，它由 7 个组件构成：

| 组件 | 来源 | 职责 |
|------|------|------|
| `ToolRegistry` | Day03 | 工具注册、schema 校验、白名单 |
| `Memory` | Day04 | 工作记忆（循环上下文）+ 长期记忆（跨任务） |
| `Planner` | Day05 | 把模糊任务分解为步骤序列 |
| `ReActLoop` | Day02 | 思考→行动→观察循环，直到产出答案 |
| `Guard` | Day09 | 输入护栏/行为护栏/输出护栏三层 |
| `ApprovalGate` | Day09 | 高危工具调用前人工确认 |
| `TrajectoryLogger` | Day10 | 步骤级轨迹日志 |

## 二、设计取舍（重要）

真实框架（LangGraph/LangChain Agent）比 AgentHub 复杂 100 倍，但**核心抽象是一致的**：

1. **LLM 被抽象成"决策函数"**：AgentHub 用规则模拟 LLM（任务类型识别 -> 选择工具），生产中换成 API 调用即可，框架其他部分不变
2. **工具是"注册-发现-调用"三段式**：与 OpenAI Function Calling 的协议同构
3. **循环有终止条件**：最大轮数 + 任务完成判定，防止失控
4. **横切关注点（护栏/日志/审批）以中间件形式插入**：不侵入主循环逻辑

## 三、三个演示场景

### 场景 1：Quickstart（01_quickstart.py）

```python
hub = AgentHub()
hub.register_tools([QueryInventory, QueryPrice, PlaceOrder])
result = hub.run("帮我查 A100 的库存和价格，然后下单 10 个")
```

观察 AgentHub 如何自动规划 3 步、逐工具调用、汇总回答。

### 场景 2：工具与记忆（02_tools_memory.py）

- 自定义两个新工具（物流查询、发票开具）注册进框架
- 长期记忆：第一次问了"仓库地址"，第二次不再重复问
- 工作记忆：同一任务内的多轮观察自动串联

### 场景 3：全流程实战（03_full_pipeline.py）

一次运行体验完整生产链路：

1. **注入攻击**被输入护栏拦截
2. **正常任务**走规划 -> ReAct -> 工具调用
3. **下单（高危）**被审批门拦截，人工批准后继续
4. **路径越界**的工具调用被行为护栏拦截
5. **输出脱敏**：回答中的手机号自动打码
6. 结束后输出**完整轨迹日志**

---

## 四、AgentHub 与真实框架的对照

| AgentHub 概念 | LangChain/LangGraph 对应 |
|---------------|--------------------------|
| `ToolRegistry` | `BaseTool` + `bind_tools` |
| `ReActLoop` | `create_react_agent` / LangGraph 节点循环 |
| `Memory` | `MemorySaver` / `Checkpointer` |
| `Guard` | LangGraph `interrupt` + 自定义 guardrail 节点 |
| `ApprovalGate` | LangGraph `interrupt()` 断点 + Command 恢复 |
| `TrajectoryLogger` | LangSmith tracing |
| `Planner` | Plan-and-Execute agent |

阅读真实框架源码时，带着 AgentHub 的骨架去看，会轻松很多。

---

## 五、12 天知识地图回顾

```
Day01 概述        -> 什么是 Agent、自主性分级        [认知]
Day02 ReAct       -> 核心循环：思考-行动-观察          [机制] ★ 核心
Day03 工具调用    -> Function Calling、注册与校验     [机制] ★ 核心
Day04 记忆系统    -> 工作记忆/短期/长期               [机制]
Day05 任务规划    -> Plan-and-Execute、TODO、DAG      [机制]
Day06 多工具编排  -> 选择、并行、错误处理、成本        [工程]
Day07 评估调试    -> 成功率指标、轨迹分析、失败模式    [工程]
Day08 多Agent     -> Supervisor/Pipeline/Debate       [架构]
Day09 人机协同    -> 审批门、中断恢复、三层护栏       [安全] ★ 核心
Day10 服务化      -> API 化、日志、追踪、指标         [运维]
Day11 生产部署    -> 灰度、版本、回滚、成本           [运维]
Day12 AgentHub    -> 全部组装                         [实战] ★ 毕业项目
```

---

## 六、下一步学习路线

1. **读源码**：LangGraph 的 `pregel` 循环（约 500 行）对照 ReActLoop 理解
2. **真实 LLM**：把 AgentHub 的模拟 LLM 换成 OpenAI 兼容 API（改动只有一处）
3. **持久化**：把 TrajectoryLogger 输出接 SQLite，做简单的任务回放工具
4. **多 Agent**：把 AgentHub 实例化多次，用 Day08 的 Supervisor 模式编排

---

## 七、代码文件说明

| 文件 | 内容 |
|------|------|
| `agenthub.py` | 核心框架：7 组件组装，全部离线可运行 |
| `01_quickstart.py` | 3 步跑通：注册工具 -> 运行 -> 查看轨迹 |
| `02_tools_memory.py` | 自定义工具、长期记忆生效演示 |
| `03_full_pipeline.py` | 护栏/审批/脱敏/日志全链路实战 |

---

## 八、毕业检查

- [ ] 能说出 AgentHub 的 7 个组件及各自职责
- [ ] 能修改 agenthub.py 新增一个工具并注册使用
- [ ] 能解释一次 run() 调用内部发生了什么（从输入到输出）
- [ ] 能对照 LangGraph 说出每个组件的对应物
