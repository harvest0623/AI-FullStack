"""
Day02 统一 LLM 封装 llm.py
=============================
提供两类后端, 统一成同一个接口, 后续章节直接复用:

  - OpenAILLM : 通过 openai 兼容接口调用真实模型
                (需要 OPENAI_API_KEY, 或自定义 base_url)
  - MockLLM   : 离线、确定性的模拟 LLM, 无需任何 Key
                由调用方注入一个 decider(决策函数) 模拟模型"思考+行动"

统一回复格式(返回值是一个 dict):
    {"content": "...",                              # 模型输出的文本(可选)
     "tool_calls": [{"name": str, "arguments": dict}]}   # 要调用的工具(可选)

用法(在其它脚本中, 把它所在目录加入 sys.path):
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from llm import OpenAILLM, MockLLM

运行本文件可自测:
  python "Day02 - 环境与 LLM 调用封装/Code/llm.py"
"""
import json
import os
from typing import Any, Callable, Optional


# ---------- 统一回复类型 ----------
def text(content: str) -> dict:
    return {"content": content, "tool_calls": []}


def tool_call(name: str, arguments: dict) -> dict:
    return {"content": "", "tool_calls": [{"name": name, "arguments": arguments}]}


# ---------- 接口基类 ----------
class BaseLLM:
    """所有 LLM 后端的统一接口。"""

    def chat(self, messages: list[dict], tools: Optional[list[dict]] = None,
             temperature: float = 0.7) -> dict:
        raise NotImplementedError

    # 便捷方法: 只取文本
    def text(self, messages, tools=None, temperature=0.7) -> str:
        r = self.chat(messages, tools=tools, temperature=temperature)
        return r.get("content", "")


# ---------- 真实 OpenAI 兼容后端 ----------
class OpenAILLM(BaseLLM):
    def __init__(self, model: str = "gpt-4o-mini", base_url: Optional[str] = None,
                 api_key: Optional[str] = None):
        self.model = model
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("未安装 openai, 请: pip install openai") from e
        self.client = OpenAI(base_url=base_url, api_key=api_key
                             or os.environ.get("OPENAI_API_KEY"))

    def chat(self, messages, tools=None, temperature=0.7) -> dict:
        kwargs = dict(model=self.model, messages=messages, temperature=temperature)
        if tools:
            kwargs["tools"] = tools
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        out = {"content": msg.content or "", "tool_calls": []}
        for tc in (msg.tool_calls or []):
            out["tool_calls"].append({
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments or "{}"),
            })
        return out


# ---------- Mock LLM 后端(离线) ----------
class MockLLM(BaseLLM):
    """
    传给一个 decider 函数来模拟"模型推理 + 行动决策"。

    def my_decider(messages, tools) -> dict:
        last = messages[-1]
        # 看最后的 Observation / 用户输入, 返回 text(...) 或 tool_call(...)
        ...

    messages 中 role 取值: system / user / assistant / tool
    tool role 的 content 是 Observation 结果。
    """
    def __init__(self, decider: Callable[[list[dict], Optional[list[dict]]], dict]):
        self.decider = decider

    def chat(self, messages, tools=None, temperature=0.7) -> dict:
        return self.decider(messages, tools)


# ---------- 便捷工厂: 默认优先真实模型, 无 KEY 回退 Mock ----------
def auto_llm(mock_decider: Optional[Callable] = None, **kw) -> BaseLLM:
    """有 OPENAI_API_KEY 用真实模型, 否则用 Mock(可传 mock_decider)。"""
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAILLM(**kw)
    if mock_decider is None:
        mock_decider = default_decider
    return MockLLM(mock_decider)


def default_decider(messages, tools=None) -> dict:
    """默认空想: 直接礼貌拒绝/复述最后输入, 用于演示不报错。"""
    last = messages[-1]["content"]
    return text(f"(Mock) 我收到了: {last}。可传入自定义 decider 来模拟 ReAct。")


if __name__ == "__main__":
    # 自测: 无 KEY 时走 Mock, 验证接口统一
    llm = auto_llm(
        mock_decider=lambda msgs, tools: text("你好, 我是离线 Mock LLM")
    )
    print("接口气泡:", llm.chat([{"role": "user", "content": "hi"}]))
    print("models:", [m for m in ("gpt-4o-mini", "gpt-4o", "deepseek-chat")])