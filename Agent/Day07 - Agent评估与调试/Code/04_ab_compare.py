"""
04_ab_compare.py
A/B 对比实验框架：同一评估集跑两个版本（如改了 Prompt/工具描述），
对比结果/过程/成本指标，并检查『失败模式迁移』。

运行：python 04_ab_compare.py
"""

import random
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 评估集（固定，回归测试用）
# ---------------------------------------------------------------------------
@dataclass
class EvalCase:
    task_id: str
    question: str
    expected: str          # 期望结果的关键内容


DATASET = [
    EvalCase("q1", "W03 销量多少？", "1450"),
    EvalCase("q2", "W03 相比 W02 涨跌多少？", "48.0"),
    EvalCase("q3", "W02 相比 W01 涨跌多少？", "-18.3"),
    EvalCase("q4", "上周订单量是多少？", "290"),
    EvalCase("q5", "行业均值对比 W03 如何？", "31.8"),
]


# ---------------------------------------------------------------------------
# 两个版本（模拟：B 版修复了工具描述，选择更准）
# ---------------------------------------------------------------------------
def run_version_a(case: EvalCase) -> dict:
    rng = random.Random(hash(case.task_id) % 1000)
    steps = rng.choice([4, 5, 6, 8])
    success = rng.random() > 0.4          # 60% 成功率
    if not success:
        mode = "死循环" if steps >= 8 else "参数幻觉"
    else:
        mode = "-"
    return {"steps": steps, "success": success,
            "tokens": 900 + steps * 180, "mode": mode}


def run_version_b(case: EvalCase) -> dict:
    rng = random.Random(hash(case.task_id) % 1000)
    steps = rng.choice([3, 4, 4, 5])       # 更少步数
    success = rng.random() > 0.2           # 80% 成功率
    if not success:
        mode = "过早放弃"
    else:
        mode = "-"
    return {"steps": steps, "success": success,
            "tokens": 700 + steps * 150, "mode": mode}


def aggregate(results: list[dict]) -> dict:
    n = len(results)
    return {
        "成功率": sum(r["success"] for r in results) / n,
        "平均步数": sum(r["steps"] for r in results) / n,
        "平均token": int(sum(r["tokens"] for r in results) / n),
        "失败模式": {r["mode"] for r in results if not r["success"]},
    }


def compare(name_a, agg_a, name_b, agg_b):
    print(f"\n{'指标':<10} {name_a:<16} {name_b:<16} 变化")
    print("-" * 56)
    rows = [("成功率", "成功率", lambda a: f"{a:.0%}"),
            ("平均步数", "平均步数", lambda a: f"{a:.1f}"),
            ("平均token", "平均token", lambda a: str(a))]
    for label, key, fmt in rows:
        va, vb = agg_a[key], agg_b[key]
        arrow = "↑" if vb > va else ("↓" if vb < va else "=")
        print(f"{label:<10} {fmt(va):<16} {fmt(vb):<16} {arrow}")
    print(f"{'失败模式':<10} {str(agg_a['失败模式']):<16} {str(agg_b['失败模式']):<16}")


def main():
    print("=" * 60)
    print(f"A/B 对比实验（评估集 {len(DATASET)} 例，固定种子可复现）")
    print("=" * 60)

    # 版本 A
    results_a = [run_version_a(c) for c in DATASET]
    # 版本 B
    results_b = [run_version_b(c) for c in DATASET]

    agg_a, agg_b = aggregate(results_a), aggregate(results_b)
    compare("A(旧Prompt)", agg_a, "B(新Prompt)", agg_b)

    print("\n[失败模式迁移检查]")
    print(f"  A 的失败模式: {agg_a['失败模式']}")
    print(f"  B 的失败模式: {agg_b['失败模式']}")
    print("  -> 即使成功率提升，也要确认没有引入新失败模式；")
    print("     若 B 出现 A 没有的模式（如观察误读），需针对性补护栏。")

    print("\n[单例回看]")
    for c, ra, rb in zip(DATASET, results_a, results_b):
        sa = "✅" if ra["success"] else "❌"
        sb = "✅" if rb["success"] else "❌"
        print(f"  {c.task_id}: A {sa}({ra['steps']}步)  B {sb}({rb['steps']}步)  期望含: {c.expected}")

    print("\n要点：")
    print("  1. 评估集固定 + 种子固定 -> 可复现的对比")
    print("  2. 看三样：结果指标、过程指标、失败模式分布")
    print("  3. 每次改动跑一遍评估集 = Agent 的回归测试")


if __name__ == "__main__":
    main()