# Day05 - Code 代码目录说明

本目录提供 Day05（构建 MCP Server：资源与提示词）的代码。

## 文件清单

| 文件 | 类型 | 运行依赖 | 作用 |
|------|------|---------|------|
| `01_resources.py` | 讲解脚本 | 无需安装 | 离线演示资源（含动态 URI）、提示词的实现形态 |
| `server_resources.py` | 真实 Server 模板 | 需 `pip install mcp` | 提供资源+提示词+工具的完整 Server |
| `README.md` | 说明 | - | 本目录说明 |

## 运行方式

### 离线讲解（无需安装）

```bash
python 01_resources.py
```

### 真实调试（需已安装 mcp / uv）

```bash
pip install mcp

# 方式一：官方调试器（推荐，可 GUI 查看资源/提示词/工具）
uv run mcp dev server_resources.py

# 方式二：直接用 Python 运行（阻塞等待连接）
python server_resources.py
```

## 说明

- `server_resources.py` 演示了资源（静态 `config://app` 与动态 `docs://{topic}`）、提示词 `review_code`、以及一个带错误处理的工具 `divide`
- 动态 URI 中，URI 路径段会作为函数参数被注入，实现『一类资源一个函数』