"""
03_stop_conditions.py
终止条件：演示四种循环出口，重点是"失控 Agent 被缰绳拦下"的过程。

- 正常完成：Final Answer
- 最大步数：max_steps 截断
- 重复检测：连续相同 Action+参数 -> 提示/终止
- 预算耗尽：token/调用数上限

运行：python 03_stop_conditions.py
"""

import json
from dataclasses import dataclass, field


# ---------------- 一个"坏了"的思考器：永远重复同一个决策 ----------------
class BrokenBrain:
    """模拟病态 LLM：陷入循环，反复查同一周数据。"""

    def __init__(self):
        self.calls = 0

    def decide(self, history):
        self.calls += 1
        # 永远返回同一个决策（无论历史如何）
        return {"action": "query_sales", "args": {"week": "2024-W02"}, "final": None}


# ---------------- 正常思考器：两步收敛 ----------------
class NormalBrain:
    def decide(self, history):
        if len(history) == 0:
            return {"action": "query_sales", "args": {"week": "2024-W03"}, "final": None}
        sales = json.loads(history[-1]["observation"])["sales"]
        return {"final": f"W03 销量为 {sales}。任务完成。"}


def query_sales(week: str) -> str:
    return json.dumps({"week": week, "sales": 1450}, ensure_ascii=False)


TOOLS = {"query_sales": query_sales}


@dataclass
class AgentConfig:
    max_steps: int = 5
    repeat_limit: int = 2        # 相同(工具+参数)连续出现 N 次即判死循环
    token_budget: int = 100


def run_agent(brain, goal, cfg: AgentConfig, tag: str):
    history, tokens_used = [], 0
    repeat_count, last_sig = 0, None

    print(f"\n--- 场景：{tag} ---")
    for step in range(1, cfg.max_steps + 1):
        # 终止3：预算
        tokens_used += 20
        if tokens_used > cfg.token_budget:
            print(f"  [终止-预算] 第{step}步 token 超限({tokens_used}>{cfg.token_budget})，强制停止")
            return "BUDGET_EXHAUSTED"

        d = brain.decide(history)

        # 终止1：最终答案
        if d.get("final"):
            print(f"  [Step {step}] Final Answer: {d['final']}")
            return "OK"

        # 终止2：重复检测（工具+参数都相同才算重复）
        sig = (d["action"], json.dumps(d["args"], sort_keys=True))
        if sig == last_sig:
            repeat_count += 1
            if repeat_count >= cfg.repeat_limit:
                print(f"  [终止-重复] 第{step}步 连续重复 {sig}，判定死循环，停止")
                return "REPEAT_LOOP"
        else:
            repeat_count, last_sig = 0, sig

        obs = TOOLS[d["action"]](**d["args"])
        history.append({"action": d["action"], "args": d["args"], "observation": obs})
        print(f"  [Step {step}] {d['action']}({d['args']}) -> {obs[:50]}")

    # 终止2：最大步数
    print(f"  [终止-步数] 达到 max_steps={cfg.max_steps}，强制停止（进展 {len(history)} 步）")
    return "MAX_STEPS"


def main():
    print("=" * 62)
    print("四种终止条件演示")
    print("=" * 62)

    # 1) 正常完成
    r = run_agent(NormalBrain(), "查 W03 销量", AgentConfig(), "正常完成")
    # 2) 死循环被重复检测拦下
    r = run_agent(BrokenBrain(), "查销量（病态大脑）", AgentConfig(max_steps=10), "死循环 -> 重复检测拦截")
    # 3) 最大步数兜底（关闭重复检测）
    r = run_agent(BrokenBrain(), "查销量（无重复检测）",
                  AgentConfig(max_steps=4, repeat_limit=999), "死循环 -> max_steps 兜底")
    # 4) 预算耗尽
    r = run_agent(BrokenBrain(), "查销量（低预算）",
                  AgentConfig(max_steps=10, repeat_limit=999, token_budget=60), "死循环 -> 预算耗尽")

    print("\n要点：")
    print("  1. Agent 是循环，循环必须有出口；max_steps 是永远的最后防线")
    print("  2. 重复检测看『工具+参数』二元组，只看工具名会误伤合理重试")
    print("  3. 预算(token/调用数)是成本视角的硬顶，生产必备(Day06/10)")
    print("  4. 被截断时应返回『已有进展+原因』，而非静默失败")


if __name__ == "__main__":
    main()