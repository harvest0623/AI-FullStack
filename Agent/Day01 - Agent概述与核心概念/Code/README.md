# Day01 - 代码运行说明

本文件夹演示 Agent 的**定义、四大组成与自主性等级**。

## 运行环境

- 无需任何第三方依赖（纯 Python 标准库）

## 文件说明与运行

| 文件 | 说明 | 运行 |
|------|------|------|
| `01_agent_intro.py` | Chatbot vs Agent 处理同一问题的行为对比（幻觉 vs 查证） | `python 01_agent_intro.py` |
| `02_agent_anatomy.py` | 四大组成（大脑/工具/记忆/规划）的最小骨架 | `python 02_agent_anatomy.py` |
| `03_autonomy_levels.py` | L0-L4 自主性等级的行为模拟 | `python 03_autonomy_levels.py` |

## 典型输出速览

```
# 01_agent_intro.py
Agent 轨迹：
  [Thought   ] 用户问上周销量，我不能凭记忆回答，先查数据库。
  [Action    ] query_sales(week='2024-W02')
  [Observation] {"week": "2024-W02", "sales": 980, "orders": 290}
  ...
回答：2024-W02 销量 980（订单 290），相比 W01 的 1200 实际下跌了 18.3%。
```

```
# 02_agent_anatomy.py
目标：对比近两年新能源汽车销量趋势
规划：['搜索获取资料', '计算关键指标', '综合对比并总结']
Step 1/3：搜索获取资料
  [Thought] 需要外部能力 -> 调用工具 search({'query': '2024 新能源汽车销量数据'})
  ...
```

## 核心结论

1. **Agent vs Chatbot**：Chatbot 输出文本（可能幻觉）；Agent 调用工具拿到可验证的观察再回答。
2. **Agent vs Workflow**：Workflow 路径由开发者预定义；Agent 路径由 LLM 运行时决定。
3. **四大组成**：工具=双手、记忆=经验、规划=路线图、LLM=大脑。
4. **自主性分级**：L0 反射 → L4 全自治；自主性与风险成正比，从 L1/L2 起步。