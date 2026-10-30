"""
01_supervisor.py
Supervisor 主从编排：一个主 Agent 负责路由与聚合，
多个专职 Worker（数据/写作/审查）各自带角色提示与工具。

运行：python 01_supervisor.py
"""

import json


# ---------------------------------------------------------------------------
# Worker：各有一技之长（用规则模拟其行为）
# ---------------------------------------------------------------------------
class Worker:
    def __init__(self, name: str, system_prompt: str, skills: list[str]):
        self.name = name
        self.system_prompt = system_prompt      # 角色提示（真实场景发给 LLM）
        self.skills = skills                    # 能处理的关键词

    def can_handle(self, task: str) -> bool:
        return any(s in task for s in self.skills)

    def run(self, task: str) -> str:
        if self.name == "数据分析":
            return json.dumps({"sales": 1450, "mom": "+48%"}, ensure_ascii=False)
        if self.name == "文案写作":
            return "本月销量 1450，环比大增 48%，增长势头强劲。"
        if self.name == "质检审查":
            return "审查通过：数据与结论一致，表述合规。"
        return "无法处理"


WORKERS = [
    Worker("数据分析", "你是数据分析师，只做查询与计算，输出 JSON。",
           ["销量", "环比", "订单", "计算", "数据"]),
    Worker("文案写作", "你是商业写手，把数据转为易读的结论文字。",
           ["写", "总结", "报告", "文案", "周报"]),
    Worker("质检审查", "你是审核员，检查数据与结论的一致性与合规性。",
           ["审查", "检查", "合规", "审核"]),
]


# ---------------------------------------------------------------------------
# Supervisor：路由 + 聚合
# ---------------------------------------------------------------------------
class Supervisor:
    """主 Agent：不动手，只派活和收结果。"""

    def __init__(self, workers: list[Worker]):
        self.workers = workers
        self.dispatch_log = []

    def route(self, task: str) -> Worker | None:
        for w in self.workers:
            if w.can_handle(task):
                return w
        return None

    def run(self, goal: str) -> str:
        print(f"[Supervisor] 接到任务：{goal}")

        # 拆解成子任务（模拟 LLM 分解）
        subtasks = self.decompose(goal)
        results = []
        for sub in subtasks:
            worker = self.route(sub)
            if worker is None:
                print(f"[Supervisor] ⚠ 无 Worker 能处理：{sub}")
                continue
            print(f"[Supervisor] 派发 '{sub}' -> {worker.name}")
            result = worker.run(sub)
            print(f"  [{worker.name}] 返回：{result[:50]}")
            self.dispatch_log.append((sub, worker.name))
            results.append(result)

        # 聚合（模拟）
        return f"最终交付：分析({results[0]}) + 结论({results[1]}) + 审查({results[2]})"

    def decompose(self, goal: str) -> list[str]:
        if "报告" in goal or "周报" in goal:
            return ["查询本月销量数据", "撰写结论文案", "审查报告合规性"]
        return ["查询相关数据"]


def main():
    print("=" * 62)
    print("Supervisor 模式：主从编排")
    print("=" * 62)
    sup = Supervisor(WORKERS)
    final = sup.run("生成本月销售分析报告")
    print(f"\n{final}")

    print("\n派发记录：")
    for sub, name in sup.dispatch_log:
        print(f"  {name:<8} <- {sub}")

    print("\n要点：")
    print("  1. Supervisor 只做路由与聚合，不做具体工作")
    print("  2. 每个 Worker 有独立系统提示（角色）与专属技能（工具）")
    print("  3. Worker 之间不直接通信——所有协调经 Supervisor，结构清晰可调试")
    print("  4. 路由质量 = Supervisor 的 Prompt 质量；路由错的代价是整个子任务白做")


if __name__ == "__main__":
    main()