# Day08 - Code 代码目录说明

本目录提供 Day08（与 LangChain / Agent 的结合）的代码。所有脚本**离线可运行**，不依赖真实 langchain 安装。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_langchain_bridge.py` | 讲解脚本 | LangChain bind_tools 思路及其与本模块的映射 |
| `02_mini_agent.py` | 讲解+演示 | 自建最小 Agent（循环 + 记忆） |
| `03_tool_abstraction.py` | 讲解+工具 | Tool / ToolRegistry 统一抽象 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_langchain_bridge.py
python 02_mini_agent.py
python 03_tool_abstraction.py
```

## 说明

- `02_mini_agent.py` 本质是 Day06 循环 + 消息记忆，示范"最小 Agent"结构
- `03_tool_abstraction.py` 是一个实用的工具注册中心，可复用到真实项目中