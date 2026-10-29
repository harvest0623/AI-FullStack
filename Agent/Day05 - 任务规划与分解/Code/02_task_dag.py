"""
02_task_dag.py
DAG 依赖图：节点 + 依赖集合，拓扑排序执行，无依赖节点可并行。
演示『查本月/查上月/查行业』并行 -> 算环比/算差距 -> 汇总。

运行：python 02_task_dag.py
"""

import json
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# DAG 定义
# ---------------------------------------------------------------------------
@dataclass
class TaskNode:
    name: str
    deps: list[str]                     # 依赖的节点名
    func: callable = None               # 无 func 表示汇总类节点
    result: object = None
    status: str = "pending"             # pending/ready/done


class TaskDAG:
    def __init__(self):
        self.nodes: dict[str, TaskNode] = {}

    def add(self, name: str, deps: list[str], func: callable = None):
        for d in deps:
            if d not in self.nodes:
                raise ValueError(f"依赖 {d} 尚未定义（请先添加）")
        self.nodes[name] = TaskNode(name, deps, func)

    def ready_nodes(self) -> list[str]:
        """依赖全部完成的待执行节点。"""
        out = []
        for n in self.nodes.values():
            if n.status == "pending" and all(
                    self.nodes[d].status == "done" for d in n.deps):
                out.append(n.name)
        return out

    def run(self, parallel=True):
        """按波次（拓扑层）执行；parallel=True 时同波次视为可并行。"""
        wave = 0
        while True:
            ready = self.ready_nodes()
            if not ready:
                break
            wave += 1
            mode = "并行执行" if (parallel and len(ready) > 1) else "顺序执行"
            print(f"  Wave {wave}（{mode}）: {ready}")

            for name in ready:                      # 真实并行可用线程池
                node = self.nodes[name]
                args = {d: self.nodes[d].result for d in node.deps}
                node.result = node.func(args) if node.func else args
                node.status = "done"
        return {n.name: n.result for n in self.nodes.values()}


# ---------------------------------------------------------------------------
# 示例：销量分析 DAG
# ---------------------------------------------------------------------------
def q_cur(_):    return 1450
def q_prev(_):   return 980
def q_industry(_): return 1100


def calc_mom(d):   return round((d["查本月"] - d["查上月"]) / d["查上月"] * 100, 1)
def calc_gap(d):   return round((d["查本月"] - d["查行业"] / 1) / (d["查行业"] / 1) * 100, 1)


def summarize(d):
    return (f"本月销量 {d['查本月']}，环比上月({d['查上月']}) {d['算环比']}%；"
            f"对比行业均值({d['查行业']}) 高出 {d['算差距']}%。结论：跑赢大盘。")


def build_dag() -> TaskDAG:
    dag = TaskDAG()
    dag.add("查本月", [], q_cur)
    dag.add("查上月", [], q_prev)
    dag.add("查行业", [], q_industry)
    dag.add("算环比", ["查本月", "查上月"], calc_mom)
    dag.add("算差距", ["查本月", "查行业"], calc_gap)
    dag.add("汇总", ["算环比", "算差距"], summarize)
    return dag


def main():
    print("=" * 62)
    print("DAG 依赖图：拓扑分层 + 并行调度")
    print("=" * 62)

    dag = build_dag()
    print("节点与依赖：")
    for n in dag.nodes.values():
        print(f"  {n.name:<8} deps={n.deps}")

    print("\n执行：")
    results = dag.run(parallel=True)

    print(f"\n最终结论：{results['汇总']}")

    # 对比：关闭并行
    print("\n--- 同一 DAG，禁止并行视角（同一波次逐个看） ---")
    dag2 = build_dag()
    dag2.run(parallel=False)

    print("\n要点：")
    print("  1. 依赖显式声明：『查本月/查上月/查行业』无依赖 -> Wave1 可并行")
    print("  2. 拓扑分层天然给出执行顺序，不靠人肉排序")
    print("  3. 真实并行：把 Wave 内节点丢线程池/异步即可（Day06 展开）")
    print("  4. 依赖校验（未定义依赖报错）在 add 时就拦截错误规划")


if __name__ == "__main__":
    main()