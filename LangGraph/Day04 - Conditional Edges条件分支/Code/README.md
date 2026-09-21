# Day04 Code - Conditional Edges 条件分支

本目录包含 Day04「Conditional Edges 条件分支」的配套脚本：条件边基础、规则路由模式、LLM 语义路由。

## 环境准备

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv pydantic
```

> `03_llm_router.py` 调用 LLM，需要 `.env` 配 `OPENAI_API_KEY`；未配置时自动降级为规则判断。`01`、`02` 不调 LLM。

## 文件说明

| 文件 | 用途 | 关键概念 |
| --- | --- | --- |
| `01_conditional_edges.py` | 条件边基础 | `add_conditional_edges`、path_map(state)、按 risk_level 路由 |
| `02_router_pattern.py` | 规则路由模式 | 分类/路由解耦、直接返节点名 vs if-else、fallback |
| `03_llm_router.py` | LLM 语义路由 | ChatOpenAI、PydanticOutputParser、结构化分类、获取 verdict |

## 运行方式

```bash
python 01_conditional_edges.py
python 02_router_pattern.py
python 03_llm_router.py
```

## 核心代码速览

### 1. 条件边完整写法

```python
def route(state): return state["risk_level"]          # state -> 路径名

g.add_conditional_edges("screen", route, {
    "low": "pass_node",
    "high": "review_node",
})
```

### 2. 无条件 fallback

```python
def route(state):
    return {"a": "n1", "b": "n2"}.get(state["k"], "default_node")
```

### 3. LLM 语义路由 + Pydantic 结构化输出

```python
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class Verdict(BaseModel):
    is_violation: bool
    severity: str

parser = PydanticOutputParser(pydantic_object=Verdict)
clf = parser.invoke(llm.invoke(prompt + parser.get_format_instructions()))
```

## 常见问题

- **报错 No node 匹配** → 核对 path_map 返回值都存在于 mapping（或直接是节点名）
- **path_map 位置错误** → 它是 `add_conditional_edges` 的第 2 个参数
- **没走到预期分支** → 用 `stream_mode="updates"` 看实际路由结果
- **想并行去多个节点** → 让 path_map 返回 `["n1", "n2"]`

## 下一步

阶段一（图基础）完成。接下来进入 Day05 用 Checkpointer 为图加持久化与断点恢复。