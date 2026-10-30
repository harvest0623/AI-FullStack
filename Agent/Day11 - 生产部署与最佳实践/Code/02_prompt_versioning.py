# -*- coding: utf-8 -*-
"""
Day11 - 02 Prompt 版本管理与 A/B 测试

演示内容：
1. Prompt 版本库：版本化存储（版本号/作者/变更说明/内容）
2. 发布流程：draft -> review -> rc（灰度） -> stable（生产）
3. A/B 测试：同一评估集对比两个版本，输出成功率与成本
4. ROI 决策：不只看成功率，要权衡 Token 成本

离线可运行。
"""

import random
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================
# 第一部分：Prompt 版本库
# ============================================================

@dataclass
class PromptVersion:
    version: str            # 语义化版本：1.2.0
    author: str
    content: str
    changelog: str
    status: str = "draft"   # draft / review / rc / stable
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    # 模拟效果数据（生产中由评估集跑出）
    success_rate: float = 0.0
    avg_tokens: int = 0


class PromptRegistry:
    """Prompt 版本库：注册、变更状态、查询生产版本"""

    def __init__(self):
        self.versions: dict[str, PromptVersion] = {}
        self.stable: str | None = None

    def register(self, pv: PromptVersion):
        self.versions[pv.version] = pv
        if pv.status == "stable":
            self.stable = pv.version

    def promote(self, version: str, to: str) -> str:
        """状态流转：draft -> review -> rc -> stable"""
        pv = self.versions[version]
        pv.status = to
        if to == "stable":
            self.stable = version
        return f"{version}: {pv.status}"

    def get_stable(self) -> PromptVersion | None:
        if self.stable:
            return self.versions[self.stable]
        return None

    def history(self) -> list[PromptVersion]:
        return sorted(self.versions.values(), key=lambda v: v.version)


# ============================================================
# 第二部分：A/B 评估（用模拟数据代替真实评估集）
# ============================================================

def run_eval(pv: PromptVersion, n_cases: int = 100) -> dict:
    """
    模拟在评估集上跑 Prompt 版本。
    生产中：对每个测试用例执行 Agent，比对期望输出判分。
    """
    results = {
        "version": pv.version,
        "cases": n_cases,
        "passed": sum(1 for _ in range(n_cases) if random.random() < pv.success_rate),
        "avg_tokens": int(pv.avg_tokens * random.uniform(0.95, 1.05)),
    }
    results["success_rate"] = results["passed"] / n_cases
    return results


def ab_decision(result_a: dict, result_b: dict, token_price: float = 0.00002) -> str:
    """
    ROI 决策：成功率提升的价值 vs 多出的 Token 成本。
    简化模型：每次失败的人工修正成本按 2 元估算。
    """
    sr_a, sr_b = result_a["success_rate"], result_b["success_rate"]
    tk_a, tk_b = result_a["avg_tokens"], result_b["avg_tokens"]

    cost_a = tk_a * token_price + (1 - sr_a) * 2.0   # token 费 + 失败修正费
    cost_b = tk_b * token_price + (1 - sr_b) * 2.0

    lines = [
        f"  A({result_a['version']}): 成功率 {sr_a:.0%}, 平均 {tk_a} tokens, 综合成本/任务 {cost_a:.3f} 元",
        f"  B({result_b['version']}): 成功率 {sr_b:.0%}, 平均 {tk_b} tokens, 综合成本/任务 {cost_b:.3f} 元",
    ]

    if cost_b < cost_a:
        lines.append(f"  决策：选 B（综合成本低 {cost_a - cost_b:.3f} 元/任务，主要是失败率降低）")
        winner = "B"
    elif cost_a < cost_b:
        lines.append(f"  决策：选 A（B 的成功率优势不足以抵消 Token 成本）")
        winner = "A"
    else:
        lines.append("  决策：打平，选成功率高的（长期质量更重要）")
        winner = "B" if sr_b >= sr_a else "A"

    print("\n".join(lines))
    return winner


# ============================================================
# 演示
# ============================================================

def main():
    random.seed(11)

    registry = PromptRegistry()

    print("=" * 56)
    print("1. 注册三个 Prompt 版本（含变更说明）")
    print("=" * 56)
    registry.register(PromptVersion(
        "1.0.0", "alice",
        "你是客服助手，回答用户问题。",
        "初始版本", status="stable", success_rate=0.82, avg_tokens=2800,
    ))
    registry.register(PromptVersion(
        "1.1.0", "bob",
        "你是客服助手。先判断问题类型（物流/退货/咨询），再按对应 SOP 回答。",
        "增加分类前置步骤，减少答非所问", status="rc", success_rate=0.87, avg_tokens=3500,
    ))
    registry.register(PromptVersion(
        "1.2.0", "carol",
        "你是客服助手。判断类型（物流/退货/咨询），按 SOP 回答，末尾附相关FAQ链接。",
        "增加FAQ推荐，提升满意度", status="draft", success_rate=0.85, avg_tokens=3100,
    ))

    for pv in registry.history():
        print(f"  v{pv.version} [{pv.status:<7}] by {pv.author:<5} {pv.changelog}")

    print()
    print("=" * 56)
    print("2. A/B 测试：当前生产版 1.0.0 vs 灰度版 1.1.0")
    print("=" * 56)
    stable = registry.get_stable()
    rc = registry.versions["1.1.0"]

    res_a = run_eval(stable, n_cases=500)
    res_b = run_eval(rc, n_cases=500)
    print(f"  评估集 500 条：A 通过 {res_a['passed']}, B 通过 {res_b['passed']}")

    winner = ab_decision(res_a, res_b)

    print()
    print("=" * 56)
    print("3. 按决策结果流转版本状态")
    print("=" * 56)
    if winner == "B":
        print(f"  {registry.promote('1.1.0', 'stable')}  <- 成为生产版本")
        print(f"  {registry.promote('1.0.0', 'review')}   <- 旧版本降级备查（可随时回滚）")
    else:
        print("  保持 1.0.0 为生产版本，1.1.0 打回修改")

    print(f"\n  当前生产版本：v{registry.stable}")

    print()
    print("=" * 56)
    print("关键结论")
    print("=" * 56)
    print("  1. Prompt 是 Agent 的源代码：版本化 + 变更说明 + 可回滚")
    print("  2. 版本流转有门槛：draft -> review -> rc(灰度) -> stable")
    print("  3. A/B 决策看综合成本：失败修正成本常被低估，Token 费只是显性成本")


if __name__ == "__main__":
    main()
