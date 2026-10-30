# Day10 代码说明

所有脚本均**离线可运行**（不依赖 FastAPI/OTel 等，用标准库模拟核心概念）。

## 运行方式

```bash
cd "Agent/Day10 - Agent服务化与可观测/Code"

python 01_fastapi_service.py    # Agent 服务化
python 02_trajectory_log.py     # 轨迹日志
python 03_tracing.py            # 链路追踪
python 04_metrics_alert.py      # 指标与告警
```

## 文件说明

| 文件 | 内容 | 关键概念 |
|------|------|---------|
| `01_fastapi_service.py` | 标准库模拟 API 服务：同步 `/chat`、异步 `/tasks`（task_id + 轮询）、线程池 worker、并发任务 | 服务化、异步模式 |
| `02_trajectory_log.py` | 请求级/步骤级/依赖级三层日志、结构化 JSON、失败步骤回放定位 | 轨迹日志 |
| `03_tracing.py` | trace_id 贯穿主 Agent/工具/子 Agent/LLM、span 树、瀑布图渲染、最慢环节定位、错误 span 标记 | 分布式追踪 |
| `04_metrics_alert.py` | Counter/Histogram/Gauge 三类指标、P50/P99 计算、告警规则引擎（P0/P1/P2 分级）、正常与异常流量对比 | 监控告警 |

## 观察要点

**01_fastapi_service.py**
- 同步接口：短任务直接返回完整回答
- 异步接口：提交后立即拿 task_id，轮询看到 `queued -> running -> done` 状态流转和进度
- 3 个任务提交给 2 个 worker：并发消费

**02_trajectory_log.py**
- 输出的 JSON 包含三层：请求级（trace_id/用户/总耗时）、步骤级（3 轮循环的思考/行动/观察）、依赖级（LLM 与工具的原始请求响应）
- 排障演示：从"ERROR: 连接超时"的观察记录定位到失败步骤

**03_tracing.py**
- 瀑巴图中缩进表示父子层级（main_agent 下挂 llm_think、tool_search、tool_db、sub_agent，sub_agent 下还有 llm_write）
- `slowest()` 找出最耗时的 span：优化优先级
- 异常链路中 tool_api 被标记 `[ERROR]`，根因一目了然

**04_metrics_alert.py**
- 场景 1（正常流量）：错误率 5%，无告警触发，延迟分布集中在 1s 内
- 场景 2（供应商故障）：错误率 25%，触发 P0（错误率）+ P1（P99 延迟）+ P1（成本）三类告警
- 注意 Token 消耗在异常场景也升高：重试导致成本翻倍是常见连锁反应

## 生产对应关系

| 演示实现 | 生产替代 |
|---------|---------|
| `AgentService`（标准库模拟） | FastAPI / Flask + Celery/Redis 队列 |
| `RequestLog.to_json()` | 结构化日志 -> ELK / Loki |
| `Tracer` | OpenTelemetry SDK + Jaeger/Tempo |
| `Metrics/AlertRule` | Prometheus + Alertmanager |
