"""
04_cost_control.py
成本控制：步数预算 / token 预算 / 工具调用预算 / 金额预算，
以及超限时的『降级』而非『死掉』。含工具结果缓存演示。

运行：python 04_cost_control.py
"""


class Budget:
    """多维度预算器：每步消耗、查询余额、超限判定。"""

    def __init__(self, max_steps=10, max_tokens=20000, max_tool_calls=8, max_cost_usd=0.5):
        self.limits = {"steps": max_steps, "tokens": max_tokens,
                       "tool_calls": max_tool_calls, "cost_usd": max_cost_usd}
        self.used = {"steps": 0, "tokens": 0, "tool_calls": 0, "cost_usd": 0.0}

    def consume(self, steps=0, tokens=0, tool_calls=0, cost_usd=0.0):
        self.used["steps"] += steps
        self.used["tokens"] += tokens
        self.used["tool_calls"] += tool_calls
        self.used["cost_usd"] += cost_usd

    def exceeded(self) -> list[str]:
        """返回超限的预算项。"""
        return [k for k, v in self.limits.items() if self.used[k] > v]

    def report(self) -> str:
        parts = [f"{k} {self.used[k]}/{self.limits[k]}" for k in self.limits]
        return "  ".join(parts)


def degrade_policy(exceeded: list[str], progress: str) -> str:
    """超限降级策略：根据超限项选择出路。"""
    if "cost_usd" in exceeded or "tokens" in exceeded:
        return (f"[降级-终止] 预算超限({exceeded})。基于已有进展输出简化结论：{progress}")
    if "steps" in exceeded:
        return f"[降级-收敛] 步数超限。停止探索，立即总结：{progress}"
    if "tool_calls" in exceeded:
        return f"[降级-去工具] 工具调用超限。禁止再调用工具，用现有信息回答：{progress}"
    return "[正常] 继续执行"


# ---------------------------------------------------------------------------
# 工具结果缓存
# ---------------------------------------------------------------------------
class ToolCache:
    """相同参数的工具调用直接命中缓存，省钱省时（注意时效性风险）。"""

    def __init__(self):
        self._cache = {}
        self.hits = 0
        self.misses = 0

    def call(self, key: str, func, **kwargs):
        if key in self._cache:
            self.hits += 1
            return self._cache[key], True
        self.misses += 1
        result = func(**kwargs)
        self._cache[key] = result
        return result, False


def query_sales(week: str) -> dict:
    return {"week": week, "sales": 1450}


def main():
    print("=" * 62)
    print("成本预算：四道闸与超限降级")
    print("=" * 62)

    budget = Budget(max_steps=3, max_tokens=200, max_tool_calls=2, max_cost_usd=0.01)
    print(f"初始预算：{budget.report()}\n")

    # 模拟一个"花钱不眨眼"的 Agent 循环
    progress = "已查明本月销量 1450"
    for step in range(1, 6):
        budget.consume(steps=1, tokens=80, tool_calls=1, cost_usd=0.004)
        print(f"Step {step}: {budget.report()}")
        exceeded = budget.exceeded()
        if exceeded:
            action = degrade_policy(exceeded, progress)
            print(f"\n{action}")
            break

    print("\n" + "=" * 62)
    print("工具结果缓存：重复查询直接命中")
    print("=" * 62)
    cache = ToolCache()
    for _ in range(3):
        r, hit = cache.call("sales:2024-W03", query_sales, week="2024-W03")
        print(f"  调用 sales:2024-W03 -> {'缓存命中' if hit else '真实执行'} {r}")
    print(f"  统计：命中 {cache.hits} 次 / 未命中 {cache.misses} 次")
    print("  ⚠ 缓存风险：销量这类数据有时效性，TTL 必须设置（过期即失效）")

    print("\n要点：")
    print("  1. 四道闸：步数/token/调用数/金额；任何一个超限都要有出路")
    print("  2. 降级而非死掉：输出已有进展的简化结论，保留任务价值")
    print("  3. 缓存省真金白银，但必须配 TTL，防止拿到过期数据")
    print("  4. 预算检查放在每步循环开头，而不是任务结束时才发现")


if __name__ == "__main__":
    main()