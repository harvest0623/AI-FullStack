"""
01_core_loop.py
最小 Agent 循环：感知 -> 思考 -> 行动 -> 观察，直到产出最终答案。
约 80 行实现"五脏俱全"的 Agent Executor 骨架（思考环节用规则模拟）。

运行：python 01_core_loop.py
"""

import json


# ---------------- 环境与工具 ----------------
SALES = {"2024-W01": 1200, "2024-W02": 980, "2024-W03": 1450}


def query_sales(week: str) -> str:
    v = SALES.get(week)
    return json.dumps({"week": week, "sales": v}, ensure_ascii=False) if v else \
        json.dumps({"error": "not found", "available": list(SALES)}, ensure_ascii=False)


def calc(expr: str) -> str:
    try:
        return json.dumps({"result": eval(expr, {"__builtins__": {}}, {})}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


TOOLS = {"query_sales": query_sales, "calc": calc}


# ---------------- 思考器（规则模拟 LLM 决策） ----------------
def think(goal: str, history: list) -> dict:
    """根据目标与历史决定下一步。返回 {"action":..., "args":..., "final":...}"""
    acts = [h["action"] for h in history]

    if not acts:
        return {"action": "query_sales", "args": {"week": "2024-W02"}, "final": None}
    if acts == ["query_sales"]:
        return {"action": "query_sales", "args": {"week": "2024-W01"}, "final": None}
    if len(acts) == 2:
        return {"action": "calc", "args": {"expr": "(980 - 1200) / 1200 * 100"}, "final": None}

    # 已有计算结果 -> 直接给最终答案
    last_obs = history[-1]["observation"]
    pct = json.loads(last_obs)["result"]
    return {"action": None, "args": None,
            "final": f"W02 销量 980，环比 W01(1200) 下跌 {abs(pct):.1f}%。"}


# ---------------- 核心循环 ----------------
def run_agent(goal: str, max_steps: int = 6) -> str:
    history = []   # 轨迹：每步 {action, args, observation}

    for step in range(1, max_steps + 1):
        # 1) 思考（感知=目标+历史，已隐含在 think 的输入里）
        decision = think(goal, history)

        # 2) 终止：拿到最终答案
        if decision["final"] is not None:
            print(f"  [Step {step}] 产出最终答案，循环正常退出。")
            return decision["final"]

        # 3) 行动：执行工具
        name, args = decision["action"], decision["args"]
        observation = TOOLS[name](**args)

        # 4) 观察：回填历史（供下一步感知）
        history.append({"action": name, "args": args, "observation": observation})
        print(f"  [Step {step}] Action={name}({args}) -> {observation[:60]}")

    return f"已达最大步数 {max_steps}，未产出最终答案（进展：{len(history)} 步）。"


def main():
    print("=" * 62)
    print("最小 Agent 循环：感知 -> 思考 -> 行动 -> 观察")
    print("=" * 62)
    goal = "上周销量涨了还是跌了？"
    print(f"目标：{goal}\n")

    answer = run_agent(goal)
    print(f"\n最终答案：{answer}")

    print("\n要点：")
    print("  1. 循环四环节齐全：think() 内含感知与思考，工具执行是行动，observation 回填是观察")
    print("  2. 终止有两条路：final answer 正常退出 / max_steps 强制截断")
    print("  3. 本例 think 是规则；Day03 替换为真实 LLM 决策接口，循环本身不变")


if __name__ == "__main__":
    main()