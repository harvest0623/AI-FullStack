"""
Function Calling 板块共享模拟框架
================================
零依赖重现 OpenAI 风格 Function/Tool Calling 的核心循环，供全板块各章脚本复用：
  - FunctionSpec     一个函数/工具的 schema (name/description/parameters)
  - FunctionRegistry 管理一组函数, 校验参数并执行
  - FunctionCallingLLM  模拟模型：决定直接回答 or 发起(可能并行的)函数调用

设计要点（与真实 API 对齐）：
  真实 OpenAI 流程:
    1. 发消息 + tools 给模型
    2. 模型回复 assistant_message 可能带 tool_calls
    3. 逐个执行函数, 把结果作为 role="tool" 消息加回
    4. 再次发给模型, 直到模型没有 tool_calls
  本框架用一个可注入的 planner 复现这套循环：
    plan(messages, tool_names) -> 选择返回:
       ("text", "直接回答的内容")
       ("call", [{"name":...,   "args":{...}}, ...])   # 可多个=并行
    LLM 类内部处理执行 + 把 tool 结果喂回 + 多轮直到没人再调。

迁移到真实 API: 只需把 LLM 内部改为调用真实模型生成 tool_calls/回复即可,
其余容器(reg.explain_tools/校验/执行消息流)全部复用。

本文件被复制到每个 Day 的 Code/ 目录以保证各章独立可运行。
"""
from __future__ import annotations
import copy
import json
import traceback


