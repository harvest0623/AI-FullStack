# Day11 Code - 评估与监控指南

本目录提供 LLM 评估与监控的完整工具链，从指标计算、LLM-as-Judge、自动化评估管道到生产监控，为 AISearch 智能问答服务构建可持续运营的评估监控能力。

## 环境准备

```bash
# Python 依赖
pip install openai

# 环境变量
export OPENAI_API_KEY=sk-your-key          # LLM-as-Judge 需要
export OLLAMA_BASE_URL=http://localhost:11434/v1  # 被评估的本地模型
```

## 文件说明

| 文件 | 说明 | 运行命令 |
| --- | --- | --- |
| `01_eval_metrics.py` | 评估指标计算（准确率/BLEU/ROUGE/格式合规） | `python 01_eval_metrics.py` |
| `02_llm_judge.py` | LLM-as-Judge 多维度评分 | `python 02_llm_judge.py` |
| `03_eval_pipeline.py` | 自动化评估管道（批量+趋势追踪） | `python 03_eval_pipeline.py` |
| `04_monitoring.py` | 生产监控数据采集与告警 | `python 04_monitoring.py` |

## 评估方法论

### 评估维度选择

| 应用类型 | 核心维度 | 推荐方法 |
| --- | --- | --- |
| 知识问答 | 准确性 | 包含匹配 + LLM-as-Judge |
| RAG 问答 | 准确性 + 忠实性 | LLM-as-Judge（加上下文） |
| 代码生成 | 功能正确性 | 单元测试 |
| 摘要 | 流畅性 + 关键信息 | ROUGE + 人工 |
| 对话 | 相关性 + 流畅性 | MT-Bench 风格 |

### 评估数据集构建指南

1. **来源**：优先使用真实用户对话（脱敏），辅以人工构造
2. **分层**：简单 40% / 中等 40% / 困难 20%
3. **标注**：每条标注期望输出与评分标准
4. **规模**：50-200 条即可有效评估
5. **维护**：每月更新，补充失败案例

### 评估数据集格式

```jsonl
{"question": "什么是 RAG？", "expected": "检索增强生成", "system": "你是助手", "difficulty": "easy"}
{"question": "对比 RAG 和微调的区别", "expected": "RAG 实时检索，微调内化知识", "difficulty": "medium"}
```

## LLM-as-Judge 最佳实践

### Prompt 设计原则

1. **明确评分标准**：每个分值有清晰描述
2. **结构化输出**：要求 JSON 格式便于解析
3. **提供参考答案**：提升评分一致性
4. **随机化顺序**：避免位置偏见
5. **控制长度**：避免长度偏见

### 偏见应对

| 偏见 | 应对策略 |
| --- | --- |
| 位置偏见 | 随机打乱候选顺序 |
| 长度偏见 | 限制输出长度 |
| 自我偏好 | 使用多个裁判模型交叉验证 |
| 评分偏高 | 强制分布（要求一定比例低分） |

### 多裁判交叉验证

```python
# 使用多个模型作为裁判，取平均
judges = [LLMJudge(model="gpt-4o"), LLMJudge(model="claude-3-opus")]
scores = [j.judge(q, a, ref).scores for j in judges]
# 取各维度平均分
```

## 监控仪表盘设计

### 核心指标卡片

| 指标 | 阈值 | 告警 |
| --- | --- | --- |
| P95 延迟 | < 5s | 超过则警告 |
| 日成本 | < 预算 | 超过 120% 严重 |
| 错误率 | < 5% | 超过 10% 严重 |
| 满意度 | > 80% | 低于则警告 |
| 有害率 | < 1% | 超过则严重 |

### Grafana / Prometheus 集成

`04_monitoring.py` 的 `to_prometheus()` 方法输出标准 Prometheus 格式指标，可直接被 Prometheus 抓取，并在 Grafana 中可视化。

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'llm-monitor'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']  # 暴露 /metrics 的服务
```

## 告警配置建议

### 告警级别

| 级别 | 响应时效 | 通知方式 |
| --- | --- | --- |
| Critical | 立即（<5min） | 电话 + 短信 + IM |
| Warning | 30 分钟内 | IM + 邮件 |
| Info | 4 小时内 | 邮件 |

### 告警规则示例

```python
# 添加自定义告警规则
monitor.add_alert_rule(AlertRule(
    name="月成本预警",
    metric="daily_cost",
    threshold=3000.0,
    comparison=">",
    severity="critical",
    message="月成本趋势将超预算",
))
```

### 告警降噪

- 同一规则 5 分钟内只告警一次
- Critical 级别合并通知
- 设置维护窗口（发布期间静默）

## 漂移检测方法

| 漂移类型 | 检测频率 | 方法 |
| --- | --- | --- |
| 概念漂移 | 每周 | 用户意图分类分布卡方检验 |
| 数据漂移 | 每日 | 输入长度/主题分布对比 |
| 模型漂移 | 每次更新 | 更新前后行为对比（A/B） |

## 常见问题

**Q: LLM-as-Judge 评分不稳定？**
降低 temperature 至 0，提供详细评分标准，使用多个裁判取平均。

**Q: 评估数据集太小不够代表性？**
50-200 条即可有效评估，关键是覆盖多样场景与难度。优先保证质量与分层。

**Q: 监控指标如何暴露给 Prometheus？**
在 FastAPI 服务中添加 `/metrics` 端点，调用 `monitor.to_prometheus()` 返回文本。
