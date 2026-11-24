# Day09 - 与 Agent/工作流集成

> 本节目标：把 "Function Calling 循环" 封装成一个可复用的 **Agent**，对外只有一个
> `run(question)` 接口，内部自动完成"理解 → 选工具 → 执行 → 再思考 → 结论"。
> 这就是 RAG/ReAct/AutoGen 背后的雏形。

---

## 1. 从工具到 Agent 的封装

前面我们手写 planner、手动调用 `chat_with_tools`。生产上更想要一个统一对象：

```python
class ToolAgent:
    def __init__(self, registry): self.reg = registry
    def run(self, question): return self.llm.chat_with_tools(question, self.reg)

agent = ToolAgent(registry)
agent.run("北京天气怎么样")
```

调用方只关心 `run()`，Agent 内部自动决定要不要用工具、用哪个。

---

## 2. 统一决策器=简易 ReAct

`ToolAgent._decide` 是一套**通用规则**，实现"选工具"：

```python
if "get_weather" not in done and "天气" in question:
    return ("call", [{"name":"get_weather", "args":{...}}])   # 需要工具 -> 调用
if tool_msgs:                                                  # 已有结果
    return ("text", f"结果: {tool_msgs[-1]['content']}")      # -> 总结回答
```

这套"要不要用工具 / 用什么 / 拿到结果后怎么总结"的逻辑，正是 ReAct
(Reason + Act) 的精神：**先想→再动→再想**。

---

## 3. 工作流(多步)视角

Agent 内部通过查看**工具历史** (`done` 列表) 决定下一步：

```
step1: 未查天气且问题含城市 -> 调 get_weather
step2: 已有工具结果 -> 汇总回答
```

换成真实 LLM：它会自然地对整个含 tool 结果的历史"再思考"一步，天然支持
复杂工作流，无需手写 step 分支。本模块用规则逼近同样的效果。

---

## 4. 为什么重要

- **解耦**：业务方只管 `run()`，不管函数调用细节。
- **可复用**：换一批工具、换一个 LLM，Agent 骨架不变。
- **衔接**：这层封装就是 ReAct / ToolCalling / AutoGen / LangGraph 的公共底座。

---

## 5. 本节练习

[09-agent.py](Code/09-agent.py) 封装 `ToolAgent`（持有 天气/算数 工具 + 通用决策器），
调用 `run()` 完成两段独立问答并断言。

```bash
python "Day09 - 与Agent工作流集成/Code/09-agent.py"
```

---

## 6. 你要记住的三句话

1. Agent = Function Calling 循环的一个**封装对象**，对外 `run()`。
2. 统一决策器实现 ReAct 精神：需要就调、有结果就总结。
3. 靠工具历史推进多步工作流，这就是复杂 Agent 的底层雏形。

下一节：**实战整合 + 评估**——把全部能力拼成一个完整小助手。