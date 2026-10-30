# Day11 代码说明

所有脚本均**离线可运行**。

## 运行方式

```bash
cd "Agent/Day11 - 生产部署与最佳实践/Code"

python 01_canary_release.py       # 灰度发布
python 02_prompt_versioning.py    # Prompt 版本管理与 A/B 测试
python 03_rollback.py            # 回滚策略
python 04_cost_optimization.py   # 成本优化
```

## 文件说明

| 文件 | 内容 | 关键概念 |
|------|------|---------|
| `01_canary_release.py` | 流量按 5%->20%->50%->100% 灰度推进、成功率/P99/成本三项指标对比、自动回滚决策 | 金丝雀发布 |
| `02_prompt_versioning.py` | Prompt 版本库、draft->review->rc->stable 状态流转、A/B 评估与 ROI 决策 | Prompt 即代码 |
| `03_rollback.py` | 回滚触发器、三层资源处理（流量/数据兼容/存量任务排空）、回滚演练计时 | 回滚策略 |
| `04_cost_optimization.py` | 精确+语义缓存（Jaccard 模拟相似度）、模型分级路由、上下文压缩 | 成本工程 |

## 观察要点

**01_canary_release.py**
- 场景 1：优秀的新版本逐级推进到 100%
- 场景 2：有问题的新版本在 5% 阶段就被识破（成功率/P99/成本任一超标），立即回滚

**02_prompt_versioning.py**
- 三个版本各有状态与变更说明（changelog）
- A/B 决策不只看成功率：`token费 + 失败修正费` 的综合成本模型
- 注意：失败的人工修正成本（2元/次）远大于 Token 费

**03_rollback.py**
- 回滚三层：流量秒级切换、v2 数据字段降级映射（reason_v2 -> reason）、存量任务进排空模式
- 演练验证：切换耗时 < 60s、数据兼容、任务处理三项检查

**04_cost_optimization.py**
- "今天北京的天气怎么样" 第二次问精确命中；"北京今日天气如何" 语义命中（相似度 >= 0.6）
- 分级路由对 5 个混合任务节省约 40%+ 成本
- 20 条对话历史压缩成 1 句摘要 + 最近 2 轮，Token 大幅下降

## 生产对应关系

| 演示实现 | 生产替代 |
|---------|---------|
| `CanaryController` | 网关流量切分（Nginx/网关配置或发布平台） |
| `PromptRegistry` | Langfuse / PromptHub / Git 仓库 |
| `RollbackManager` | 发布平台一键回滚 + DB 迁移脚本 |
| `SemanticCache` | GPTCache / Redis + 向量检索 |
| `ModelRouter` | LiteLLM 路由 / 自建调度层 |
