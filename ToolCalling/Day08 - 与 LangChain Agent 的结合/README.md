# Day08 - 与 LangChain / Agent 的结合

> 把工具调用桥接到 LangChain 的思路，并自建一个复用 Day06 循环的最小 Agent，最后用统一抽象封装"工具注册"。

---

## 1. LangChain 中的思路

LangChain 提供 `bind_tools` 把 Python 函数/装饰器转成模型可用的工具，并自动生成 tool 消息：

```python
# 伪代码（示意）
model = SomeChatModel(...)
tools = [get_weather, get_time]          # 直接给函数
model_with_tools = model.bind_tools(tools)

resp = model_with_tools.invoke("北京天气")
# resp.tool_calls → [{'name':'get_weather','args':{...}}]
```

- **bind_tools**：读函数签名/docstring 生成工具 schema（对应 Day03 的思路）
- **ToolNode / ToolMessage**：LangGraph 里把执行结果包成 tool 消息回填
- 底层同样是"tools 传入 + tool_calls 返回 + tool 角色回填"

> 框架没有发明新机制，只是把 Day04-06 的循环与规范**封装成工具 API**。理解本质后可平滑迁移。

---

## 2. 自建最小 Agent（复用 Day06 循环）

不依赖框架，也能用 Day06 的 `run_loop` 搭一个最小 Agent。只需给循环加上：

- **记忆**：把历史 tool 消息一直保留在 `messages` 里
- **规划**：多轮迭代，让模型一步步拆解

```
while 未到 MAX 且仍有 tool_calls:
    模型决策 → 执行工具 → 回填 → 继续
```

这就是"能自主完成多步任务"的最简形态。

---

## 3. 统一工具抽象

为了工程化，把"函数"和"工具描述"统一封装：

```python
class Tool:
    def __init__(self, fn, description=None):
        self.fn = fn
        self.schema = to_schema(fn, description)   # Day03 思路
        self.registry_name = fn.__name__

    def run(self, **kwargs):
        return self.fn(**kwargs)

# 注册中心
class ToolRegistry:
    def __init__(self): self._t = {}
    def add(self, tool): self._t[tool.registry_name] = tool
    def list_schemas(self): return [t.schema for t in self._t.values()]
    def call(self, name, args): return self._t[name].run(**args)
```

好处：
- 一处定义，多处复用
- 统一生成 schema、统一安全调用、统一错误兜底
- 便于接框架或自建 Agent

---

## 4. 本节小结

- LangChain 用 `bind_tools` / ToolNode 封装了同一条工具调用链路
- 自建 Agent = Day06 循环 + 记忆 + 多步迭代
- 用 `Tool` / `ToolRegistry` 统一抽象，工程更规范、易扩展

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_langchain_bridge.py` | LangChain bind_tools 思路示意 |
| `02_mini_agent.py` | 自建最小 Agent（复用循环+记忆） |
| `03_tool_abstraction.py` | Tool / ToolRegistry 统一抽象 |
| `README.md` | 本目录说明 |

均**离线可运行**（不依赖 langchain 真实安装）。