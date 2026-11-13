"""
Day04 练习一：手写 Thought 循环
=================================
用纯文本 ReAct 协议, 手写最小 while 循环:
  LLM 生成 Thought/Action -> 解析 -> (执行) -> Observation 回填 -> 再循环
内置一个极简工具执行(square), 让循环真正收敛, 无需 API。

运行:
  python "Day04 - 手写推理循环 Thoughts/Code/01-thought-loop.py"
"""
import json
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import text  # noqa: E402  (仅演示输出格式; 循环自己控制)  # noqa: F401


# ---------- 极简工具执行(示意, Day05 会接入注册表) ----------
def run_tool(action: str, args: dict):
    if action == "square":
        return f"square({args['x']}) = {args['x'] ** 2}"
    if action == "add":
        return f"{args['a']} + {args['b']} = {args['a'] + args['b']}"
    return f"(未知工具 {action})"


# ---------- 解析协议 ----------
def parse_output(reply: str) -> dict:
    """从模型文本解析出 thought / action / args / final。"""
    out = {"thought": None, "action": None, "args": {}, "final": None}
    for line in reply.splitlines():
        line = line.strip()
        if line.startswith("Thought:"):
            out["thought"] = line[len("Thought:"):].strip()
        elif line.startswith("Final Answer:"):
            out["final"] = line[len("Final Answer:"):].strip()
        elif line.startswith("Action Input:"):
            try:
                out["args"] = json.loads(line[len("Action Input:"):].strip())
            except json.JSONDecodeError:
                out["args"] = {}
        elif line.startswith("Action:"):
            m = re.search(r"\b(\w+)", line[len("Action:"):])
            out["action"] = m.group(1) if m else None
    return out


# ---------- Mock LLM: 模拟"想-做"交替, 最终收敛 ----------
def react_decider(messages, tools=None):
    """看最后的 Observation, 决定下一步。"""
    hist = "\n".join(m["content"] for m in messages if m.get("content"))
    if "square" not in hist:
        return {"content": "Thought: 我需要计算 12 的平方。\nAction: square\nAction Input: {\"x\": 12}", "tool_calls": []}
    if "square(12) = 144" in hist:
        return {"content": "Thought: 已经得到结果 144, 可以作答。\nFinal Answer: 结果是 144。", "tool_calls": []}
    return {"content": "Action Input: {}", "tool_calls": []}


def main() -> None:
    user = "计算 12 的平方并告诉我"
    system = (
        "你是 ReAct 代理。请严格按以下格式逐行输出:\n"
        "Thought: <推理>\n"
        "Action: <工具名>\n"
        "Action Input: <json>\n"
        "当无需再调用工具时, 输出:\nFinal Answer: <答案>"
    )
    history = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    print("开始 ReAct 手写循环 (max_steps=8)\n")
    for step in range(8):
        reply = react_decider(history)["content"]
        print(f"── 第 {step+1} 轮 ──")
        print(reply, "\n")

        parsed = parse_output(reply)
        history.append({"role": "assistant", "content": reply})

        # 终止: Final Answer
        if parsed["final"]:
            print("✅ 代理给出最终回答:", parsed["final"])
            return

        # 执行 Action 并回填 Observation
        if parsed["action"]:
            obs = run_tool(parsed["action"], parsed["args"])
            print(f"   (工具返回: {obs})")
            history.append({"role": "tool", "content": obs})

    print("⚠️ 达到最大轮次, 强制终止。")


if __name__ == "__main__":
    main()