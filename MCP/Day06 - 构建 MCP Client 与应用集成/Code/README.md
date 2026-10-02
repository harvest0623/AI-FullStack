# Day06 - Code 代码目录说明

本目录提供 Day06（构建 MCP Client 与应用集成）的代码。所有脚本**离线可运行**，无需安装 mcp 包，也不依赖真实 LLM。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_client_connect.py` | 讲解+演示 | Client 握手、能力发现、调用的离线模拟，含真实 SDK 写法注释 |
| `client_llm.py` | 集成演示 | 展示「发现→决策→调用→回填」闭环（含 LLM 决策骨架） |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_client_connect.py
python client_llm.py
```

## 说明

- `01_client_connect.py`：用 `ClientSession` 的真实 API 注释 + 离线模拟输出，帮你理解连接流程
- `client_llm.py`：用简单规则函数代替 LLM，完整演示「模型决策 → MCP 调用 → 回复」的闭环；真实环境把 `mock_llm_decide` 换成真实 LLM 的 tool calling 即可
- 若想跑真实链路，可把 Day04 的 `server_hello.py` + `client_test.py` 作为可运行闭环对照