# -*- coding: utf-8 -*-
"""
Day10 - 04 指标采集与告警（Metrics & Alerting）

演示内容：
1. 三类指标：计数器（请求数/失败数）、直方图（延迟分布）、仪表盘（进行中任务）
2. 模拟一波流量，统计 P50/P99 延迟、成功率、Token 成本
3. 告警规则引擎：错误率 / P99 / 成本三类规则，分级 P0/P1/P2
4. 正常流量 vs 异常流量下的告警对比

离线可运行。
"""

import random
import time
from dataclasses import dataclass, field


# ============================================================
# 第一部分：指标类型
# ============================================================

class Counter:
    """计数器：只增不减（请求数、失败数、Token 数）"""
    def __init__(self, name: str):
        self.name = name
        self.value = 0

    def inc(self, n: int = 1):
        self.value += n


class Histogram:
    """直方图：按桶统计延迟分布"""

    # 延迟桶（毫秒）：0-100, 100-500, 500-1k, 1k-5k, 5k+
    BUCKETS = [0, 100, 500, 1000, 5000, float("inf")]

    def __init__(self, name: str):
        self.name = name
        self.values: list[float] = []

    def observe(self, ms: float):
        self.values.append(ms)

    def percentile(self, p: float) -> float:
        """计算 P50 / P99"""
        if not self.values:
            return 0
        s = sorted(self.values)
        idx = min(int(len(s) * p / 100), len(s) - 1)
        return s[idx]

    def bucket_counts(self) -> list[int]:
        counts = [0] * (len(self.BUCKETS) - 1)
        for v in self.values:
            for i in range(len(self.BUCKETS) - 1):
                if self.BUCKETS[i] <= v < self.BUCKETS[i + 1]:
                    counts[i] += 1
                    break
        return counts


class Gauge:
    """仪表盘：瞬时值（进行中任务数、队列长度）"""
    def __init__(self, name: str):
        self.name = name
        self.value = 0

    def set(self, v: int):
        self.value = v

    def inc(self):
        self.value += 1

    def dec(self):
        self.value -= 1


# ============================================================
# 第二部分：指标注册表
# ============================================================

@dataclass
class Metrics:
    requests: Counter = field(default_factory=lambda: Counter("requests"))
    failures: Counter = field(default_factory=lambda: Counter("failures"))
    tokens: Counter = field(default_factory=lambda: Counter("tokens"))
    latency: Histogram = field(default_factory=lambda: Histogram("latency_ms"))
    in_flight: Gauge = field(default_factory=lambda: Gauge("in_flight"))

    def summary(self) -> dict:
        total = max(self.requests.value, 1)
        return {
            "请求数": self.requests.value,
            "失败数": self.failures.value,
            "成功率": f"{(1 - self.failures.value / total):.0%}",
            "P50 延迟(ms)": f"{self.latency.percentile(50):.0f}",
            "P99 延迟(ms)": f"{self.latency.percentile(99):.0f}",
            "平均 Token": self.tokens.value // total,
        }


# ============================================================
# 第三部分：告警规则引擎
# ============================================================

@dataclass
class AlertRule:
    name: str
    level: str          # P0 / P1 / P2
    check: callable     # (metrics) -> bool
    message: str


ALERT_RULES = [
    AlertRule(
        "错误率过高", "P0",
        lambda m: m.failures.value / max(m.requests.value, 1) > 0.10,
        "5 分钟窗口错误率超过 10%，立即处理",
    ),
    AlertRule(
        "P99 延迟劣化", "P1",
        lambda m: m.latency.percentile(99) > 5000,
        "P99 延迟超过 5s，性能异常",
    ),
    AlertRule(
        "单任务成本异常", "P1",
        lambda m: m.tokens.value / max(m.requests.value, 1) > 5000,
        "平均 Token 消耗超过预算基线",
    ),
    AlertRule(
        "任务堆积", "P2",
        lambda m: m.in_flight.value > 100,
        "进行中任务数超 100，考虑扩容",
    ),
]


def evaluate_alerts(m: Metrics) -> list[tuple[str, str, str]]:
    """返回触发的告警列表 [(level, name, message), ...]"""
    fired = []
    for rule in ALERT_RULES:
        if rule.check(m):
            fired.append((rule.level, rule.name, rule.message))
    return sorted(fired, key=lambda x: x[0])  # P0 排最前


# ============================================================
# 第四部分：流量模拟
# ============================================================

def simulate_traffic(metrics: Metrics, n: int, error_rate: float = 0.05,
                     slow_rate: float = 0.05, token_avg: int = 2000):
    """模拟 n 个请求"""
    for _ in range(n):
        metrics.requests.inc()
        metrics.in_flight.inc()

        # 模拟延迟：正常 100-800ms，慢请求 3-8s
        if random.random() < slow_rate:
            latency = random.uniform(3000, 8000)
        else:
            latency = random.uniform(100, 800)
        metrics.latency.observe(latency)

        # 模拟失败
        if random.random() < error_rate:
            metrics.failures.inc()

        # 模拟 Token 消耗
        metrics.tokens.inc(int(random.gauss(token_avg, 300)))

        metrics.in_flight.dec()
    return metrics


# ============================================================
# 演示
# ============================================================

def main():
    random.seed(42)

    print("=" * 56)
    print("场景 1：正常流量（错误率 5%，慢请求 5%）")
    print("=" * 56)
    m1 = Metrics()
    simulate_traffic(m1, n=200, error_rate=0.05, slow_rate=0.05, token_avg=2000)
    for k, v in m1.summary().items():
        print(f"  {k}: {v}")

    print("\n触发的告警：")
    alerts = evaluate_alerts(m1)
    if alerts:
        for lv, name, msg in alerts:
            print(f"  [{lv}] {name} - {msg}")
    else:
        print("  无（一切正常）")

    print()
    print("--- 延迟分布（按桶） ---")
    labels = ["0-100ms", "100-500ms", "0.5-1s", "1-5s", "5s+"]
    for label, cnt in zip(labels, m1.latency.bucket_counts()):
        bar = "#" * (cnt // 3)
        print(f"  {label:<10} {cnt:>4} {bar}")

    print()
    print("=" * 56)
    print("场景 2：异常流量（LLM 供应商故障：错误率 25%，全变慢）")
    print("=" * 56)
    m2 = Metrics()
    simulate_traffic(m2, n=200, error_rate=0.25, slow_rate=0.60, token_avg=6500)
    for k, v in m2.summary().items():
        print(f"  {k}: {v}")

    print("\n触发的告警：")
    for lv, name, msg in evaluate_alerts(m2):
        print(f"  [{lv}] {name} - {msg}")

    print()
    print("=" * 56)
    print("告警分级响应建议")
    print("=" * 56)
    print("  P0：电话叫醒值班，5 分钟内响应（服务不可用级别）")
    print("  P1：工作群通知，当天处理（性能/成本异常）")
    print("  P2：记录到工单，下个迭代处理（容量预警）")


if __name__ == "__main__":
    main()
