# Day07 - MCP 与 AI Agent 集成实战

> 把前几天的内容拼成一个能「自主规划并调用外部工具」的 Agent：注册多个 MCP Server、自动发现工具、模型决策调用、多 Server 协作。这是 MCP 最有价值的使用方式。

---

## 1. Agent 与 MCP 的关系

- **Agent** = 规划 + 记忆 + 工具使用（Day07 聚焦「工具使用」环节）
- **MCP** 负责让 Agent 的标准能力接入层规范化、可复用

```
               ┌──────────── Agent 决策循环 ────────────┐
               │  观察环境  →  规划  →  决定调用工具      │
               │   ▲                       │            │
               │   └──── 回填结果 ◀────────┘            │
               └────────────────┬──────────────────────┘
                                │ 标准化
                     ┌──────────▼──────────┐
                     │    MCP 能力接入层     │
                     └──┬──────┬──────┬─────┘
                     Server A Server B Server C
                     工具     资源     工具
```

---

## 2. 注册多个 Server

言 Agent 通常要为不同能力分别连 Server：

```python
servers = {
    "bank": StdioServerParameters(command="python", args=["server_bank.py"]),
    "files": StdioServerParameters(command="python", args=["server_files.py"]),
    "web":   StdioServerParameters(command="python", args=["server_web.py"]),
}
```

每个 Server 一个 Client 连接，Agent 汇总多份工具清单，形成一个**统一工具面**。

---

## 3. Agent 决策循环（核心）

一个通用的 MCP Agent 循环：

1. **收集工具**：为每个 Server `list_tools()`，汇总成模型可读的工具 schema
2. **注入上下文**：把工具清单放入系统提示
3. **模型决策**：LLM 输出「要调哪个工具 + 参数」（tool calling）
4. **执行**：定位到对应 Server 的 Client，`call_tool()` 真实执行
5. **回填/反思**：把结果交给模型，判断是否还需更多工具调用（循环）
6. **结束**：模型给出最终答复

关键点：**多 Server 需要有「工具 → Server」的路由表**，才能知道某个工具归哪个 Client 执行。

---

## 4. 一个业务示例

Day07 提供一个「银行查询」业务 Server（`server_bank.py`），暴露如 `get_balance`、`transfer` 工具。Agent（`01_agent_loop.py` 离线模拟）演示如何：

- 发现银行 Server 的工具
- 根据用户问句决定调用查询余额
- 把结果组织成回复

---

## 5. 与 LangChain 等框架的结合

若你已用了 Agent 框架，MCP 也能融入：

- 用框架的 tool adapter 把 MCP 工具变成框架的工具
- 或直接以「自己维护 Client + 决策循环」的方式集成
- 关键依旧是：工具清单 → schema → 模型决策 → call_tool

---

## 6. 本节小结

- Agent 用 MCP 连接外部能力，工具清单 → schema → 决策 → 执行
- 多个 Server → 多份 Client → 汇总成统一工具面 + 路由表
- 离线可用「规则决策」跑通闭环，真实环境换成 LLM tool calling
- 与既有的 Agent 框架可平滑集成

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_agent_loop.py` | Agent + MCP 决策循环的讲解与离线模拟 |
| `server_bank.py` | 一个业务 Server 模板（需 SDK，也可离线阅读） |
| `README.md` | 本目录说明 |

`01_agent_loop.py` 离线可运行；`server_bank.py` 需 `mcp` 包才能真实运行。