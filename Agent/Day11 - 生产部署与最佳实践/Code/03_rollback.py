# -*- coding: utf-8 -*-
"""
Day11 - 03 回滚策略（Rollback）

演示内容：
1. 回滚触发条件：成功率下跌 / P99 超时 / 成本突增
2. 回滚的三层资源处理：
   - 代码/Prompt 切回旧版本（流量切换）
   - 数据兼容：新版本写入的数据旧版本能否读
   - 存量任务：进行中的任务让其跑完，不强行中断
3. 回滚演练：验证切换耗时 < 1 分钟

离线可运行。
"""

import random
import time
from dataclasses import dataclass, field


# ============================================================
# 第一部分：运行时指标与回滚触发器
# ============================================================

@dataclass
class RuntimeMetrics:
    """生产版本运行时的滑动窗口指标"""
    success_rate: float
    p99_ms: float
    cost_per_task: float


class RollbackTrigger:
    """回滚触发器：指标越线 -> 自动回滚"""

    def __init__(self, baseline: RuntimeMetrics):
        self.baseline = baseline

    def should_rollback(self, current: RuntimeMetrics) -> tuple:
        reasons = []
        if current.success_rate < 0.90 and self.baseline.success_rate >= 0.95:
            reasons.append(f"成功率 {current.success_rate:.0%} 跌破 90%（基线 {self.baseline.success_rate:.0%}）")
        if current.p99_ms > 30000:
            reasons.append(f"P99 延迟 {current.p99_ms / 1000:.0f}s 超过 30s")
        if current.cost_per_task > self.baseline.cost_per_task * 2:
            reasons.append(
                f"单任务成本 {current.cost_per_task:.2f} 元超基线 2 倍（{self.baseline.cost_per_task:.2f} 元）"
            )
        return (len(reasons) > 0, reasons)


# ============================================================
# 第二部分：回滚管理器（三层资源处理）
# ============================================================

@dataclass
class Task:
    task_id: str
    version: str      # 由哪个版本创建
    status: str = "running"   # running / done


@dataclass
class DataRecord:
    record_id: str
    schema: str      # v1 / v2 格式
    payload: dict


class RollbackManager:
    """
    回滚三件事：
    1. 流量切回旧版本
    2. 数据兼容处理（v2 格式 -> v1 格式转换 or 兼容读取）
    3. 存量任务优雅处理（跑完不中断）
    """

    def __init__(self, current_version: str, target_version: str):
        self.current = current_version
        self.target = target_version
        self.inflight_tasks: list[Task] = [
            Task(f"T-{i:03d}", current_version) for i in range(1, 6)
        ]
        self.recent_data: list[DataRecord] = [
            DataRecord(f"R-{i:03d}", "v2", {"score": 0.9, "reason_v2": "新格式字段"})
            for i in range(1, 4)
        ]

    def rollback(self) -> float:
        """执行回滚，返回耗时（秒）"""
        t0 = time.time()

        # --- 第 1 层：流量切换 ---
        print("  [1/3] 流量切换：100% 流量切回旧版本（网关配置，秒级生效）")
        print(f"        {self.current} -> {self.target}")

        # --- 第 2 层：数据兼容 ---
        print("  [2/3] 数据兼容：v2 新写入的记录转换为 v1 可读格式")
        for rec in self.recent_data:
            if rec.schema == "v2" and "reason_v2" in rec.payload:
                # 兼容转换：把 v2 专有字段映射到 v1 通用字段
                rec.payload["reason"] = rec.payload.pop("reason_v2")
                rec.schema = "v1-compatible"
                print(f"        {rec.record_id}: reason_v2 -> reason（字段降级映射）")

        # --- 第 3 层：存量任务 ---
        print("  [3/3] 存量任务：5 个进行中任务标记为\"跑完即停\"，不强行中断")
        for t in self.inflight_tasks:
            t.status = "draining"  # 排空模式：当前的做完，不再接新任务
        print(f"        已标记 {len(self.inflight_tasks)} 个任务进入排空模式")

        time.sleep(0.05)  # 模拟切换开销
        return time.time() - t0


# ============================================================
# 第三部分：回滚演练
# ============================================================

def rollback_drill():
    """
    回滚演练：定期执行，验证切换时效与正确性。
    生产中建议每月一次，演练环境尽量贴近生产。
    """
    print("  开始回滚演练（每月一次）...")
    mgr = RollbackManager(current_version="v2.1.0", target_version="v2.0.3")
    elapsed = mgr.rollback()

    print(f"\n  演练结果：")
    print(f"    切换耗时：{elapsed:.2f}s（要求 < 60s）{'合格' if elapsed < 60 else '不合格'}")
    print(f"    数据兼容：{'合格' if all(r.schema == 'v1-compatible' for r in mgr.recent_data) else '不合格'}")
    print(f"    任务处理：{'合格' if all(t.status == 'draining' for t in mgr.inflight_tasks) else '不合格'}")


# ============================================================
# 演示
# ============================================================

def main():
    random.seed(3)

    baseline = RuntimeMetrics(success_rate=0.95, p99_ms=2500, cost_per_task=0.08)
    trigger = RollbackTrigger(baseline)

    print("=" * 56)
    print("场景 1：指标正常，不触发回滚")
    print("=" * 56)
    normal = RuntimeMetrics(success_rate=0.94, p99_ms=2800, cost_per_task=0.09)
    fired, reasons = trigger.should_rollback(normal)
    print(f"  触发回滚：{fired}（{'; '.join(reasons) if reasons else '指标在基线附近，正常'}）")

    print()
    print("=" * 56)
    print("场景 2：新版本翻车（成功率暴跌+成本翻倍），触发自动回滚")
    print("=" * 56)
    bad = RuntimeMetrics(success_rate=0.72, p99_ms=12000, cost_per_task=0.21)
    fired, reasons = trigger.should_rollback(bad)
    print(f"  触发回滚：{fired}")
    for r in reasons:
        print(f"    - {r}")

    print("\n  执行回滚：")
    mgr = RollbackManager(current_version="v2.1.0", target_version="v2.0.3")
    elapsed = mgr.rollback()
    print(f"\n  回滚完成，耗时 {elapsed:.2f}s，用户侧只表现为『刚才那几次回答不好，现在恢复了』")

    print()
    print("=" * 56)
    print("场景 3：回滚演练（定期验证回滚方案有效）")
    print("=" * 56)
    rollback_drill()

    print()
    print("关键结论：")
    print("  1. 回滚触发要自动化：等人工决策的功夫损失已经扩大")
    print("  2. 回滚三层：流量 / 数据 / 存量任务，漏一层就有尾巴")
    print("  3. 不演练的回滚等于没有回滚")


if __name__ == "__main__":
    main()
