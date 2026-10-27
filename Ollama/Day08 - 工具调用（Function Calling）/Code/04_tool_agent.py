# -*- coding: utf-8 -*-
"""
Day08 - 04 工具型 Agent（双模式）

把"请求模型 → 看是否要工具 → 执行 → 结果回传"封装成循环，
直到模型不再调用工具，输出最终答案——这是一个最小 Tool Agent。

双模式：有支持 tools 的模型 -> 真实循环；无 -> 规则模拟"模型依次想要多个工具"。
"""

import json
from ollama_util import is_ollama_available, real_chat_with_tools

MODEL = "qwen2.5"

TOOLS = [
    {"type": "function", "function": {
        "name": "get_weather", "description": "查天气",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                       "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "add", "description": "两数相加",
        "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                       "required": ["a", "b"]}}},
]
REGISTRY = {
    "get_weather": lambda **k: f"{k['city']} 晴 24℃",
    "add": lambda **k: k["a"] + k["b"],
}


class ToolAgent:
    """最小工具 Agent：循环直到模型不再要工具"""

    def __init__(self, system: str, tools: list[dict]):
        self.tools = tools
        self.messages = [{"role": "system", "content": system}]

    def _run_real(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        for _ in range(4):  # 最多 4 轮工具循环，防止死循环
            resp = real_chat_with_tools(MODEL, self.messages, self.tools)
            msg = resp.get("message", {})
            calls = msg.get("tool_calls", [])
            if not calls:
                final = msg.get("content", "")
                self.messages.append({"role": "assistant", "content": final})
                return final
            self.messages.append(msg)
            for c in calls:
                fn = c["function"]
                args = json.loads(fn.get("arguments") or "{}")
                out = REGISTRY[fn["name"]](**args)
                print(f"    [tool] {fn['name']}({args}) → {out}")
                self.messages.append({"role": "tool", "content": str(out)})
        return "（达到最大工具轮数，停止）"

    def _run_sim(self, user_text: str) -> str:
        print("  [模拟] 模型判定：先查北京天气，再算加法和={3+4}？")
        plan = [("get_weather", {"city": "北京"}), ("add", {"a": 3, "b": 4})]
        details = []
        for name, args in plan:
            out = REGISTRY[name](**args)
            details.append(str(out))
            print(f"    [tool] {name}({args}) → {out}")
        self.messages.append({"role": "user", "content": user_text})
        answer = ("模拟作答：北京今天晴24℃；3加4等于7。算好咯！")
        return answer

    def run(self, user_text: str) -> str:
        if is_ollama_available(MODEL):
            return self._run_real(user_text)
        return self._run_sim(user_text)


def main():
    print(">> 工具型 Agent\n")
    agent = ToolAgent(
        "你是乐于助人的本地助手，能用工具查天气和做加法。",
        TOOLS,
    )
    reply = agent.run("帮我查下北京天气，顺便算 3 加 4。")
    print(f"\nAgent 最终答复：{reply}")


if __name__ == "__main__":
    main()