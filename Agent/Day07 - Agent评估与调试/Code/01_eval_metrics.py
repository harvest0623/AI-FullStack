"""
01_eval_metrics.py
Agent 评估指标体系：结果 / 过程 / 成本三类指标的计算与汇总报告。
对若干"运行记录"（含轨迹摘要）计算指标并输出评估报告。

运行：python 01_eval_metrics.py
"""

from dataclasses import dataclass, field


@dataclass
class RunRecord:
    """一次任务运行的记录（Agent 跑完后收集）。"""
    task_id: str
    success: bool                    # 结果指标：任务是否达成
    steps: int                       # 过程指标：总步数
    tool_calls: list[str]            # 过程指标：调用序列（含失败标记）
    tokens: int                      # 成本指标
    latency_ms: float
    budget_exceeded: bool = False    # 是否触发超限截断


# 模拟 6 次运行（含失败/超限/重试等真实情况）
RUNS = [
    RunRecord("t1", True,  4, ["query_sales", "query_sales", "calc"],            1200, 850, False),
    RunRecord("t2", True,  6, ["query_sales", "query_sales", "calc",
                               "query_sales(retry)", "calc"],                   1900, 1400, False),
    RunRecord("t3", False, 8, ["query_sales", "query_sales", "query_sales",
                               "query_sales", "query_sales", "query_sales"],    2600, 2100, True),
    RunRecord("t4", True,  5, ["query_kb", "calc", "query_sales", "calc"],      1500, 990, False),
    RunRecord("t5", False, 3, ["query_sales"],                                   700, 300, False),
    RunRecord("t6", True,  4, ["query_sales", "calc"],                          1000, 700, False),
]


def evaluate(runs: list[RunRecord]) -> dict:
    n = len(runs)
    total_calls = sum(len(r.tool_calls) for r in runs)
    retry_calls = sum(1 for r in runs for c in r.tool_calls if "retry" in c)
    return {
        # ---- 结果指标 ----
        "任务成功率": f"{sum(r.success for r in runs)}/{n} = {sum(r.success for r in runs)/n:.0%}",
        "超限截断率": f"{sum(r.budget_exceeded for r in runs)}/{n}",
        # ---- 过程指标 ----
        "平均步数(成功)": round(sum(r.steps for r in runs if r.success) /
                              max(1, sum(r.success for r in runs)), 1),
        "平均步数(失败)": round(sum(r.steps for r in runs if not r.success) /
                              max(1, sum(not r.success for r in runs)), 1),
        "重试率": f"{retry_calls}/{total_calls} = {retry_calls/total_calls:.0%}",
        # ---- 成本指标 ----
        "平均token": int(sum(r.tokens for r in runs) / n),
        "平均延迟ms": int(sum(r.latency_ms for r in runs) / n),
    }


def report(metrics: dict):
    print("=" * 56)
    print("Agent 评估报告")
    print("=" * 56)
    for section, keys in [("结果指标", ["任务成功率", "超限截断率"]),
                          ("过程指标", ["平均步数(成功)", "平均步数(失败)", "重试率"]),
                          ("成本指标", ["平均token", "平均延迟ms"])]:
        print(f"\n[{section}]")
        for k in keys:
            print(f"  {k:<16} {metrics[k]}")


def insight(runs: list[RunRecord], metrics: dict):
    print("\n[解读]")
    # 失败任务更费步数 -> 失败模式可能是死循环
    print(f"  失败任务平均步数({metrics['平均步数(失败)']})明显高于成功任务"
          f"({metrics['平均步数(成功)']})，且 t3 触发超限：疑似死循环/无收敛。")
    print("  t5 三步即失败：疑似过早放弃（只查一次就直答）。")
    print("  => 结果指标之外，过程指标帮你『看出怎么失败的』。")


def main():
    metrics = evaluate(RUNS)
    report(metrics)
    insight(RUNS, metrics)
    print("\n要点：")
    print("  1. 三层指标缺一不可：结果(成没成)/过程(怎么跑的)/成本(花了多少)")
    print("  2. 成功与失败任务的步数差，往往直接指向失败模式")
    print("  3. 生产上把 RunRecord 持久化(Day10)，指标随时间看趋势")


if __name__ == "__main__":
    main()