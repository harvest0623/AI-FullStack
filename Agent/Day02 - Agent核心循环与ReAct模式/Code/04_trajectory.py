"""
04_trajectory.py
轨迹（Trajectory）：记录每步 (Thought/Action/Observation) + 元数据（时间/耗时/token），
导出 JSONL 落盘，并做结构化回放与统计。

运行：python 04_trajectory.py
"""

import json
import time
from dataclasses import dataclass, field, asdict


# ---------------- 轨迹数据结构 ----------------
@dataclass
class Step:
    index: int
    thought: str
    action: str
    args: dict
    observation: str
    ts: float = field(default_factory=time.time)
    latency_ms: float = 0.0
    tokens: int = 0


class Trajectory:
    """Agent 黑匣子：追加步骤、导出 JSONL、回放与统计。"""

    def __init__(self, goal: str):
        self.goal = goal
        self.steps: list[Step] = []

    def add(self, **kw):
        self.steps.append(Step(index=len(self.steps) + 1, **kw))

    def to_jsonl(self) -> str:
        lines = [json.dumps({"goal": self.goal, **asdict(s)}, ensure_ascii=False) for s in self.steps]
        return "\n".join(lines)

    def replay(self):
        """结构化回放：逐步重演运行过程。"""
        print(f"回放目标：{self.goal}")
        for s in self.steps:
            print(f"  #{s.index} [{time.strftime('%H:%M:%S', time.localtime(s.ts))}] "
                  f"{s.latency_ms:5.1f}ms {s.tokens:>4}tok")
            print(f"     Thought: {s.thought}")
            print(f"     Action : {s.action}({json.dumps(s.args, ensure_ascii=False)})")
            print(f"     Observ : {s.observation[:70]}")

    def stats(self):
        return {
            "steps": len(self.steps),
            "total_tokens": sum(s.tokens for s in self.steps),
            "total_latency_ms": round(sum(s.latency_ms for s in self.steps), 1),
            "tool_calls": sum(1 for s in self.steps if s.action != "FINAL"),
        }


# ---------------- 模拟一次带轨迹记录的 Agent 运行 ----------------
def run_with_trajectory() -> Trajectory:
    traj = Trajectory("对比 W01 与 W02 销量")
    script = [
        ("需要两个周的数据，先查 W01。", "query_sales", {"week": "2024-W01"},
         '{"week": "2024-W01", "sales": 1200}'),
        ("拿到 W01=1200，再查 W02。", "query_sales", {"week": "2024-W02"},
         '{"week": "2024-W02", "sales": 980}'),
        ("两期数据齐了，计算环比。", "calc", {"expr": "(980-1200)/1200*100"}, '{"result": -18.33}'),
        ("下跌 18.3%，可以总结。", "FINAL", {}, "W02 销量环比下跌 18.3%。"),
    ]
    for thought, action, args, obs in script:
        t0 = time.perf_counter()
        time.sleep(0.02)                      # 模拟执行耗时
        latency = (time.perf_counter() - t0) * 1000
        traj.add(thought=thought, action=action, args=args, observation=obs,
                 latency_ms=round(latency, 1), tokens=180 + len(thought))
    return traj


def main():
    traj = run_with_trajectory()

    print("=" * 62)
    print("1) 结构化回放")
    print("=" * 62)
    traj.replay()

    print("\n" + "=" * 62)
    print("2) 运行统计")
    print("=" * 62)
    for k, v in traj.stats().items():
        print(f"  {k:<18} {v}")

    print("\n" + "=" * 62)
    print("3) JSONL 导出（生产落盘格式，每行一步）")
    print("=" * 62)
    print(traj.to_jsonl()[:400] + "\n  ...（截断显示）")

    # 写到本地文件演示落盘
    out = "trajectory_demo.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        f.write(traj.to_jsonl())
    print(f"已写入 {out}")

    print("\n要点：")
    print("  1. 轨迹=黑匣子：调试/评估/审计/回放都靠它")
    print("  2. 每步带 ts/latency/tokens 元数据，为成本核算与性能分析留好数据")
    print("  3. JSONL 每行一步，方便流式写入与逐行分析（Day10 可观测会复用）")


if __name__ == "__main__":
    main()