# Day07 - Code 代码目录说明

本目录提供 Day07（MCP 与 AI Agent 集成实战）的代码。

## 文件清单

| 文件 | 类型 | 运行依赖 | 作用 |
|------|------|---------|------|
| `01_agent_loop.py` | 讲解+演示 | 无需安装 | 多 Server 汇聚 + Agent 决策循环的离线模拟 |
| `server_bank.py` | 真实 Server 模板 | 需 `pip install mcp` | 一个「银行能力」业务 Server |
| `README.md` | 说明 | - | 本目录说明 |

## 运行方式

### 离线演示（无需安装）

```bash
python 01_agent_loop.py
```

### 真实 Server（需已安装 mcp）

```bash
pip install mcp
python server_bank.py
# 可用官方调试器: uv run mcp dev server_bank.py
```

## 说明

- `01_agent_loop.py` 用一个「工具→Server」路由表 + 规则决策函数，完整演示 Agent 调用 MCP 工具的循环；真实环境把决策函数换成 LLM tool calling 即可
- `server_bank.py` 是独立业务 Server，可被任何 MCP 客户端消费