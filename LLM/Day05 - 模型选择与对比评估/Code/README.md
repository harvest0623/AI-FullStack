# Day05 Code - 模型选型与对比评估代码

本目录提供 4 个可独立运行的 Python 脚本，覆盖模型对比、基准测试、模型路由、成本延迟分析四大工程化场景。所有脚本围绕 `AISearch` 项目的"选型决策"环节展开。

---

## 环境准备

```bash
pip install openai anthropic python-dotenv
```

在 `d:\Coding\AI-FullStack\LLM` 或项目根目录创建 `.env`：

```
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxx
```

> 未配置的 Key 对应模型会自动跳过，不会中断运行。

---

## 文件清单

### `01_model_comparison.py` — 多模型输出对比工具

**核心类**：`ModelComparator`、`ComparisonReport`、`ModelResult`

**功能**：对同一 prompt 调用多个模型，并排展示输出质量、响应时间、Token 消耗与估算成本。

**对比维度**：

| 维度 | 字段 |
|------|------|
| 输出质量 | `output` 全文 |
| 响应时间 | `latency_sec` |
| Token 消耗 | `prompt_tokens` / `completion_tokens` / `total_tokens` |
| 成本 | `cost_usd`（按价格表计算） |

**使用示例**：

```python
from importlib import util
import sys
sys.path.insert(0, ".")
# 直接 import 同目录模块
spec = util.spec_from_file_location("mc", "01_model_comparison.py")
mc = util.module_from_spec(spec)
spec.loader.exec_module(mc)

comparator = mc.ModelComparator()
comparator.register_openai("gpt-4o-mini")
comparator.register_openai("gpt-4o")
comparator.register_anthropic("claude-3-5-sonnet-20240620")
report = comparator.compare("用一句话解释 RAG")
print(report.render())
```

直接运行：`python 01_model_comparison.py`

---

### `02_benchmark_runner.py` — 基准测试运行器

**核心类**：`BenchmarkRunner`、`TestCase`、`BenchmarkReport`、`TaskType`

**功能**：内置分类/推理/代码/创作各 5 题共 20 题测试集，批量调用模型，自动判分，输出 Markdown 报告。

**判分策略**：

| 策略 | 含义 | 适用 |
|------|------|------|
| `contains` | 输出包含期望关键词 | 创作题、代码题 |
| `exact` | 完全匹配 | 分类题、推理题 |
| `regex` | 正则匹配 | 复杂格式校验 |
| `llm` | LLM-as-Judge（需自行扩展） | 主观题 |

**自定义测试集**：

```python
runner = BenchmarkRunner(model="gpt-4o")
my_cases = [
    runner.__class__ and TestCase("MINE-01", TaskType.CLASSIFY, "...", "正面"),
]
report = runner.run(my_cases)
print(report.to_markdown())
```

直接运行：`python 02_benchmark_runner.py`（可通过环境变量 `BENCHMARK_MODEL` 切换模型）

---

### `03_model_router.py` — 模型路由器

**核心类**：`ModelRouter`、`RouterConfig`、`RouteDecision`

**两种路由**：

| 路由方式 | 方法 | 是否调用 LLM | 优点 |
|---------|------|------------|------|
| 规则路由 | `route_static()` | 否 | 零成本、可解释 |
| 动态路由 | `route_dynamic()` | 是（小模型） | 更精准降本 |

**路由决策维度**：任务类型 / 输入长度 / 用户分级（free/vip）/ 复杂度（动态路由）。

**示例**：

```python
router = ModelRouter()
# 规则路由
d = router.route_static("证明根号2是无理数")
# 动态路由（先调 mini 判复杂度再升级）
d = router.route_dynamic("证明根号2是无理数")
print(d.model, d.reason)
```

直接运行：`python 03_model_router.py`

---

### `04_cost_latency_analysis.py` — 成本与延迟分析

**核心类**：`CostLatencyAnalyzer`、`LatencyRecord`、`LatencyReport`

**测量指标**：

| 指标 | 含义 | 测量方式 |
|------|------|---------|
| TTFT | 首字延迟 | 流式首 chunk 到达时间 |
| 生成速度 | tokens/s | 输出 token 数 / 生成时长 |
| 总延迟 | 请求总耗时 | 起止时间差 |
| Token 消耗 | 输入/输出 token | 流式 usage 字段 |
| 成本 | 单次 $ | 价格表计算 |
| 月度成本 | 30 天估算 | `estimate_monthly_cost()` |

