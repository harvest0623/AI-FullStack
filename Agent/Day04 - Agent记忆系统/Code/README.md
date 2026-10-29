# Day04 - 代码运行说明

本文件夹实现 Agent 的**三层记忆、历史管理、长时存储与打分淘汰**。

## 运行环境

- `03_longterm_store.py` 需要 numpy；其余纯标准库

```bash
pip install numpy
```

## 文件说明与运行

| 文件 | 说明 | 运行 |
|------|------|------|
| `01_memory_layers.py` | 工作记忆/短时记忆/长时记忆三层协作 | `python 01_memory_layers.py` |
| `02_history_mgmt.py` | 滑动窗口 vs 摘要压缩 vs 混合策略 | `python 02_history_mgmt.py` |
| `03_longterm_store.py` | 长时记忆写入、关键词+语义检索、注入上下文 | `python 03_longterm_store.py` |
| `04_memory_score.py` | 重要性打分、召回强化、时间衰减与淘汰 | `python 04_memory_score.py` |

## 典型输出速览

```
# 02_history_mgmt.py
[策略1 滑动窗口(保留4)] 共 5 条，估算 xx tokens
  ⚠ 丢了首条 user（任务目标），Agent 会『忘记自己要干嘛』
[策略3 混合策略(生产)] ...
  ✅ 目标+摘要+最近细节+工具结果截断

# 04_memory_score.py
  [淘汰] 容量超限，移除低分记忆：'昨天聊了个周末计划…' (score=...)

# 03_longterm_store.py
2) 语义检索：'用户喜欢怎么被称呼'（无字面重叠）
  score=...  用户称呼为张工 ...
```

## 核心结论

1. **三层记忆**：工作（单步草稿）、短时（任务内上下文，窗口受限）、长时（跨会话存储，按需检索）。
2. **短时管理**：纯截断会丢任务目标；生产用混合策略（system+目标+摘要+最近K条+工具结果瘦身）。
3. **长时记忆**：写入（事实/经验）→ 检索（关键词/语义/meta 过滤）→ 注入（克制的 top_k 前缀）。
4. **打分淘汰**：`importance × (1+log(1+use)) × e^(-λΔt)`，召回即强化，低分先出局。