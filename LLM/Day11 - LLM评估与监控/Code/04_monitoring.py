# 文件用途：生产监控数据采集
# LLMMonitor 类：采集延迟(P50/P95/P99) / 成本(Token消耗/费用) / 质量(用户反馈/抽检)
# 安全(有害内容检测) / 可用性(错误率)
# 支持告警规则配置（阈值/异常检测），生成监控报告数据
# 含 Prometheus 格式指标输出示例
# Python 3.10+ 可运行（纯标准库）

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class RequestRecord:
    """单次请求记录。"""

    timestamp: float
    latency: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    model: str = ""
    status: str = "success"  # success / error / timeout
    user_id: str = ""
    endpoint: str = "/chat"
    has_harmful: bool = False
    feedback: str = ""  # positive / negative / ""


@dataclass
class AlertRule:
    """告警规则。"""

    name: str
    metric: str          # 指标名
    threshold: float     # 阈值
    comparison: str = ">"  # > / < / >= / <= / ==
    window_seconds: int = 300  # 时间窗口
    severity: str = "warning"  # warning / critical
    message: str = ""
    enabled: bool = True


@dataclass
class Alert:
    """告警事件。"""

    rule_name: str
    severity: str
    metric_value: float
    threshold: float
    message: str
    timestamp: str


