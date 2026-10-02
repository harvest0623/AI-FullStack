# Day02 - Code 代码目录说明

本目录提供 Day02（架构与消息协议）的全部代码与说明。所有讲解脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_architecture.py` | 讲解脚本 | MCP 协议层次与生命周期流程 |
| `02_jsonrpc.py` | 讲解+演示 | JSON-RPC 2.0 三种消息的分类与识别 |
| `03_transport.py` | 讲解脚本 | stdio 与 Streamable HTTP 传输对比 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_architecture.py
python 02_jsonrpc.py
python 03_transport.py
```

## 说明

- `02_jsonrpc.py` 里内置了一个简单的消息分类函数，演示如何区分 request / response / notification
- 本日不涉及真实 SDK，纯概念；真实建连从 Day04 开始