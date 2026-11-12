"""
Day01 练习一：文字版 ReAct 演示
=================================
用「旅行规划」示例, 把一次 ReAct 轨迹(Thought / Action / Observation)
逐步打印并注释, 让你直观感受「想一步→走一步→看一眼→再想」的循环节拍。

无需 API, 完全离线演示 ReAct 范式本身。
运行:
  python "Day01 - 认识 ReAct 与 Agent 范式/Code/01-narrate-react.py"
"""


def display_trace(trace: list[dict]) -> None:
    """把一条 ReAct 轨迹漂亮地打印出来。"""
    for i, step in enumerate(trace, 1):
        kind = step["kind"]
        payload = step["content"]
        tag = {"thought": "💭 Thought", "action": "🛠  Action", "observation": "👀 Observation",
               "answer": "✅ Answer"}.get(kind, kind.upper())
        print(f"── Step {i} · {tag} ")
        print(f"   {payload}\n")


def main() -> None:
    # 一段完整的 ReAct 轨迹: 用户问「明天去成都适合带伞吗?」
    trace = [
        {"kind": "thought",
         "content": "用户想知道明天成都的天气以决定是否带伞。我应查询未来天气。"},
        {"kind": "action",
         "content": 'search_weather(city="成都", date="2026-09-23")'},
        {"kind": "observation",
         "content": "成都 2026-09-23: 小雨, 18~22℃, 降水概率 80%"},
        {"kind": "thought",
         "content": "明天下雨概率高且有雨, 应建议用户带伞。现在可以作答。"},
        {"kind": "action",
         "content": 'finish_agent(answer="明天成都小雨, 建议带伞并穿防水衣物。")'},
        {"kind": "observation",
         "content": "回答已返回给用户。"},
        {"kind": "answer",
         "content": "明天成都小雨, 建议带伞并穿防水衣物。"},
    ]

    print("=" * 60)
    print("ReAct 轨迹演示: 想一步 → 走一步 → 看一眼 → 再想一步")
    print("=" * 60, "\n")

    print("【初始】用户: 明天去成都适合带伞吗?\n")
    display_trace(trace)

    thoughts = sum(1 for s in trace if s["kind"] == "thought")
    actions = sum(1 for s in trace if s["kind"] == "action")
    print("=" * 60)
    print(f"小结: 共 {thoughts} 次思考, {actions} 次行动, 3 次观察(含回答消耗).")
    print("关键: 每次 Action 之后都有 Observation 反馈, 决定下一步.")
    print("=" * 60)


if __name__ == "__main__":
    main()