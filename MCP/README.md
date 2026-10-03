# MCP 学习指南

> 系统化掌握 Model Context Protocol（MCP）：从核心概念与架构、JSON-RPC 消息协议与传输方式、工具/资源/提示词三大原语，到用 Python SDK 构建 Server 与 Client、与 AI Agent 集成、接入真实生态客户端，再到综合实战与生产要点，构建"让 AI 安全地连接并调用外部世界"的标准化能力

> 共 9 天，聚焦 MCP 协议本身的原理、构建与工程实践，是 AI-FullStack 应用的"外部能力接入层"

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [为什么用 MCP](#为什么用-mcp)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

**MCP（Model Context Protocol，模型上下文协议）** 是一个开放的标准化协议，解决"AI 应用如何安全、统一地连接外部工具、数据源与服务"的问题。它定义了 **Host（宿主）/ Client（客户端）/ Server（服务端）** 的协作模型，以及 **工具（Tools）、资源（Resources）、提示词（Prompts）** 等标准原语，让任何 MCP Server 都能被任何 MCP 客户端即插即用。

**与 AI-FullStack 其他板块的关系**：
- 前面模块（Python / LLM / LangChain / LangGraph / RAG / Agent / Ollama）解决了"模型怎么组织、工具链怎么编排、数据怎么处理"；
- **本板块解决"这些能力如何用一套标准化协议暴露给模型调用"**。
- Agent 需要"动手"（调工具、读文件、查库），MCP 就是让这些外部能力以统一的方式接入模型上下文的协议层。

**学习目标**：完成本板块后，你应能：
- 讲清 MCP 的定位、四大角色（Host / Client / Server / 外部系统）与三大原语
- 理解基于 JSON-RPC 2.0 的消息协议与 stdio / Streamable HTTP 两种传输
- 理解 Session 生命周期（initialize → initialized → 操作 → shutdown）
- 用 Python SDK（FastMCP）构建自己的 MCP Server（工具 / 资源 / 提示词）
- 用 Client 连接 Server，实现工具发现与调用
- 把 MCP Server 集成进 AI Agent，实现"能调工具"的智能体
- 在 Claude、Cline、Cursor 等真实客户端中接入与调试自己的 Server
- 掌握多 Server 编排、安全、认证、性能与生产最佳实践

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 讲解脚本 + 可直接套用的 Server/Client 模板
- **代码优先兼容离线运行**：本机未装 `mcp` 包时，讲解脚本自动讲解概念并以"模拟实现"演示流程（不真连外部）；检测到可用依赖时给出真实 SDK 写法提示，便于对照。
- 紧扣 MCP 本身，逐层深入，最后落到 Agent 集成与生产实践

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 命令行 | 必须 | 终端基本操作、环境变量 |
| Python | 掌握 | 所有代码均为 Python，含 async 基础 |
| JSON / RPC | 了解 | JSON-RPC 2.0 是 MCP 的协议基底 |
| HTTP | 了解 | 理解远程传输（Streamable HTTP） |
| AI 基础 | 了解 | LLM、Agent、工具调用（Tool/Function）概念 |

**环境准备**（建议，但不是运行本板块概念脚本的强制前提）：
- Python 3.9+，建议 3.11
- 可选：安装官方 MCP SDK `pip install mcp`
- 可选：安装 `uv`（`mcp` 官方 CLI 常用 `uv run mcp dev`）
- 可选：一个支持 MCP 的客户端（Claude Desktop、VS Code、Cline、Cursor 等）用于 Day08-09

> **重要**：本板块讲解脚本全部**离线可运行**，未装 `mcp` 包也能学完概念。若已安装 SDK，可在"真实代码"模板手动运行对照，加深理解。

---

## 为什么用 MCP

| 对比项 | 每个工具一套私有接入 | MCP 统一协议 |
|--------|--------------------|-------------|
| 接入成本 | 每个工具写专用集成，N 个工具 N 套 | 一次实现，任意 MCP 客户端即插即用 ★ |
| 标准化 | 无统一规范，各做各的 | 定义 Host/Client/Server 与三大原语 |
| 可复用 | 绑定某个应用 | Server 可被任意 Host 复用 |
| 安全性 | 权限各管各的 | 客户端可控，按需暴露能力 |
| 生态 | 封闭 | 官方参考 Server + 蓬勃发展的生态 |

---

## 学习路线图

```
┌──────────────────────────────────────────────────────────────────┐
│             MCP 学习路线（9天，从理解协议到上手构建）              │
└──────────────────────────────────────────────────────────────────┘

阶段一：理解协议（Day01-Day03）
┌──────────┬──────────┬──────────┐
│ Day01    │ Day02    │ Day03    │
│ 概述与   │ 架构与   │ 核心原语 │
│ 核心概念 │ 消息协议 │ 工具/资源 │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     ▼          ▼          ▼
阶段二：上手构建（Day04-Day06）
┌──────────┬──────────┬──────────┐
│ Day04    │ Day05    │ Day06    │
│ Server(一)│ Server(二)│ Client 与│
│ 工具     │ 资源/提示 │ 应用集成 │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     ▼          ▼          ▼
阶段三：集成与生产（Day07-Day09）
┌──────────┬──────────┬──────────┐
│ Day07    │ Day08    │ Day09    │
│ 与 AI    │ 生态与   │ 综合实战 │
│ Agent 集成│ 真实客户端│ 与生产要点│
└──────────┴──────────┴──────────┘
```

---

## 每日内容详表

### Day01 - MCP 概述与核心概念
- **核心**：MCP 是什么、为什么需要（解决 AI 与外部世界连接）、三大角色（Host/Client/Server）、与普通 API / Function Calling / Agent 的区别、一个典型会话长什么样
- **代码**：`01_what_is_mcp.py`（定位与概念）/`02_roles.py`（Host/Client/Server 角色）/`03_compare.py`（MCP vs 其他方案对比）/`mcp_check.py`（环境检测）/`README.md`
- **重点**：定位与三大角色、MCP 解决的核心痛点

### Day02 - 架构与消息协议
- **核心**：MCP 架构全貌、基于 JSON-RPC 2.0、两类角色、传输方式（stdio / Streamable HTTP）、Session 生命周期（initialize → initialized → 操作 → shutdown）、request/response/notification
- **代码**：`01_architecture.py`（架构与协议栈）/`02_jsonrpc.py`（JSON-RPC 消息格式）/`03_transport.py`（stdio vs HTTP 传输）/`README.md`
- **重点**：协议层次、生命周期、两种传输

### Day03 - 核心原语：工具 / 资源 / 提示词
- **核心**：三大原语的概念与区别（Tools 让模型"动手"、Resources 让模型"读数据"、Prompts 复用模板）、各自的结构、适用场景、示例对比
- **代码**：`01_three_primitives.py`（三大原语总览）/`02_tools.py`（工具详解）/`03_resources_prompts.py`（资源与提示词）/`README.md`
- **重点**：三大原语的定义、结构、何时用哪个

### Day04 - 构建 MCP Server（一）：工具
- **核心**：安装 mcp SDK、用 FastMCP 创建 Server、用 `@mcp.tool` 定义工具、参数与返回、在 stdio 模式运行、用 Client 快速自测
- **代码**：`01_fastmcp_hello.py`（讲解 + 简易模拟）/`server_hello.py`（可直接运行的 Server）/`client_test.py`（连接测试的 Client）/`README.md`
- **重点**：FastMCP 基本用法、定义并暴露工具

### Day05 - 构建 MCP Server（二）：资源与提示词
- **核心**：用 `@mcp.resource` 暴露资源（文件/配置/数据）、`@mcp.prompt` 定义提示词模板、组合使用、动态 URI 资源、错误处理与日志
- **代码**：`01_resources.py`（讲解 + 模拟资源）/`server_resources.py`（带资源与提示词的 Server）/`README.md`
- **重点**：资源与提示词的实现与动态 URI

### Day06 - 构建 MCP Client 与应用集成
- **核心**：用 Client 连接 Server、列出能力（list_tools / read_resource）、调用工具、把 MCP 工具接进更上层应用（结合 LLM）
- **代码**：`01_client_connect.py`（Client 连接与能力发现）/`client_llm.py`（Client + LLM 调工具演示/模拟）/`README.md`
- **重点**：Client 连接、能力发现、工具调用

### Day07 - MCP 与 AI Agent 集成实战
- **核心**：让 Agent 拥有 MCP 能力：注册多个 Server、工具自动发现、Agent 决策并调用 MCP 工具、多 Server 协作、与 LangChain/自建 Agent 结合的思路
- **代码**：`01_agent_loop.py`（Agent + MCP 循环讲解与模拟）/`server_bank.py`（一个业务 Server 示例）/`README.md`
- **重点**：Agent 与 MCP 的协作循环、多 Server

### Day08 - MCP 生态与真实客户端
- **核心**：官方参考 Server（filesystem / github 等）、Claude Desktop / Cline / Cursor / VS Code 接入配置方式、如何把自建 Server 配置进客户端、常用工具与调试入口
- **代码**：`01_ecosystem.py`（生态图景与参考 Server）/`02_config.py`（客户端配置讲解与模板）/`03_debug.py`（mcp dev / Inspector 调试）/`README.md`
- **重点**：接入真实客户端、调试方法

### Day09 - 综合实战与生产要点
- **核心**：从零搭一个"业务 Server + Client + Agent"的完整案例、多 Server 编排、安全与最小权限、传输选择、认证（OAuth）、性能与超时、上线自检清单、总结与后续路径
- **代码**：`server_shop.py`（完整业务 Server）/`client_agent.py`（配合运行的 Agent 客户端）/`01_architecture_case.py`（架构讲解）/`02_production_check.py`（上线自检清单）/`README.md`
- **重点**：完整案例、安全与生产实践

---

## 目录结构

```
MCP/
├── README.md                          ← 本文件（板块总入口）
├── Day01 - MCP 概述与核心概念/
│   ├── README.md
│   └── Code/
│       ├── 01_what_is_mcp.py
│       ├── 02_roles.py
│       ├── 03_compare.py
│       ├── mcp_check.py
│       └── README.md
├── Day02 - 架构与消息协议/
│   ├── README.md
│   └── Code/...
├── ...（Day03-Day08 同构）...
└── Day09 - 综合实战与生产要点/
    ├── README.md
    └── Code/
        ├── server_shop.py
        ├── client_agent.py
        ├── 01_architecture_case.py
        ├── 02_production_check.py
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码/模板统一放在 `Code/` 子文件夹内，`.py` 讲解脚本可直接 `python x.py` 运行
- 以 `server_*.py` / `client_*.py` 命名的为**真实可运行模板**（需安装 `mcp` 包，属容器内/本地演示）
- 概念讲解脚本**离线可跑**（不依赖 `mcp` 包）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-5 小时 | 约 1.5 周 |
| 标准 | 业余学习 | 2 小时 | 约 2-3 周 |
| 保守 | 碎片时间 | 1 小时 | 约 1.5 月 |

### 学习方法论

1. **协议先行**：Day01-03 把四大角色、三大原语、消息协议彻底讲清，这是理解一切的基石
2. **先跑讲解脚本**：离线脚本用"模拟实现"演示流程，先看懂再写真代码
3. **动手构建**：Day04 起自己写一个 Server，再写 Client 连自己，形成闭环
4. **接入 Agent**：Day07 把 Server 接进 Agent，体会"工具即能力"
5. **对照真实生态**：Day08 在 Claude / Cline 等客户端中接入并调试自己的 Server

### 阶段性检查点

- **阶段一完成后**：能讲清 MCP 的角色、原语、生命周期与传输方式
- **阶段二完成后**：能独立构建 Server（工具/资源/提示词）并用 Client 调用
- **阶段三完成后**：能让 Agent 调用自建 Server，并掌握生产部署要点

---

## 如何运行代码

### 环境准备

```bash
# 1.（可选）安装 MCP Python SDK（用于真实 Server/Client 模板）
pip install mcp

# 2.（可选）安装 uv（官方 CLI 常用运行器）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 之后可用: uv run mcp dev ...
```

### 运行示例

```bash
# 离线概念讲解（无需 mcp 包）
python "Day01 - MCP 概述与核心概念/Code/01_what_is_mcp.py"

# 真实 Server（需 mcp 包）
cd "Day04 - 使用 Python SDK 构建 MCP Server（一）/Code"
python server_hello.py

# 另开终端，用 Client 连接测试
python client_test.py

# 官方调试器（需 uv + mcp）
uv run mcp dev "Day04 .../Code/server_hello.py"
```

> 讲解脚本**无需 mcp 包也能运行**；`server_*.py` / `client_*.py` 需真实安装并连接。

---

## 知识点速查

### 核心概念速查

| 概念 | 说明 |
|------|------|
| MCP | 让 AI 应用统一连接外部工具/数据的开放协议 |
| Host | 宿主应用（Claude Desktop、应用等），面向用户 |
| Client | 宿主体内与 Server 一对一连接的中介 |
| Server | 暴露能力（工具/资源/提示词），封装外部系统 |
| Tools | 让模型"动作"的接口（写文件、调 API） |
| Resources | 让模型"读"的上下文数据 |
| Prompts | 可复用的提示模板 |
| JSON-RPC 2.0 | MCP 底层消息协议 |

### 常用原语速查

| 原语 | 方向 | 典型用途 |
|------|------|---------|
| `tools/list` / `tools/call` | Client → Server | 列出 / 调用工具 |
| `resources/read` | Client → Server | 读取资源内容 |
| `prompts/get` | Client → Server | 获取提示模板 |
| `initialize` | Client → Server | 会话建立 |
| `notifications/initialized` | Client → Server | 会话就绪 |
| `logging/message` | Server → Client | 服务器日志 |

### 关键机制速查

| 项 | 说明 |
|----|------|
| stdio 传输 | 本地子进程交互，走标准输入/输出 |
| Streamable HTTP | 远程传输，基于 HTTP + SSE |
| Sampling | Server 反向请求模型生成（高级） |
| Roots | 宿主导知 Server 可访问的本地目录 |

---

## 后续板块

本板块完成后，可自然衔接：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **多模态** | 让 MCP 传递图片/音频等更多载体 |
| **部署运维** | 把 MCP Server 容器化、远程化部署 |
| **微服务** | MCP Server + LLM 应用的服务化架构 |
| **Agent 进阶** | MCP 作为 Agent 的外部能力接入层 |

---

## 学习资源补充

> 遇到疑问时优先查阅官方文档

- [Model Context Protocol 官方文档](https://modelcontextprotocol.io) - 权威参考
- [MCP Python SDK 文档](https://github.com/modelcontextprotocol/python-sdk) - 官方 SDK
- [MCP 规范（Specification）](https://modelcontextprotocol.io/specification) - 协议规范
- [官方参考 Server 仓库](https://github.com/modelcontextprotocol/servers) - 可参考的 Server 实现

---

## 贡献与反馈

本学习手册为原创内容，参考 MCP 官方文档的组织思想但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，让 AI 真正"接通世界"！**