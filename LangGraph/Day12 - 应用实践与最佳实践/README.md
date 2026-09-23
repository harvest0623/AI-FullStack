# Day12 - 应用实践与最佳实践

> 学的不是"跑通一个 demo"，而是"用一套可维护、可测试、可部署的方法论来交付产品"。

## 本章简介

前 11 天我们掌握了 LangGraph 的各类能力，但真实的工程落地还需要把它们组织成**可维护、可测试、可部署**的产品级项目。本章聚焦：横向的**项目架构分层**（状态/节点/图工厂/配置分离）、纵向的**测试方法论**（节点级 / 图级 / mock LLM）、以及面向交付的 **FastAPI 封装**（REST 化 invoke/stream）、**Docker 部署**与**可观测性监控**。最后以一份集成了 Day01–Day11 全部能力的 `GraphFlow` 综合示例收尾，作为整个板块的里程碑作业。

---

## 学习目标

学完本章，你应该能：

- [ ] 按"状态/节点/图工厂/配置"分层组织一个 LangGraph 项目
- [ ] 用图工厂函数 `build_graph(config) -> CompiledGraph` 复用、可配置地构建图
- [ ] 为核心为节点级与图级编写自动化测试，并用 mock LLM 替换真实模型
- [ ] 用 `RunnableConfig` 在运行时传递 `thread_id`/`user_id` 等参数
- [ ] 集成 LangSmith 做链路追踪与调试
- [ ] 用 FastAPI 把图封装成 `/invoke`、`/stream` 的 REST 接口
- [ ] 用 Docker 容器化部署并做健康检查
- [ ] 建立日志、指标、告警构成的可观测体系

---

## 理论知识讲解

### 一、项目架构设计

一个可维护的 LangGraph 项目，建议按层拆分：

```
my_graph_app/
├── state.py            # 状态模型 TypedDict / Reducer
├── nodes.py           # 节点集(单一职责,每个节点独立函数)
├── tools.py           # 工具/外部依赖封装(可选)
├── graphs/
│   └── factory.py     # 图工厂: build_graph(config) -> CompiledGraph
├── config.py          # 配置管理(模型名/参数/线程等)
└── main.py            # 入口/服务封装
```

- **图工厂函数**：`build_graph(config) -> CompiledGraph`，把配置注入图构造，做到"同一份代码、多种配置"。
- **节点模块化**：每个节点独立文件/函数，便于测试与复用。
- **配置分离**：模型名称、`max_attempts`、线程等通过 `config` 传入，不硬编码。

```python
def build_graph(cfg: dict) -> CompiledGraph:
    llm = ChatOpenAI(model=cfg["model"])
    ...
    return builder.compile(checkpointer=cfg_checkpointer(cfg))
```

---

### 二、可测试性

| 层级 | 方式 | 说明 |
|------|------|------|
| 单节点测试 | 直接调用 `node(state, ...)` | 校验节点输入输出 |
| 图集成测试 | `graph.invoke(inputs)` + 断言状态 | 校验整条链路 |
| 快照测试 | 固定输入对比输出 | 回归防护 |
| mock LLM | 测试时替换模型 | 稳定、快、免费 |

```python
def test_audit_node():
    res = audit_node({"input_text": "广告文案"})
    assert "risk" in res

def test_graph():
    out = build_graph(default_cfg).invoke({"input_text": "..."})
    assert out["status"] == "ok"
```

---

### 三、Config 与 RunnableConfig

- `config` 承载**运行时参数**：`thread_id`、`user_id`、`retry` 开关等。
- 节点通过 `config: RunnableConfig` 参数读取 `config["configurable"]`。

```python
def node(state, *, config: RunnableConfig):
    uid = config["configurable"].get("user_id", "anonymous")
    tid = config["configurable"]["thread_id"]
```

> `RunnableConfig` 不仅传业务字段，也会携带 Checkpointer / Store / callbacks 等框架上下文。

---

### 四、LangSmith 追踪集成

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=lsv2_xxx
export LANGCHAIN_PROJECT=graphflow
```

- 设置后，**每次图执行自动上报 trace**（含节点、输入输出、token、错误）。
- 在 LangSmith 面板可调试链路、对比运行耗时、做离线评测。

---

### 五、FastAPI 封装

把图封装为 REST API，暴露 `/invoke` 与 `/stream`：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Req(BaseModel):
    text: str
    thread_id: str = "default"
    user_id: str = "anonymous"

@app.post("/analyze")          # 一次性返回
def analyze(req: Req):
    cfg = {"configurable": {"thread_id": req.thread_id, "user_id": req.user_id}}
    return graph.invoke({"input_text": req.text}, config=cfg)

@app.post("/stream")           # 流式返回
async def stream(req: Req):
    async for chunk in graph.astream(...):
        yield ...
```

