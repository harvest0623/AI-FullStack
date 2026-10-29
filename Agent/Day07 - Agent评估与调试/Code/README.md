# Day07 - 代码运行说明

本文件夹实现 Agent 的**评估指标、轨迹调试、失败模式与 A/B 实验**。

## 运行环境

- 纯 Python 标准库，无第三方依赖

## 文件说明与运行

| 文件 | 说明 | 运行 |
|------|------|------|
| `01_eval_metrics.py` | 结果/过程/成本三层指标计算与报告 | `python 01_eval_metrics.py` |
| `02_trajectory_debug.py` | 轨迹自动体检：标红可疑步骤+二分定位 | `python 02_trajectory_debug.py` |
| `03_failure_modes.py` | 五大失败模式复现与对策（故障手册） | `python 03_failure_modes.py` |
| `04_ab_compare.py` | A/B 对比实验框架 + 失败模式迁移检查 | `python 04_ab_compare.py` |

## 典型输出速览

```
# 01_eval_metrics.py
[结果指标]
  任务成功率        4/6 = 67%
[过程指标]
  平均步数(成功)    4.8
  平均步数(失败)    5.5

# 02_trajectory_debug.py
Step 2   ⚠ 忽视错误
  Thought    : 上月是 1200。   <- 编造数字
第一个可疑步骤：Step 2（query W02 返回 timeout）

# 04_ab_compare.py
指标         A(旧Prompt)      B(新Prompt)      变化
成功率       60%              80%              ↑
```

## 核心结论

1. **三层指标**：结果（成功率/超限率）、过程（步数/重试率）、成本（token/延迟）。
2. **轨迹调试**：规则体检（忽视错误/无据数字/未验证事实）→ 二分定位 → 单步重放。
3. **五大失败模式**：死循环、幻觉工具、参数幻觉、过早放弃、观察误读——执行层工程硬防，认知层 Prompt 软治。
4. **A/B + 回归**：固定评估集与种子；看指标也看失败模式迁移；改动必跑评估集。