class LLMMonitor:
    """LLM 生产监控数据采集器。"""

    def __init__(self, max_records: int = 10000) -> None:
        self.records: deque[RequestRecord] = deque(maxlen=max_records)
        self.alert_rules: list[AlertRule] = []
        self.alerts: list[Alert] = []
        self._cost_by_model: dict[str, float] = {}
        self._cost_by_user: dict[str, float] = {}
        self._cost_by_endpoint: dict[str, float] = {}

    # ---------- 数据采集 ----------
    def record(self, rec: RequestRecord) -> None:
        """记录一次请求。"""
        self.records.append(rec)
        # 成本分类统计
        if rec.status == "success":
            self._cost_by_model[rec.model] = (
                self._cost_by_model.get(rec.model, 0) + rec.cost
            )
            self._cost_by_user[rec.user_id] = (
                self._cost_by_user.get(rec.user_id, 0) + rec.cost
            )
            self._cost_by_endpoint[rec.endpoint] = (
                self._cost_by_endpoint.get(rec.endpoint, 0) + rec.cost
            )
        # 触发告警检查
        self._check_alerts()

    def record_simple(
        self,
        latency: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        model: str = "",
        status: str = "success",
        user_id: str = "",
        endpoint: str = "/chat",
        has_harmful: bool = False,
        feedback: str = "",
    ) -> None:
        """便捷记录方法。"""
        self.record(
            RequestRecord(
                timestamp=time.time(),
                latency=latency,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model=model,
                status=status,
                user_id=user_id,
                endpoint=endpoint,
                has_harmful=has_harmful,
                feedback=feedback,
            )
        )

    # ---------- 指标计算 ----------
    def _recent_records(self, window_seconds: int) -> list[RequestRecord]:
        """获取时间窗口内的记录。"""
        cutoff = time.time() - window_seconds
        return [r for r in self.records if r.timestamp >= cutoff]

    @staticmethod
    def _percentile(data: list[float], p: float) -> float:
        """计算百分位数。"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = max(0, min(len(sorted_data) - 1, int(len(sorted_data) * p) - 1))
        return round(sorted_data[idx], 3)

    def latency_metrics(self, window: int = 3600) -> dict[str, float]:
        """延迟指标。"""
        records = self._recent_records(window)
        latencies = [r.latency for r in records if r.status == "success"]
        return {
            "count": len(latencies),
            "avg": round(sum(latencies) / len(latencies), 3) if latencies else 0,
            "p50": self._percentile(latencies, 0.5),
            "p95": self._percentile(latencies, 0.95),
            "p99": self._percentile(latencies, 0.99),
            "max": max(latencies) if latencies else 0,
        }

    def cost_metrics(self, window: int = 86400) -> dict[str, Any]:
        """成本指标。"""
        records = self._recent_records(window)
        total_cost = sum(r.cost for r in records)
        total_tokens = sum(r.input_tokens + r.output_tokens for r in records)
        return {
            "total_cost": round(total_cost, 6),
            "total_tokens": total_tokens,
            "input_tokens": sum(r.input_tokens for r in records),
            "output_tokens": sum(r.output_tokens for r in records),
            "by_model": dict(sorted(self._cost_by_model.items())),
            "by_user": dict(sorted(self._cost_by_user.items())),
            "by_endpoint": dict(sorted(self._cost_by_endpoint.items())),
        }

    def quality_metrics(self, window: int = 86400) -> dict[str, Any]:
        """质量指标。"""
        records = self._recent_records(window)
        positive = sum(1 for r in records if r.feedback == "positive")
        negative = sum(1 for r in records if r.feedback == "negative")
        total_feedback = positive + negative
        satisfaction = positive / total_feedback if total_feedback > 0 else 0
        return {
            "total_requests": len(records),
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": round(satisfaction, 4),
        }

    def safety_metrics(self, window: int = 3600) -> dict[str, Any]:
        """安全指标。"""
        records = self._recent_records(window)
        harmful = sum(1 for r in records if r.has_harmful)
        return {
            "total": len(records),
            "harmful_count": harmful,
            "harmful_rate": round(harmful / len(records), 4) if records else 0,
        }

    def availability_metrics(self, window: int = 3600) -> dict[str, Any]:
        """可用性指标。"""
        records = self._recent_records(window)
        errors = sum(1 for r in records if r.status != "success")
        total = len(records)
        return {
            "total": total,
            "success": total - errors,
            "errors": errors,
            "error_rate": round(errors / total, 4) if total else 0,
            "availability": round(1 - errors / total, 4) if total else 1,
        }

    # ---------- 告警 ----------
    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加告警规则。"""
        self.alert_rules.append(rule)

    def add_default_rules(self) -> None:
        """添加默认告警规则。"""
        defaults = [
            AlertRule(
                name="高延迟",
                metric="latency_p95",
                threshold=5.0,
                comparison=">",
                severity="warning",
                message="P95 延迟超过 5 秒",
            ),
            AlertRule(
                name="成本超限",
                metric="daily_cost",
                threshold=100.0,
                comparison=">",
                severity="critical",
                message="日成本超过预算",
            ),
            AlertRule(
                name="错误率过高",
                metric="error_rate",
                threshold=0.1,
                comparison=">",
                severity="critical",
                message="错误率超过 10%",
            ),
            AlertRule(
                name="有害内容",
                metric="harmful_rate",
                threshold=0.01,
                comparison=">",
                severity="critical",
                message="检测到有害内容",
            ),
            AlertRule(
                name="满意度下降",
                metric="satisfaction_rate",
                threshold=0.8,
                comparison="<",
                severity="warning",
                message="用户满意度低于 80%",
            ),
        ]
        self.alert_rules.extend(defaults)

    def _check_alerts(self) -> None:
        """检查告警规则。"""
        metric_values = {
            "latency_p95": self.latency_metrics()["p95"],
            "daily_cost": self.cost_metrics()["total_cost"],
            "error_rate": self.availability_metrics()["error_rate"],
            "harmful_rate": self.safety_metrics()["harmful_rate"],
            "satisfaction_rate": self.quality_metrics()["satisfaction_rate"],
        }

        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            value = metric_values.get(rule.metric, 0)
            triggered = self._compare(value, rule.threshold, rule.comparison)
            if triggered:
                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    metric_value=value,
                    threshold=rule.threshold,
                    message=rule.message,
                    timestamp=datetime.now().isoformat(),
                )
                self.alerts.append(alert)
                print(f"[ALERT][{rule.severity.upper()}] {rule.name}: {rule.message}")

    @staticmethod
    def _compare(value: float, threshold: float, op: str) -> bool:
        ops = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
        }
        return ops.get(op, lambda a, b: False)(value, threshold)

    # ---------- 报告 ----------
    def generate_report(self) -> dict[str, Any]:
        """生成监控报告数据。"""
        return {
            "timestamp": datetime.now().isoformat(),
            "latency": self.latency_metrics(),
            "cost": self.cost_metrics(),
            "quality": self.quality_metrics(),
            "safety": self.safety_metrics(),
            "availability": self.availability_metrics(),
            "recent_alerts": [
                {
                    "rule_name": a.rule_name,
                    "severity": a.severity,
                    "metric_value": a.metric_value,
                    "threshold": a.threshold,
                    "message": a.message,
                    "timestamp": a.timestamp,
                }
                for a in self.alerts[-10:]  # 最近10条告警
            ],
        }

    def to_prometheus(self) -> str:
        """输出 Prometheus 格式指标。"""
        latency = self.latency_metrics()
        cost = self.cost_metrics()
        avail = self.availability_metrics()
        safety = self.safety_metrics()
        quality = self.quality_metrics()

        lines = [
            "# HELP llm_latency_p95 P95 latency in seconds",
            "# TYPE llm_latency_p95 gauge",
            f'llm_latency_p95 {latency["p95"]}',
            "",
            "# HELP llm_latency_p99 P99 latency in seconds",
            "# TYPE llm_latency_p99 gauge",
            f'llm_latency_p99 {latency["p99"]}',
            "",
            "# HELP llm_total_tokens Total tokens consumed",
            "# TYPE llm_total_tokens counter",
            f'llm_total_tokens {cost["total_tokens"]}',
            "",
            "# HELP llm_total_cost Total cost in USD",
            "# TYPE llm_total_cost counter",
            f'llm_total_cost {cost["total_cost"]}',
            "",
            "# HELP llm_error_rate Error rate",
            "# TYPE llm_error_rate gauge",
            f'llm_error_rate {avail["error_rate"]}',
            "",
            "# HELP llm_harmful_rate Harmful content rate",
            "# TYPE llm_harmful_rate gauge",
            f'llm_harmful_rate {safety["harmful_rate"]}',
            "",
            "# HELP llm_satisfaction_rate User satisfaction rate",
            "# TYPE llm_satisfaction_rate gauge",
            f'llm_satisfaction_rate {quality["satisfaction_rate"]}',
        ]

        # 按模型分维度的成本
        for model, c in cost.get("by_model", {}).items():
            safe_model = model.replace("-", "_").replace("/", "_")
            lines.append(f'llm_cost_by_model{{model="{safe_model}"}} {c}')

        return "\n".join(lines)