**使用示例**：

```python
analyzer = CostLatencyAnalyzer()
analyzer.register_openai("gpt-4o-mini")
analyzer.register_openai("gpt-4o")
report = analyzer.measure("用 100 字解释 RAG", repeat=3)
print(report.to_markdown())
print(analyzer.estimate_monthly_cost(report.records, daily_requests=2000))
```

直接运行：`python 04_cost_latency_analysis.py`

---

## 模型选型决策指南

### 各模型能力雷达图数据（5 分制，主观评估）

| 模型 | 推理 | 代码 | 创作 | 多语言 | 多模态 | 指令遵循 | 长上下文 | 速度 | 性价比 |
|------|------|------|------|--------|--------|---------|---------|------|--------|
| GPT-4o | 4.5 | 4.5 | 4.5 | 4.5 | 5.0 | 4.5 | 4.0 | 4.5 | 3.5 |
| GPT-4o-mini | 3.0 | 3.5 | 3.5 | 4.0 | 3.5 | 4.0 | 4.0 | 5.0 | 5.0 |
| o1 | 5.0 | 4.5 | 3.5 | 4.0 | 1.0 | 3.5 | 4.0 | 1.5 | 1.5 |
| Claude 3.5 Sonnet | 4.5 | 5.0 | 4.5 | 4.0 | 3.5 | 4.5 | 4.5 | 4.0 | 3.5 |
| Gemini 1.5 Pro | 4.0 | 4.0 | 4.0 | 4.5 | 5.0 | 4.0 | 5.0 | 4.0 | 4.0 |

### 选型决策树

```
1. 是否隐私敏感？
   是 → 开源本地部署（Llama 3 / Qwen 2.5）
   否 → 2. 是否超长上下文（>200K）？
        是 → Gemini 1.5 Pro / Claude 3.5
        否 → 3. 是否复杂推理？
             是 → o1 / Claude 3.5
             否 → 4. 是否高并发低成本？
                  是 → GPT-4o-mini / Qwen-Turbo
                  否 → GPT-4o / Claude 3.5 Sonnet
```

### 价格对比表（示例，以官方为准）

| 模型 | 输入 ($/1M) | 输出 ($/1M) | 1K 请求成本（1K+1K） |
|------|------------|------------|---------------------|
| GPT-4o-mini | 0.15 | 0.6 | $0.00075 |
| Gemini 1.5 Pro | 1.25 | 5 | $0.00625 |
| GPT-4o | 2.5 | 10 | $0.0125 |
| Claude 3.5 Sonnet | 3 | 15 | $0.018 |
| o1 | 15 | 60 | $0.075 |

### A/B 测试方法论

1. **流量分桶**：按 `user_id` 哈希分桶，确保同一用户始终在同一组。
2. **样本量**：每组 ≥ 1000，避免偶然波动；小效应需更大样本。
3. **指标**：
   - 业务：任务完成率、用户满意度、留存率
   - 工程：延迟 P50/P95、成本、错误率
4. **统计检验**：用卡方/t 检验，p < 0.05 才下结论。
5. **避坑**：避免过早停止；避免只看单一指标；警惕辛普森悖论。

### 模型切换迁移指南

| 迁移方向 | 关键差异 | 迁移要点 |
|---------|---------|---------|
| OpenAI → Claude | system 参数位置不同；max_tokens 必填 | 调整消息结构；补充 max_tokens |
| OpenAI → 通义千问 | OpenAI 兼容入口 | 改 base_url；模型名换为 qwen-* |
| OpenAI → Gemini | SDK 与消息结构差异大 | 重写调用层；图像传入方式不同 |
| API → 本地（Ollama） | 速度/能力下降 | 提示词需重新调优；降低期望 |

---

## 常见问题

**Q1：脚本运行报 `RateLimitError`？**
A：调小并发或加 `time.sleep(1)`；正式项目用 Day07 的限流器。

**Q2：通义千问怎么接？**
A：用 `register_openai(model, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")`，Key 用 `DASHSCOPE_API_KEY`。

**Q3：价格表过期怎么办？**
A：直接修改脚本顶部的 `MODEL_PRICING` 字典，以官方最新定价为准。
