# Day09 - Code 代码目录说明

本目录提供 Day09（综合实战与生产要点）的代码。

## 文件清单

| 文件 | 类型 | 运行依赖 | 作用 |
|------|------|---------|------|
| `server_shop.py` | 真实 Server 模板 | 需 `pip install mcp` | 在线商店业务 Server（工具/资源/提示词） |
| `client_agent.py` | 离线 Agent 演示 | 无需安装 | 消费 server_shop 能力的完整闭环模拟 |
| `01_architecture_case.py` | 讲解脚本 | 无需安装 | 三层案例架构讲解 |
| `02_production_check.py` | 讲解脚本 | 无需安装 | 上线自检清单 |
| `README.md` | 说明 | - | 本目录说明 |

## 运行方式

### 离线讲解（无需安装）

```bash
python client_agent.py
python 01_architecture_case.py
python 02_production_check.py
```

### 真实 Server（需已安装 mcp）

```bash
pip install mcp
python server_shop.py
# 或调试: uv run mcp dev server_shop.py
```

## 说明

- `server_shop.py` 是完整业务 Server：`list_items` / `order_item` 工具、`inventory://items` 资源、`place_order_guide` 提示词
- `client_agent.py` 用规则函数模拟 LLM 决策，跑通「发现→决策→调用→回填」闭环；真实场景换 LLM tool calling 即可
- `02_production_check.py` 是照 9 天要点整理的「上线前 checklist」