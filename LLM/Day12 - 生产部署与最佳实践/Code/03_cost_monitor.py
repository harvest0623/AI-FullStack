# 文件用途：成本监控系统
# CostMonitor 类：实时 Token 消耗统计 / 日周月成本报告 / 预算告警
# 成本趋势分析 / 按模型/用户/接口分类统计
# 含 Redis 持久化、告警通知（日志/邮件/Webhook）
# Python 3.10+ 可运行（纯标准库，Redis 可选）

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cost-monitor")

# 可选 Redis
try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore


@dataclass
class UsageRecord:
    """用量记录。"""

    timestamp: float
    model: str
    user_id: str
    endpoint: str
    input_tokens: int
    output_tokens: int
    cost: float


@dataclass
class BudgetConfig:
    """预算配置。"""

    daily_budget: float = 50.0
    weekly_budget: float = 300.0
    monthly_budget: float = 1000.0
    alert_threshold: float = 0.8  # 达到 80% 预算时告警
    critical_threshold: float = 1.2  # 超过 120% 时严重告警


@dataclass
class CostAlert:
    """成本告警。"""

    level: str  # warning / critical
    message: str
    current_cost: float
    budget: float
    timestamp: str


class CostMonitor:
    """LLM 成本监控系统。"""

    def __init__(
        self,
        budget: BudgetConfig | None = None,
        redis_url: str | None = None,
    ) -> None:
        self.budget = budget or BudgetConfig()
        self.records: list[UsageRecord] = []
        self._redis = None
        if redis_url and redis is not None:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("CostMonitor Redis 已连接")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Redis 连接失败，使用内存存储: {exc}")
                self._redis = None

        self.alerts: list[CostAlert] = []
        self._notifiers: list[Callable[[CostAlert], None]] = [self._log_notifier]
        self._daily_alerted: dict[str, bool] = {}  # 避免重复告警

    # ---------- 记录 ----------
    def record(
        self,
        model: str,
        user_id: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        """记录一次用量。"""
        rec = UsageRecord(
            timestamp=time.time(),
            model=model,
            user_id=user_id,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
        self.records.append(rec)
        if self._redis:
            self._redis.lpush("cost_records", json.dumps({
                "timestamp": rec.timestamp,
                "model": model,
                "user_id": user_id,
                "endpoint": endpoint,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
            }))
        # 检查预算告警
        self._check_budget()

    # ---------- 统计 ----------
    def _filter_by_period(self, period: str) -> list[UsageRecord]:
        """按时间周期过滤记录。"""
        now = time.time()
        if period == "daily":
            cutoff = now - 86400
        elif period == "weekly":
            cutoff = now - 86400 * 7
        elif period == "monthly":
            cutoff = now - 86400 * 30
        else:
            cutoff = 0
        return [r for r in self.records if r.timestamp >= cutoff]

    def get_cost_summary(self, period: str = "daily") -> dict[str, Any]:
        """获取成本汇总。"""
        records = self._filter_by_period(period)
        total_cost = sum(r.cost for r in records)
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)

        # 分类统计
        by_model: dict[str, float] = defaultdict(float)
        by_user: dict[str, float] = defaultdict(float)
        by_endpoint: dict[str, float] = defaultdict(float)
        for r in records:
            by_model[r.model] += r.cost
            by_user[r.user_id] += r.cost
            by_endpoint[r.endpoint] += r.cost

        budget_map = {
            "daily": self.budget.daily_budget,
            "weekly": self.budget.weekly_budget,
            "monthly": self.budget.monthly_budget,
        }
        budget = budget_map.get(period, 0)
        usage_rate = total_cost / budget if budget > 0 else 0

        return {
            "period": period,
            "total_cost": round(total_cost, 6),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "budget": budget,
            "usage_rate": round(usage_rate, 4),
            "by_model": dict(sorted(by_model.items(), key=lambda x: -x[1])),
            "by_user": dict(sorted(by_user.items(), key=lambda x: -x[1])[:10]),
            "by_endpoint": dict(sorted(by_endpoint.items(), key=lambda x: -x[1])),
            "record_count": len(records),
        }

    def get_trend(self, days: int = 7) -> dict[str, Any]:
        """获取成本趋势（按天）。"""
        now = datetime.now()
        daily_costs: list[dict[str, Any]] = []
        for i in range(days - 1, -1, -1):
            date = now - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            day_records = [
                r for r in self.records
                if day_start.timestamp() <= r.timestamp < day_end.timestamp()
            ]
            daily_costs.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "cost": round(sum(r.cost for r in day_records), 4),
                "requests": len(day_records),
                "tokens": sum(r.input_tokens + r.output_tokens for r in day_records),
            })
        return {
            "days": days,
            "daily": daily_costs,
            "total": round(sum(d["cost"] for d in daily_costs), 4),
            "avg_daily": round(sum(d["cost"] for d in daily_costs) / days, 4),
        }

    # ---------- 预算告警 ----------
    def _check_budget(self) -> None:
        """检查预算告警。"""
        daily = self.get_cost_summary("daily")
        today = datetime.now().strftime("%Y-%m-%d")

        if daily["usage_rate"] >= self.budget.critical_threshold:
            if not self._daily_alerted.get(f"{today}_critical"):
                alert = CostAlert(
                    level="critical",
                    message=f"日成本 ${daily['total_cost']:.2f} 超过预算 ${daily['budget']:.2f} 的 120%",
                    current_cost=daily["total_cost"],
                    budget=daily["budget"],
                    timestamp=datetime.now().isoformat(),
                )
                self._fire_alert(alert)
                self._daily_alerted[f"{today}_critical"] = True
        elif daily["usage_rate"] >= self.budget.alert_threshold:
            if not self._daily_alerted.get(f"{today}_warning"):
                alert = CostAlert(
                    level="warning",
                    message=f"日成本 ${daily['total_cost']:.2f} 达到预算 ${daily['budget']:.2f} 的 80%",
                    current_cost=daily["total_cost"],
                    budget=daily["budget"],
                    timestamp=datetime.now().isoformat(),
                )
                self._fire_alert(alert)
                self._daily_alerted[f"{today}_warning"] = True

    def _fire_alert(self, alert: CostAlert) -> None:
        """触发告警通知。"""
        self.alerts.append(alert)
        for notifier in self._notifiers:
            try:
                notifier(alert)
            except Exception as exc:  # noqa: BLE001
                logger.error(f"告警通知失败: {exc}")

    @staticmethod
    def _log_notifier(alert: CostAlert) -> None:
        """日志告警通知器。"""
        log_fn = logger.warning if alert.level == "warning" else logger.critical
        log_fn(f"[COST ALERT][{alert.level.upper()}] {alert.message}")

    def add_email_notifier(self, email: str) -> None:
        """添加邮件通知器（需配置 SMTP）。"""
        def email_notifier(alert: CostAlert) -> None:
            logger.info(f"[邮件通知] 发送至 {email}: {alert.message}")
            # 实际实现需接入 SMTP，此处仅记录
        self._notifiers.append(email_notifier)

    def add_webhook_notifier(self, webhook_url: str) -> None:
        """添加 Webhook 通知器。"""
        def webhook_notifier(alert: CostAlert) -> None:
            logger.info(f"[Webhook] 推送至 {webhook_url}: {alert.message}")
            # 实际实现可用 requests.post 推送
        self._notifiers.append(webhook_notifier)

    # ---------- 报告 ----------
    def generate_report(self) -> dict[str, Any]:
        """生成完整成本报告。"""
        return {
            "timestamp": datetime.now().isoformat(),
            "daily": self.get_cost_summary("daily"),
            "weekly": self.get_cost_summary("weekly"),
            "monthly": self.get_cost_summary("monthly"),
            "trend_7d": self.get_trend(7),
            "recent_alerts": [
                {
                    "level": a.level,
                    "message": a.message,
                    "current_cost": round(a.current_cost, 4),
                    "budget": a.budget,
                    "timestamp": a.timestamp,
                }
                for a in self.alerts[-5:]
            ],
        }


def demo_cost_monitor() -> None:
    """演示成本监控。"""
    import random

    monitor = CostMonitor(
        budget=BudgetConfig(daily_budget=10.0, weekly_budget=50.0, monthly_budget=200.0),
    )
    monitor.add_webhook_notifier("https://hooks.example.com/cost-alert")

    models = ["gpt-4o", "gpt-4o-mini"]
    endpoints = ["/chat", "/stream", "/embed"]
    prices = {"gpt-4o": (0.0025, 0.01), "gpt-4o-mini": (0.00015, 0.0006)}

    print("=== 模拟 200 次请求 ===")
    for i in range(200):
        model = random.choice(models)
        endpoint = random.choice(endpoints)
        in_tok = random.randint(50, 500)
        out_tok = random.randint(50, 300)
        in_price, out_price = prices[model]
        cost = (in_tok / 1000) * in_price + (out_tok / 1000) * out_price
        monitor.record(
            model=model,
            user_id=f"user_{random.randint(1, 15)}",
            endpoint=endpoint,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost=cost,
        )

    # 报告
    report = monitor.generate_report()
    print("\n=== 成本报告 ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo_cost_monitor()
