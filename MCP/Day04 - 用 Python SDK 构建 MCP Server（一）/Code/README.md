# Day04 - Code 代码目录说明

本目录提供 Day04（构建 MCP Server：工具）的代码。

## 文件清单

| 文件 | 类型 | 运行依赖 | 作用 |
|------|------|---------|------|
| `01_fastmcp_hello.py` | 讲解脚本 | 无需安装 | 模拟 FastMCP 注册链路，演示装饰器用法 |
| `server_hello.py` | 真实 Server 模板 | 需 `pip install mcp` | 暴露 echo / add 两个工具的 FastMCP Server |
| `client_test.py` | 真实 Client 模板 | 需 `mcp` | 连接 server_hello.py 并调用工具 |
| `README.md` | 说明 | - | 本目录说明 |

## 运行方式

### 离线讲解（无需安装）

```bash
python 01_fastmcp_hello.py
```

### 真实闭环（需已安装 mcp SDK）

请在两个终端分别运行：

```bash
# 终端一：启动 Server（阻塞等待连接）
python server_hello.py

# 终端二：连接并调用
python client_test.py
```

或合并为一条（先装依赖）：

```bash
pip install mcp
python client_test.py   # 其内部会以子进程拉起 server_hello.py
```

> `client_test.py` 会以子进程方式自动启动 `server_hello.py`，因此只需运行它一个即可看到完整闭环。

## 说明

- `01_fastmcp_hello.py` 用内置模拟类复现 FastMCP 的装饰器注册逻辑，纯离线、不联网
- 请确保 `server_hello.py` 与 `client_test.py` 在同一目录，且已安装 mcp 包