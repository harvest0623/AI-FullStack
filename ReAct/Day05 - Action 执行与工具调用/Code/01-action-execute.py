"""
Day05 练习一：文本协议 Action 执行
====================================
完整 ReAct 闭环(文本协议):
  Thought -> Action -> 用注册表执行 -> Observation 回填 -> 再循环 -> Final Answer
任务: 计算 (3*4) 的平方, 需要调用 multiply 与 square 两次。

运行:
  python "Day05 - Action 执行与工具调用/Code/01-action-execute.py"
"""
import json
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402


# ---------- 工具 ----------
@tool
def multiply(a: float, b: float) -> str:
    """两数相乘"""
    return str(a * b)


@tool
def square(x: float) -> str:
    """求平方"""
    return str(x ** 2)


def parse(reply: str) -> dict:
    out = {"action": None, "args": {}, "final": None}
    for line in reply.splitlines():
        line = line.strip()
        if line.startswith("Final Answer:"):
            out["final"] = line[len("Final Answer:"):].strip()
        elif line.startswith("Action:"):
            name = line[len("Action:"):].strip()
            out["action"] = name.split()[0] if name else None
        elif line.startswith("Action Input:"):
            try:
                out["args"] = json.loads(line[len("Action Input:"):].strip())
            except json.JSONDecodeError:
                out["args"] = {}
    return out


def react_decider(messages, tools=None):
    """依据历史里的工具结果, 决定下一步: 先乘, 再平方, 最后作答。"""
    obs = [m["content"] for m in messages if m.get("role") == "tool"]
    if not obs:
        return {"content": "Thought: 我需要先计算 3*4。\nAction: multiply\nAction Input: {\"a\": 3, \"b\": 4}", "tool_calls": []}
    if obs[-1] in ("12", "12.0"):
        return {"content": "Thought: 已得到中间结果, 再求平方。\nAction: square\nAction Input: {\"x\": 12}", "tool_calls": []}
    if obs[-1] in ("144", "144.0"):
        return {"content": "Thought: 得到 144, 作答。\nFinal Answer: (3*4)^2 = 144", "tool_calls": []}
    return {"content": "Thought: 情况不明。\nAction: square\nAction Input: {\"x\": 12}", "tool_calls": []}


def main() -> None:
    reg = ToolRegistry([multiply, square])   # 已是 @tool 装饰的 Tool 对象
    history = [
        {"role": "system", "content": "你是 ReAct。按 Thought/Action/Action Input 输出; 求完给 Final Answer。"},
        {"role": "user", "content": "计算 (3*4) 的平方，并告诉我结果。"},
    ]

    print("ReAct 文本协议: 多步骤执行\n")
    for step in range(6):
        reply = react_decider(history)["content"]
        print(f"── 第 {step+1} 轮 ──\n{reply}\n")
        parsed = parse(reply)
        history.append({"role": "assistant", "content": reply})

        if parsed["final"]:
            print("✅ 最终答案:", parsed["final"])
            return
        if parsed["action"]:
            t = reg.get(parsed["action"])
            if t is None:
                obs = f"错误: 工具 {parsed['action']} 不存在"
            else:
                obs = t.run(**parsed["args"])
            print(f"   (Observation: {obs})\n")
            history.append({"role": "tool", "content": obs})

    print("⚠️ 达到最大轮次未完成")


if __name__ == "__main__":
    main()