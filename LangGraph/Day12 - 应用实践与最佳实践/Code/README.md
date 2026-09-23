# Day12 Code 说明 —— 应用实践与最佳实践

本章是 LangGraph 板块的收官：把前 11 天能力整合成可维护、可测试、可部署的产品级工程。

## 文件导航

| 文件 | 类/对象 | 演示内容 | 运行 |
|------|---------|---------|------|
| `01_architecture.py` | `ArchitectureDemo` | 分层架构：状态模型 / 节点集 / 配置 / 图工厂 `build_graph(cfg)` | `python 01_architecture.py` |
| `02_testing.py` | `GraphTester` | 测试框架：节点级 / 图集成 / mock LLM | `python 02_testing.py` |
| `03_fastapi_service.py` | `app` | FastAPI：`POST /analyze`、`POST /stream`、`GET /health` | `uvicorn 03_fastapi_service:app --reload` |
| `04_best_practices.py` | `ProductionGraph` | 综合实践：记忆+Reducer+Retry+Fallback+Stream+人工干预 | `python 04_best_practices.py` |

## Running FastAPI

```bash
pip install fastapi uvicorn
uvicorn 03_fastapi_service:app --reload

# 测试接口
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/analyze -H "Content-Type: application/json" \
     -d '{"text":"稳赚不赔点击链接","thread_id":"t1","user_id":"u1"}'
curl -N -X POST http://127.0.0.1:8000/stream -H "Content-Type: application/json" \
     -d '{"text":"稳赚不赔点击链接"}'
```

## 架构分层速查

```
状态模型(TypedDict/reducer)  →  nodes.py
节点集(单一职责函数)          →  nodes.py
图工厂 build_graph(cfg)       →  factory.py
配置管理(model/risk_words/重试) → config.py
```

## 测试要点

- 节点级：直接调用 `node(state)` 断言返回。
- 图级：`graph.invoke(inputs)` 断言最终状态。
- mock LLM：测试时替换真实模型，固定输出 + 计数。

## 综合示例关注

`04_best_practices.py` 一条链路同时体现：
- **短时记忆**：`messages` 用 `add_messages` 累积，Checkpointer 持久化。
- **长时记忆**：人工复核通过后写入 `InMemoryStore`。
- **Reducer**：`add_messages` 有序累积。
- **Retry**：`analyze` 节点配 `RetryPolicy`。
- **Fallback**：低成本规则引擎兜底（LLM 可选）。
- **人工干预**：高风险 `interrupt()` → `Command(resume=...)`。
- **Stream**：`stream_mode="updates"` 逐节点输出。

## 进阶思考

1. 给 `03_fastapi_service` 加鉴权（`API Key` 头校验）与简单限流。
2. 为 `01_architecture` 增加 `SqliteSaver`/`PostgresSaver` 选项，观察持久化。
3. Docker 化：`Dockerfile` + `docker-compose`，注入 `OPENAI_API_KEY` 并做 `/health` 探活。