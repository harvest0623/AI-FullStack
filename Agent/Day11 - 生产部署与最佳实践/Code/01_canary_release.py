# -*- coding: utf-8 -*-
"""
Day11 - 01 灰度发布（Canary Release）

演示内容：
1. 流量按百分比切分给新旧版本
2. 模拟两个版本的 Agent 表现（成功率/延迟/成本）
3. 灰度决策引擎：指标正常 -> 提升流量；异常 -> 自动回滚
4. 完整的 5% -> 20% -> 50% -> 100% 发布（或中途回滚）流程

离线可运行。
"""

import random
from dataclasses import dataclass, field


# ============================================================
# 第一部分：版本定义
# ============================================================

@dataclass
class Version:
    name: str
    success_rate: float    # 成功率
    p99_ms: float          # P99 延迟
    cost_per_task: float    # 单任务成本（元）

    def serve(self, n: int) -> dict:
        """模拟 n 个请求的表现"""
        return {
            "requests": n,
            "success": sum(1 for _ in range(n) if random.random() < self.success_rate),
            "p99_ms": self.p99_ms * random.uniform(0.95, 1.05),
            "cost": n * self.cost_per_task,
        }


V1 = Version("v1-stable", success_rate=0.95, p99_ms=2000, cost_per_task=0.08)
V2_GOOD = Version("v2-candidate-good", success_rate=0.96, p99_ms=1800, cost_per_task=0.07)
V2_BAD = Version("v2-candidate-bad", success_rate=0.80, p99_ms=9000, cost_per_task=0.20)


# ============================================================
# 第二部分：灰度控制器
# ============================================================

@dataclass
class CanaryPolicy:
    """灰度规则：与基线对比，超阈值即判定异常"""
    max_success_drop: float = 0.02      # 成功率最多下降 2pp
    max_p99_ratio: float = 2.0           # P99 最多是基线的 2 倍
    max_cost_ratio: float = 1.5          # 成本最多是基线的 1.5 倍


class CanaryController:
    """
    灰度控制器：
    - 每阶段把指定比例流量给新版本，其余给旧版本
    - 指标对比通过 -> 推进到下一阶段
    - 指标异常 -> 立即回滚（流量 100% 切回旧版本）
    """

    STAGES = [0.05, 0.20, 0.50, 1.00]  # 5% -> 20% -> 50% -> 100%

    def __init__(self, old: Version, new: Version, policy: CanaryPolicy | None = None):
        self.old = old
        self.new = new
        self.policy = policy or CanaryPolicy()
        self.stage_idx = 0

    def run_stage(self, total_traffic: int = 200) -> str:
        """执行一个灰度阶段，返回 'promote' / 'rollback' / 'done'"""
        if self.stage_idx >= len(self.STAGES):
            return "done"

        ratio = self.STAGES[self.stage_idx]
        n_new = int(total_traffic * ratio)
        n_old = total_traffic - n_new

        print(f"\n--- 阶段 {self.stage_idx + 1}：新版本承接 {ratio:.0%} 流量 ---")

        res_old = self.old.serve(n_old) if n_old else None
        res_new = self.new.serve(n_new)

        if res_old:
            base_sr = res_old["success"] / res_old["requests"]
        else:  # 100% 阶段没有旧版本对照，用版本定义的基线
            base_sr = self.old.success_rate

        new_sr = res_new["success"] / res_new["requests"]
        base_p99 = self.old.p99_ms
        base_cost = self.old.cost_per_task

        print(f"  基线成功率 {base_sr:.0%} vs 新版本 {new_sr:.0%}")
        print(f"  基线 P99 {base_p99:.0f}ms vs 新版本 {res_new['p99_ms']:.0f}ms")
        print(f"  基线单成本 {base_cost:.2f} vs 新版本 {res_new['cost'] / max(res_new['requests'], 1):.2f}")

        # 决策
        drop = base_sr - new_sr
        if drop > self.policy.max_success_drop:
            print(f"  [异常] 成功率下降 {drop:.0%} 超过阈值 {self.policy.max_success_drop:.0%} -> 回滚！")
            return "rollback"
        if res_new["p99_ms"] > base_p99 * self.policy.max_p99_ratio:
            print(f"  [异常] P99 超过基线 {self.policy.max_p99_ratio} 倍 -> 回滚！")
            return "rollback"
        if (res_new["cost"] / max(res_new["requests"], 1)) > base_cost * self.policy.max_cost_ratio:
            print(f"  [异常] 单任务成本超过基线 {self.policy.max_cost_ratio} 倍 -> 回滚！")
            return "rollback"

        print("  [正常] 指标达标，推进下一阶段")
        self.stage_idx += 1
        return "promote" if self.stage_idx < len(self.STAGES) else "done"


def full_release(controller: CanaryController) -> bool:
    """执行完整灰度流程，返回是否发布成功"""
    while True:
        action = controller.run_stage()
        if action == "done":
            print("\n>>> 灰度完成：新版本 100% 上线，发布成功！")
            return True
        if action == "rollback":
            print(">>> 触发自动回滚：流量 100% 切回旧版本，用户几乎无感")
            return False


# ============================================================
# 演示
# ============================================================

def main():
    random.seed(7)

    print("=" * 56)
    print("场景 1：新版本优秀 -> 灰度顺利推进到 100%")
    print("=" * 56)
    c1 = CanaryController(V1, V2_GOOD)
    full_release(c1)

    print()
    print("=" * 56)
    print("场景 2：新版本有问题 -> 第一阶段即回滚")
    print("=" * 56)
    c2 = CanaryController(V1, V2_BAD)
    full_release(c2)

    print()
    print("=" * 56)
    print("关键结论")
    print("=" * 56)
    print("  1. LLM 是概率系统，即使测试全过也要灰度验证真实流量")
    print("  2. 成功率/P99/成本三项指标任一超标立即回滚")
    print("  3. 回滚只是切流量，用户无感——这就是灰度的价值")


if __name__ == "__main__":
    main()
