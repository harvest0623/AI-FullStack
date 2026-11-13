"""
Day04 练习二：终止与最大轮次
===============================
演示一个"赖皮"模型: 只会反复输出 Action 却从不出 Final Answer,
ReAct 循环必须用 max_steps 兜底, 避免无限调用/烧钱。

运行:
  python "Day04 - 手写推理循环 Thoughts/Code/02-max-steps.py"
"""
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm import text  # noqa: F401  # noqa: E402


def parse(reply: str) -> dict:
    out = {"final": None, "action": None}
    for line in reply.splitlines():
        line = line.strip()
        if line.startswith("Final Answer:"):
            out["final"] = line[len("Final Answer:"):].strip()
        elif line.startswith("Action:"):
            out["action"] = line[len("Action:"):].strip().split()[0] if line[len("Action:"):].strip() else None
    return out


def stuck_decider(messages, tools=None):
    """永不终止的模型: 每次都说要再查一次。"""
    return {"content": "Thought: 我再查一下。\nAction: get_more\nAction Input: {\"n\": 1}", "tool_calls": []}


def main() -> None:
    print("ReAct with max_steps 演示 (一个永不 'Final Answer' 的模型)\n")
    history = [
        {"role": "system", "content": "严格按 Thought/Action/Final Answer 输出。"},
        {"role": "user", "content": "一直查数据直到确定答案"},
    ]

    max_steps = 6
    for step in range(max_steps):
        reply = stuck_decider(history)["content"]
        print(f"[{step+1}/{max_steps}] {reply}")
        # 假设每次都执行成功得到观察
        history.append({"role": "assistant", "content": reply})
        history.append({"role": "tool", "content": "Observation: 结果 1"})
        p = parse(reply)
        if p["final"]:
            print("✅ 提前终止:", p["final"])
            return

    print(f"\n⚠️ 已达最大轮次 {max_steps}, 强制终止。")
    print("   现实中被 kickout 的兜底: 返回半完成提示, 不做额外调用。")


if __name__ == "__main__":
    main()