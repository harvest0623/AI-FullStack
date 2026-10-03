# Day08 - Code 代码目录说明

本目录提供 Day08（MCP 生态与真实客户端）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_ecosystem.py` | 讲解脚本 | 生态构成 + 官方参考 Server 图景 |
| `02_config.py` | 讲解脚本 | 如何把 Server 接入真实客户端（mcpServers 配置） |
| `03_debug.py` | 讲解脚本 | mcp dev / Inspector 调试流程 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_ecosystem.py
python 02_config.py
python 03_debug.py
```

## 说明

- 本日以「怎么看清生态 + 怎么接入/调试」为主，均为讲解
- 真实动手：在装了 `mcp` 后，对任意 `server_*.py` 执行
  `uv run mcp dev server_xxx.py` 打开 Inspector
- 接入真实客户端时，照着 `02_config.py` 的 JSON 结构填写 `command` 与 `args`