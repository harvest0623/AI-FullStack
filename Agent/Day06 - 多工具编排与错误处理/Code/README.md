# Day06 - 代码运行说明

本文件夹实现**多工具编排**：选择路由、并行调用、错误重试与成本预算。

## 运行环境

- 纯 Python 标准库，无第三方依赖

## 文件说明与运行

| 文件 | 说明 | 运行 |
|------|------|------|
| `01_tool_selection.py` | 两级路由（先选域再选工具）+ 负面描述 | `python 01_tool_selection.py` |
| `02_parallel_tools.py` | 并行调用、tool_call_id 关联回填、部分失败 | `python 02_parallel_tools.py` |
| `03_error_retry.py` | 错误五分类 + 退避重试 + 策略分派 | `python 03_error_retry.py` |
| `04_cost_control.py` | 四道预算闸 + 超限降级 + 工具结果缓存 | `python 04_cost_control.py` |

## 典型输出速览

```
# 02_parallel_tools.py
模型一次输出 3 个 tool_calls：
  call_a  query_sales({"region": "north"})
  ...
并发执行完成：0.31s（串行需 ~0.6s+）

# 03_error_retry.py
瞬时故障（服务过载）    -> transient   => 指数退避重试，上限 3 次
权限不足                -> permission  => 不重试！升级人工处理

    第 1 次失败(503)，退避 0.1s 后重试...
    第 2 次失败(503)，退避 0.2s 后重试...
  最终结果：{'week': '2024-W03', 'sales': 1450}（共尝试 3 次）

# 04_cost_control.py
Step 3: steps 3/3  tokens 240/200  ...
[降级-收敛] 步数超限。停止探索，立即总结：已查明本月销量 1450
```

## 核心结论

1. **选择准确性**：两级路由（域→工具）+ 动态注入子集 + 负面描述，N 选 1 降维。
2. **并行编排**：一次决策多个 tool_calls，并发执行按 ID 回填；部分失败显式回填交模型决策。
3. **错误分类决定策略**：参数错→改参数；瞬时错→退避重试；权限/幻觉→快速失败上报。
4. **预算四道闸**：步数/token/调用数/金额，超限要降级输出（保留进展），缓存要配 TTL。