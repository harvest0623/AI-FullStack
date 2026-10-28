# Day02 - 代码运行说明

本文件夹实现 Agent 的**核心循环、ReAct 三元组、终止条件与轨迹记录**。

## 运行环境

- 纯 Python 标准库，无第三方依赖

## 文件说明与运行

| 文件 | 说明 | 运行 |
|------|------|------|
| `01_core_loop.py` | 最小 Agent 循环（感知-思考-行动-观察） | `python 01_core_loop.py` |
| `02_react_pattern.py` | ReAct 三元组（Thought/Action/Observation） | `python 02_react_pattern.py` |
| `03_stop_conditions.py` | 四种终止条件与失控拦截 | `python 03_stop_conditions.py` |
| `04_trajectory.py` | 轨迹记录/JSONL 导出/回放统计 | `python 04_trajectory.py` |

> `04_trajectory.py` 会在当前目录生成 `trajectory_demo.jsonl` 演示落盘。

## 典型输出速览

```
# 01_core_loop.py
  [Step 1] Action=query_sales({'week': '2024-W02'}) -> {"week": "2024-W...
  [Step 2] Action=query_sales({'week': '2024-W01'}) -> ...
  [Step 3] Action=calc({...}) -> {"result": -18.333...}
  [Step 4] 产出最终答案，循环正常退出。

# 03_stop_conditions.py
  [终止-重复] 第3步 连续重复 ('query_sales', '{"week": "2024-W02"}')，判定死循环，停止
  [终止-步数] 达到 max_steps=4，强制停止（进展 4 步）
```

## 核心结论

1. **核心循环**是所有 Agent 框架的心跳：感知→思考→行动→观察循环往复。
2. **ReAct** 让每步都有显式 Thought：可解释、可调试、更准确。
3. **终止条件**是缰绳：Final Answer / max_steps / 重复检测 / 预算耗尽；`max_steps` 永远必设。
4. **轨迹**是黑匣子：含元数据（时间/耗时/token）的 JSONL 落盘，支撑调试、评估与审计。