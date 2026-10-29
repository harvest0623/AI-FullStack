"""
01_plan_execute.py
Plan-and-Execute 范式：先规划出任务清单，再逐步执行。
对比"无规划的反应式"在长任务上的短视问题。

运行：python 01_plan_execute.py
"""

import json


# ---------------------------------------------------------------------------
# 环境：模拟工具
# ---------------------------------------------------------------------------
SALES = {"2024-W03": 1450, "2024-W02": 980, "2024-W01": 1200}
COMPETITOR = {"行业均值": 1100}


def query_sales(week: str) -> str:
    v = SALES.get(week, 0)
    return json.dumps({"week": week, "sales": v}, ensure_ascii=False)


def query_competitor() -> str:
    return json.dumps(COMPETITOR, ensure_ascii=False)


def calc(expr: str) -> str:
    return json.dumps({"result": round(eval(expr, {"__builtins__": {}}, {}), 2)}, ensure_ascii=False)


TOOLS = {"query_sales": query_sales, "query_competitor": query_competitor, "calc": calc}


# ---------------------------------------------------------------------------
# Planner：从目标生成步骤清单（模拟 LLM 规划）
# ---------------------------------------------------------------------------
def planner(goal: str) -> list[dict]:
    if "行业" in goal or "竞品" in goal:
        return [
            {"step": "查询本周销量", "tool": "query_sales", "args": {"week": "2024-W03"}},
            {"step": "查询上周销量", "tool": "query_sales", "args": {"week": "2024-W02"}},
            {"step": "查询行业均值", "tool": "query_competitor", "args": {}},
            {"step": "计算环比", "tool": "calc", "args": {"expr": "(1450-980)/980*100"}},
            {"step": "计算与行业差距", "tool": "calc", "args": {"expr": "(1450-1100)/1100*100"}},
            {"step": "汇总结论", "tool": None, "args": {}},
        ]
    return [
        {"step": "查询本周销量", "tool": "query_sales", "args": {"week": "2024-W03"}},
        {"step": "汇总结论", "tool": None, "args": {}},
    ]


# ---------------------------------------------------------------------------
# Executor：按清单执行，收集结果
# ---------------------------------------------------------------------------
def executor(plan: list[dict]) -> dict:
    results = {}
    for i, task in enumerate(plan, 1):
        if task["tool"] is None:
            # 汇总步骤：基于已有结果生成结论（模拟）
            mom = json.loads(results["计算环比"])["result"]
            gap = json.loads(results["计算与行业差距"])["result"]
            answer = (f"本周销量 1450，环比上周(980)增长 {mom}%，"
                      f"高于行业均值(1100) {gap}%。整体表现强劲。")
            print(f"  [{i}/{len(plan)}] {task['step']} -> {answer}")
            results[task["step"]] = answer
            continue
        obs = TOOLS[task["tool"]](**task["args"])
        print(f"  [{i}/{len(plan)}] {task['step']} -> {task['tool']}(...) = {obs}")
        results[task["step"]] = obs
    return results


def main():
    print("=" * 62)
    print("Plan-and-Execute：先画地图，再走路")
    print("=" * 62)
    goal = "分析本周销量，并对比行业水平"
    print(f"目标：{goal}\n")

    print("阶段一：Planner 生成计划")
    plan = planner(goal)
    for i, t in enumerate(plan, 1):
        print(f"  {i}. {t['step']}")

    print("\n阶段二：Executor 逐步执行")
    results = executor(plan)

    print(f"\n执行完毕：{len(plan)} 步，全部结果键：{list(results)}")

    print("\n要点：")
    print("  1. 规划一次全局可见：环比、行业差距两个分支一目了然（反应式容易漏掉其一）")
    print("  2. 执行器每步只需『当前步骤』上下文，长任务不爆 token")
    print("  3. 计划与执行分离：失败时可以只重跑失败步（见 03_replan.py）")


if __name__ == "__main__":
    main()