class FunctionSpec:
    """描述一个可被模型调用的函数/工具。"""

    def __init__(self, name: str, description: str,
                 parameters: dict | None = None, func=None):
        self.name = name
        self.description = description or ""
        self.parameters = parameters or {
            "type": "object",
            "properties": {},
            "required": [],
        }
        self.func = func  # callable(**kwargs) -> str 或 dict

    def to_openai_tool(self) -> dict:
        """转成 OpenAI 的 tools 表述(仅用于展示/理解)。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __repr__(self):
        return f"<FunctionSpec {self.name}>"


class FunctionCallError(Exception):
    """函数调用过程中的错误(参数/执行/未知函数)。"""
    def __init__(self, message, recoverable=True):
        super().__init__(message)
        self.recoverable = recoverable


class FunctionRegistry:
    """管理一组函数: 解析 + 校验参数 + 执行。"""

    def __init__(self, specs=None):
        self._specs = {s.name: s for s in (specs or [])}

    def add(self, spec: FunctionSpec):
        self._specs[spec.name] = spec
        return self

    def has(self, name: str) -> bool:
        return name in self._specs

    def get(self, name: str) -> FunctionSpec:
        return self._specs[name]

    def names(self) -> list:
        return list(self._specs)

    def explain_tools(self) -> list:
        """给模型看的工具说明(模拟 tools 入参)。"""
        return [s.to_openai_tool() for s in self._specs.values()]

    def execute(self, name: str, args: dict) -> str:
        """执行一个函数: 校验 -> 调用 -> 返回字符串结果。失败抛 FunctionCallError。"""
        spec = self._specs.get(name)
        if not spec:
            raise FunctionCallError(f"未知函数: {name}", recoverable=True)
        checked = self._validate(spec, args or {})
        try:
            value = spec.func(**checked)
        except FunctionCallError:
            raise
        except (TypeError, ValueError) as e:
            raise FunctionCallError(f"{name} 执行报错: {e}", recoverable=True)
        except Exception as e:  # noqa: BLE001 —— 让任何异常都可恢复地回传模型
            raise FunctionCallError(f"{name} 执行异常: {type(e).__name__}: {e}",
                                    recoverable=True)
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    @staticmethod
    def _validate(spec: FunctionSpec, args: dict) -> dict:
        """按 parameters.properties/required 校验参数。缺失必填或类型明显不符时抛错。"""
        props = spec.parameters.get("properties", {})
        required = set(spec.parameters.get("required", []))
        missing = required - set(args)
        if missing:
            raise FunctionCallError(
                f"{spec.name}: 缺少必填参数 {sorted(missing)}", recoverable=True)
        # 类型校验(常见类型)
        for k, v in args.items():
            prop = props.get(k)
            if not prop:
                continue
            t = prop.get("type")
            if t == "string" and not isinstance(v, str):
                raise FunctionCallError(
                    f"{spec.name}: 参数 '{k}' 应为字符串, 实为 {type(v).__name__}",
                    recoverable=True)
            if t in ("number", "integer") and isinstance(v, bool):
                raise FunctionCallError(
                    f"{spec.name}: 参数 '{k}' 应为数字, 实为布尔", recoverable=True)
            if t == "integer" and isinstance(v, float) and not v.is_integer():
                raise FunctionCallError(
                    f"{spec.name}: 参数 '{k}' 应为整数, 实为 {v}", recoverable=True)
            if t == "boolean" and not isinstance(v, bool):
                raise FunctionCallError(
                    f"{spec.name}: 参数 '{k}' 应为布尔, 实为 {type(v).__name__}",
                    recoverable=True)
        return {k: v for k, v in args.items() if k in props or k in required}


class _ToolResult:
    """一次函数执行产生的 tool 消息。"""
    def __init__(self, tool_call_id, name, content):
        self.tool_call_id = tool_call_id
        self.name = name
        self.content = content


class FunctionCallingLLM:
    """模拟模型: 决定直接答 or 调用函数。plan 可注入(接真实模型时替换)。"""

    def __init__(self, plan=None, name="mock-llm"):
        self.name = name
        # plan(conversation, tool_names) -> ("text", content)
        #                              or ("call", [ {"name","args"} ], fallback_text)
        self._plan = plan or self._default_plan

    # ---------- 默认规则 planner ----------
    def _default_plan(self, conv, tools):
        # 找不到合理触发时直接回答
        return ("text", "（未配置决策器，直接回答）")

    # ---------- 主循环 ----------
    def chat_with_tools(self, user_text: str, registry: FunctionRegistry,
                        max_rounds: int = 8):
        """处理一次用户请求, 内部循环"模型->工具->模型"直到无需再调。返回最终文本。"""
        conv = [{"role": "user", "content": user_text}]
        tool_names = registry.names()
        turn = 0
        while turn < max_rounds:
            turn += 1
            decision = self._plan(copy.deepcopy(conv), list(tool_names))
            kind = decision[0]
            if kind == "text":
                return decision[1]

            # 发起(可能并行的)函数调用
            calls = decision[1]
            fallback = decision[2] if len(decision) > 2 else ""
            results = []
            for i, c in enumerate(calls):
                name = c["name"]
                args = c.get("args", {})
                if not registry.has(name):
                    # 模型调了未知函数 -> 塞一条错误 tool 结果
                    results.append(_ToolResult(f"call_{turn}_{i}", name,
                                               f"[error] 未知函数: {name}"))
                    continue
                try:
                    content = registry.execute(name, args)
                except FunctionCallError as e:
                    content = f"[error] {e}" if e.recoverable else f"[fatal] {e}"
                results.append(_ToolResult(f"call_{turn}_{i}", name, content))

            # 把函数调用+结果作为消息追加
            assistant_msg = {
                "role": "assistant",
                "content": fallback or "",
                "tool_calls": [
                    {"id": r.tool_call_id, "name": r.name} for r in results
                ],
            }
            conv.append(assistant_msg)
            for r in results:
                conv.append({"role": "tool", "tool_call_id": r.tool_call_id,
                             "name": r.name, "content": r.content})
        return "达到最大轮次，仍未收敛。"

    # ---------- 直接一次"模型回复" ----------
    def generate_call(self, user_text: str, registry: FunctionRegistry):
        """返回原始决策(便于演示 schema / 解析)。相当于一次模型输出。"""
        conv = [{"role": "user", "content": user_text}]
        return self._plan(copy.deepcopy(conv), list(registry.names()))


# ---------- 常用工具样例 ----------
def tool_get_weather(city: str, unit: str = "C") -> str:
    table = {"上海": "晴, 26°C", "北京": "多云, 18°C", "深圳": "雨, 29°C", "广州": "阴, 30°C"}
    temp = table.get(city, "未知城市")
    return f"{city} 天气: {temp}"


def tool_add(a: float, b: float) -> float:
    return a + b


def tool_search_book(keyword: str) -> list:
    library = {
        "mongo": ["MongoDB 实战", "MongoDB 权威指南"],
        "ai": ["AI 时代", "深度学习"],
    }
    return library.get(keyword.lower(), [])


if __name__ == "__main__":
    # 框架自测: 用规则 planner 触发一次函数调用
    calls_made = []

    def plan(conv, tools):
        if any(t["role"] == "tool" for t in conv):
            # 已经拿到工具结果 -> 总结
            for t in conv:
                if t["role"] == "tool":
                    return ("text", f"好的, 得到: {t['content']}")
        return ("call", [{"name": "get_weather", "args": {"city": "上海"}}])

    from framework_function_calling import (FunctionCallingLLM, FunctionRegistry, FunctionSpec)
    reg = FunctionRegistry()
    reg.add(FunctionSpec("get_weather", "查询天气",
                         {"properties": {"city": {"type": "string"}}, "required": ["city"]},
                         tool_get_weather))
    llm = FunctionCallingLLM(plan=plan)
    out = llm.chat_with_tools("上海天气?", reg)
    print("输出:", out)
    assert "得到" in out
    print("framework_function_calling 框架自测通过 ✓")