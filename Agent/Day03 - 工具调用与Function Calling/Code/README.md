# Day03 - 代码运行说明

本文件夹实现**工具定义、注册表、参数校验与 Function Calling 完整往返**。

## 运行环境

- 纯 Python 标准库，无第三方依赖

## 文件说明与运行

| 文件 | 说明 | 运行 |
|------|------|------|
| `01_tool_schema.py` | 工具定义好坏对比 + 函数自动转 Schema | `python 01_tool_schema.py` |
| `02_tool_registry.py` | 注册表：注册/路由/清单生成/错误处理 | `python 02_tool_registry.py` |
| `03_param_validate.py` | 五类参数校验与可指导的错误信息 | `python 03_param_validate.py` |
| `04_tool_roundtrip.py` | Function Calling 六阶段完整往返（最小真 Agent） | `python 04_tool_roundtrip.py` |

## 典型输出速览

```
# 02_tool_registry.py
  幻觉工具: {'error': "未知工具 'query_weather'", 'available': ['query_sales', 'calc', ...]}

# 03_param_validate.py
[格式幻觉(编造周次)] 输入 {'week': '上周'}
  ❌ 拒绝
    - 参数 'week' 格式错误：需匹配 ^\d{4}-W\d{2}$，示例：['2024-W03']

# 04_tool_roundtrip.py
[Step 1] 模型决策 -> 调用 query_sales({"week": "2024-W02"})
           执行结果: {"week": "2024-W02", "sales": 980, "orders": 290}
...
[Step 4] 模型最终回答：W02 销量 980（订单 290），环比 W01（1200）下跌 18.33%。
```

## 切换到真实 LLM

`04_tool_roundtrip.py` 中的 `SimLLM` 与 OpenAI tool_calls 结构对齐，替换方法：

```python
# pip install openai
from openai import OpenAI
client = OpenAI()  # 需设置 OPENAI_API_KEY

class RealLLM:
    def chat(self, messages, tools):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[{"type": "function", "function": t} for t in tools],
        )
        msg = resp.choices[0].message
        return {"role": "assistant", "content": msg.content,
                "tool_calls": [{"id": c.id, "name": c.function.name,
                                "arguments": json.loads(c.function.arguments)}
                               for c in (msg.tool_calls or [])]}
# Agent 循环代码完全不变
```

## 核心结论

1. **模型只出意图**（工具名+参数的 JSON），执行永远在你的代码里。
2. **描述即文档**：name/description/Schema 质量决定工具选用准确率。
3. **校验是第一道闸**：必填/类型/枚举/格式/范围，错误信息要可指导。
4. **往返即循环**：六阶段接上 Day02 核心循环 = 完整 Agent。