- 添加健康检查端点 `/health`。
- 完善异常处理与鉴权/限流（生产）。

---

### 六、Docker 部署

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

- 环境变量通过 `.env` / 运行时注入（`OPENAI_API_KEY` 等）。
- 加健康检查：`docker build` 后 `curl /health`。

---

### 七、可观测性与监控

- **日志**：结构化日志（`logging` JSON 输出）。
- **指标**：延迟、成功率、token 成本——可在节点层用 Callback 统计。
- **告警**：错误率 / 超时率超过阈值触发。

---

### 八、最佳实践总结

| 维度 | 最佳实践 |
|------|---------|
| 状态设计 | 明确覆盖/累积字段，用 Reducer 表达合并意图 |
| 节点设计 | 单一职责，一个节点只做一件事 |
| 约束 | 条件边 fallback 全覆盖，杜绝无路径分支 |
| Checkpointer | 生产必配，支撑记忆/恢复/人工干预 |
| 测试 | 节点级 + 图级双覆盖 |
| 版本与升级 | 状态定义变更谨慎，做好迁移与文档 |

---

## 代码文件说明

| 文件 | 类 | 说明 |
|------|-----|------|
| `Code/01_architecture.py` | `ArchitectureDemo` | 完整项目架构：状态(内聚 typed dict)、节点、图工厂、配置管理的分层示例 |
| `Code/02_testing.py` | `GraphTester` | 图测试框架：节点级/图级、mock LLM、断言；可复用测试模式 |
| `Code/03_fastapi_service.py` | `app` | FastAPI 封装：`POST /analyze`、`POST /stream`、健康检查、错误处理；可 uvicorn 运行 |
| `Code/04_best_practices.py` | `ProductionGraph` | 综合最佳实践：整合记忆+Reducer+Retry+Fallback+Stream+人工干预的完整生产级示例（含交互演示） |
| `Code/README.md` | - | 应用与最佳实践指南：架构设计、测试方法论、FastAPI/Docker 教程、监控、最佳实践清单、路线回顾 |

---

## 关键知识点总结

### 项目架构图

```
main.py ──► graphs/factory.py ──► nodes.py ──► state.py
              (build_graph)        (节点集)       (TypedDict)
                    │
              config.py(models/params) + tools.py
```

### 图工厂函数模式

```python
def build_graph(cfg) -> CompiledGraph:
    # 依据 cfg 选择模型、reducer、checkpointer
    return builder.compile(...)
```

### 测试策略速查

| 目标 | 手法 |
|------|------|
| 节点正确性 | 直接调 `node(state)` 断言 |
| 链路正确性 | `graph.invoke` + 状态断言 |
| 回归防护 | 快照对比固定输入 |
| 测试隔离 | mock LLM 返回固定输出 |

### FastAPI 封装要点

- `/analyze`（一次性）、`/stream`（流式）、`/health`（健康）。
- `RunnableConfig` 注入 thread_id / user_id。
- 统一异常处理 + 兜底响应。

### 部署清单

- 需求冻结 `requirements.txt`；Docker 化；环境变量注入；健康检查；日志/指标/告警。

### 最佳实践总结表

见上文"八、最佳实践总结"。

---

## 实战练习

1. **重构分层**：把某个 Day 的图改造成 `state.py / nodes.py / factory.py / config.py` 四文件结构，并支持通过配置切换模型与 `max_attempts`。
2. **补测试**：对一个含条件边的图，用 mock LLM 分别覆盖"成功""降级""超时"三条路径的图级测试，确保无分支漏测。
3. **FastAPI 全流程**：启动 `03_fastapi_service.py`，用 `curl -X POST /analyze` 和流式 `/stream` 分别验证返回；再写一个 `/health` 探活脚本，模拟部署健康检查。

---

## 参考阅读

- [LangGraph 官方文档 - 部署](https://langgraph-ai.github.io/langgraph/cloud/)
- [LangChain 官方文档 - RunnableConfig](https://python.langchain.com/docs/concepts/runnables/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangSmith 官方文档](https://docs.smith.langchain.com/)