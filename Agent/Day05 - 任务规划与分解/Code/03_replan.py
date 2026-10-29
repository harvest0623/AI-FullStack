"""
03_replan.py
动态重规划（Replan）：执行中发现偏差/失败时，保留已完成成果，重排剩余步骤。
演示：计划中"查询行业均值"失败 -> 触发 Replan -> 换用新数据源。

运行：python 03_replan.py
"""

import json


# ---------------------------------------------------------------------------
# 模拟环境：行业接口首次失败，备用接口可用
# ---------------------------------------------------------------------------
CALL_COUNT = {"industry_api": 0}


def industry_api_v1():
    CALL_COUNT["industry_api"] += 1
    return {"error": "timeout", "retry_after": None}      # 首次调用即失败


def industry_api_backup():
    return {"value": 1100, "source": "backup"}


# ---------------------------------------------------------------------------
# 计划 / 执行 / 重规划
# ---------------------------------------------------------------------------
def make_plan() -> list[dict]:
    return [
        {"id": 1, "step": "查本月销量", "tool": "sales", "args": {}, "status": "done", "result": 1450},
        {"id": 2, "step": "查行业均值", "tool": "industry_api", "args": {}, "status": "pending"},
        {"id": 3, "step": "算领先幅度", "tool": "calc", "args": {}, "status": "pending"},
        {"id": 4, "step": "汇总结论", "tool": None, "args": {}, "status": "pending"},
    ]


def execute_step(task: dict):
    if task["tool"] == "sales":
        return 1450
    if task["tool"] == "industry_api":
        return industry_api_v1()                    # 会失败
    if task["tool"] == "industry_backup":
        return industry_api_backup()
    if task["tool"] == "calc":
        return round((1450 - 1100) / 1100 * 100, 1)
    return None


def replan(plan: list[dict], failed: dict, observation) -> list[dict]:
    """重规划：保留已完成；失败步换方案；后续步骤保持。"""
    new_plan = []
    for task in plan:
        if task["id"] == failed["id"]:
            # 依据观察选择替代方案（真实场景由 LLM 决策）
            if isinstance(observation, dict) and observation.get("error") == "timeout":
                new_plan.append({"id": task["id"], "step": "查行业均值(备用源)",
                                 "tool": "industry_backup", "args": {}, "status": "pending"})
        else:
            new_plan.append(task)
    return new_plan


def run_with_replan(max_replans: int = 2):
    plan = make_plan()
    replans_used = 0

    print("初始计划：")
    for t in plan:
        print(f"  {t['id']}. [{t['status']:<7}] {t['step']}")

    while any(t["status"] != "done" for t in plan):
        task = next(t for t in plan if t["status"] == "pending")
        print(f"\n执行：{task['step']}（tool={task['tool']}）")
        result = execute_step(task)

        if isinstance(result, dict) and "error" in result:
            if replans_used >= max_replans:
                print(f"  失败且重规划次数已用尽({replans_used})，终止任务并上报。")
                return None
            replans_used += 1
            print(f"  ❌ 失败: {result} -> 触发第 {replans_used} 次重规划")
            plan = replan(plan, task, result)
            print("  新计划：")
            for t in plan:
                mark = "✓" if t["status"] == "done" else " "
                print(f"    {mark} {t['id']}. {t['step']}")
        else:
            task["status"], task["result"] = "done", result
            print(f"  ✅ 结果: {result}")

    # 汇总
    gap = next(t for t in plan if t["step"] == "算领先幅度")["result"]
    print(f"\n最终结论：本月销量 1450，领先行业均值 31.8%（用 {replans_used} 次重规划）")
    return gap


def main():
    print("=" * 62)
    print("动态重规划：计划赶不上变化时")
    print("=" * 62)
    run_with_replan()

    print("\n要点：")
    print("  1. Replan 只重排『未来』：已完成步骤（查本月）成果直接保留")
    print("  2. 重规划依据 = 失败观察（error 类型决定换什么方案）")
    print("  3. 重规划次数必须有上限（本例 2 次），否则『反复改道』本身失控")
    print("  4. 耗尽后应『保存进展 + 明确上报』，而非静默失败")


if __name__ == "__main__":
    main()