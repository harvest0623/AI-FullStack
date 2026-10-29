"""
02_trajectory_debug.py
轨迹调试：对一次失败运行做自动"体检"，标红可疑步骤，
并演示二分定位『第一个可疑观察』的排查思路。

运行：python 02_trajectory_debug.py
"""

from dataclasses import dataclass


@dataclass
class TStep:
    thought: str
    action: str
    observation: str


# 一次"结果错误"的运行轨迹（最终答案引用了没查过的数字）
TRAJECTORY = [
    TStep("需要先查本月销量。",
          "query_sales(week='2024-W03')",
          '{"week": "2024-W03", "sales": 1450}'),
    TStep("再查上月销量做对比。",
          "query_sales(week='2024-W02')",
          '{"error": "timeout", "detail": "db busy"}'),          # 可疑1：查询失败
    TStep("上月是 1200。",                                            # 可疑2：编造数字
          "calc(expr='(1450-1200)/1200*100')",
          '{"result": 20.83}'),
    TStep("环比增长 20.83%，行业均值 1250 也高于它。",                # 可疑3：又一个编造数字
          "FINAL",
          "本月销量 1450，环比 +20.83%，高于行业均值 1250。"),
]

RULES = [
    ("忽视错误", lambda s: '"error"' in s.observation and "失败" not in s.thought
                          and "错误" not in s.thought),
    ("无据数字", lambda s: any(w.isdigit() and w not in s.observation and w not in s.action
                              for w in s.thought.replace("2024", "").split())),
    ("最终含未验证事实", lambda s: s.action == "FINAL" and s.observation.count("1250") > 0
                                   and not any("1250" in t.observation for t in TRAJECTORY if t.action != "FINAL")),
]


def diagnose(steps: list[TStep]):
    print("=" * 62)
    print("轨迹体检：逐步扫描并标记可疑信号")
    print("=" * 62)
    first_suspect = None
    for i, s in enumerate(steps, 1):
        flags = [name for name, rule in RULES if rule(s)]
        mark = "  ⚠ " + ",".join(flags) if flags else "  ✅"
        print(f"\nStep {i} {mark}")
        print(f"  Thought    : {s.thought}")
        print(f"  Action     : {s.action}")
        print(f"  Observation: {s.observation[:60]}")
        if flags and first_suspect is None:
            first_suspect = i
    return first_suspect


def main():
    first = diagnose(TRAJECTORY)

    print("\n" + "=" * 62)
    print("二分定位结论")
    print("=" * 62)
    print(f"第一个可疑步骤：Step {first}（query W02 返回 timeout）")
    print("  根因链：W02 查询超时 -> 模型无视错误编造 1200 -> 计算基于假数据")
    print("        -> 最终答案再编 1250（行业均值从未查询）")
    print("\n修复建议：")
    print("  1. 工具错误应显式回填并在 Thought 层提示『该数据不可用』")
    print("  2. Prompt 增加约束：只能引用 Observation 中出现过的数字")
    print("  3. 单步重放验证：只重跑 query_sales(W02)，确认是环境问题还是偶发")

    print("\n要点：")
    print("  1. 调试=看轨迹全貌 -> 自动规则体检 -> 二分定位第一步可疑")
    print("  2. 三类高频可疑信号：忽视错误 / 无据数字 / 引用未验证事实")
    print("  3. 修复后把该案例加入评估集，防止回归（见 04_ab_compare.py）")


if __name__ == "__main__":
    main()