def demo_monitoring() -> None:
    """演示监控数据采集。"""
    import json
    import random

    monitor = LLMMonitor()
    monitor.add_default_rules()

    models = ["gpt-4o-mini", "qwen2.5:7b"]
    endpoints = ["/chat", "/stream", "/embed"]

    print("=== 模拟采集 100 条请求数据 ===")
    for i in range(100):
        latency = random.uniform(0.3, 6.0)
        in_tok = random.randint(50, 500)
        out_tok = random.randint(50, 300)
        cost = (in_tok * 0.00015 + out_tok * 0.0006) / 1000
        model = random.choice(models)
        endpoint = random.choice(endpoints)
        status = "error" if random.random() < 0.05 else "success"
        harmful = random.random() < 0.02
        feedback = random.choice(["positive", "negative", "", "", ""])

        monitor.record_simple(
            latency=latency,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost=cost,
            model=model,
            status=status,
            user_id=f"user_{random.randint(1, 20)}",
            endpoint=endpoint,
            has_harmful=harmful,
            feedback=feedback,
        )

    # 生成报告
    report = monitor.generate_report()
    print("\n=== 监控报告 ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # Prometheus 格式
    print("\n=== Prometheus 指标 ===")
    print(monitor.to_prometheus())


if __name__ == "__main__":
    demo_monitoring()
