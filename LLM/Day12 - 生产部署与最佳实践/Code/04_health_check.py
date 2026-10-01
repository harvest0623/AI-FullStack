# 文件用途：健康检查与告警
# HealthChecker 类：检查 LLM API 可用性 / 响应延迟 / 错误率 / 缓存命中率
# 熔断器实现（连续失败暂停请求），故障转移逻辑（主模型故障→备用模型）
# 告警通知，含 /health 和 /ready 接口实现
# Python 3.10+ 可运行（纯标准库）

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("health-checker")


class CircuitState(str, Enum):
    """熔断器状态。"""

    CLOSED = "closed"      # 正常放行
    OPEN = "open"          # 熔断，拒绝请求
    HALF_OPEN = "half_open"  # 半开，试探性放行


@dataclass
class CircuitConfig:
    """熔断器配置。"""

    failure_threshold: int = 5        # 连续失败次数阈值
    recovery_timeout: float = 30.0    # 熔断后恢复试探时间（秒）
    half_open_max: int = 3            # 半开状态最大试探请求数
    success_threshold: int = 2        # 半开转闭合的成功次数


@dataclass
class HealthStatus:
    """健康状态。"""

    healthy: bool
    latency: float
    error_rate: float
    cache_hit_rate: float
    circuit_state: str
    details: dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """熔断器实现。"""

    def __init__(self, config: CircuitConfig | None = None) -> None:
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_count = 0
        self._last_failure_time = 0.0
        self._lock_calls: list[bool] = []  # 最近调用结果

    def allow_request(self) -> bool:
        """是否允许请求通过。"""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            # 检查是否到了恢复试探时间
            if time.time() - self._last_failure_time >= self.config.recovery_timeout:
                logger.info("熔断器进入半开状态，开始试探")
                self.state = CircuitState.HALF_OPEN
                self._half_open_count = 0
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_count < self.config.half_open_max:
                self._half_open_count += 1
                return True
            return False
        return False

    def record_success(self) -> None:
        """记录成功。"""
        self._lock_calls.append(True)
        if len(self._lock_calls) > 100:
            self._lock_calls = self._lock_calls[-100:]

        if self.state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                logger.info("熔断器恢复闭合状态")
                self.state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self.state == CircuitState.CLOSED:
            self._failure_count = 0

    def record_failure(self) -> None:
        """记录失败。"""
        self._lock_calls.append(False)
        if len(self._lock_calls) > 100:
            self._lock_calls = self._lock_calls[-100:]

        self._last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("半开状态试探失败，重新熔断")
            self.state = CircuitState.OPEN
            self._success_count = 0
        elif self.state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"连续失败 {self._failure_count} 次，熔断器开启"
                )
                self.state = CircuitState.OPEN

    @property
    def error_rate(self) -> float:
        """最近错误率。"""
        if not self._lock_calls:
            return 0.0
        failures = sum(1 for x in self._lock_calls if not x)
        return failures / len(self._lock_calls)


class HealthChecker:
    """LLM 服务健康检查器。"""

    def __init__(self) -> None:
        self._latencies: deque[float] = deque(maxlen=1000)
        self._cache_hits: deque[bool] = deque(maxlen=1000)
        self._error_count = 0
        self._total_count = 0
        self._start_time = time.time()
        self._check_fn: Callable[[], bool] | None = None
        self.circuit = CircuitBreaker()

    def set_check_function(self, fn: Callable[[], bool]) -> None:
        """设置健康检查函数（返回 True 表示健康）。"""
        self._check_fn = fn

    def record_request(
        self,
        latency: float,
        success: bool,
        cache_hit: bool = False,
    ) -> None:
        """记录一次请求结果。"""
        self._total_count += 1
        if success:
            self._latencies.append(latency)
            self.circuit.record_success()
        else:
            self._error_count += 1
            self.circuit.record_failure()
        self._cache_hits.append(cache_hit)

    def check(self) -> HealthStatus:
        """执行健康检查。"""
        latencies = list(self._latencies)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        error_rate = (
            self._error_count / self._total_count if self._total_count > 0 else 0
        )

        cache_hits = list(self._cache_hits)
        cache_hit_rate = (
            sum(1 for h in cache_hits if h) / len(cache_hits) if cache_hits else 0
        )

        # 外部检查函数
        external_ok = True
        if self._check_fn:
            try:
                external_ok = self._check_fn()
            except Exception as exc:  # noqa: BLE001
                logger.error(f"健康检查函数异常: {exc}")
                external_ok = False

        healthy = (
            external_ok
            and self.circuit.state != CircuitState.OPEN
            and error_rate < 0.1
        )

        return HealthStatus(
            healthy=healthy,
            latency=round(avg_latency, 3),
            error_rate=round(error_rate, 4),
            cache_hit_rate=round(cache_hit_rate, 4),
            circuit_state=self.circuit.state.value,
            details={
                "total_requests": self._total_count,
                "error_count": self._error_count,
                "uptime": round(time.time() - self._start_time, 2),
                "circuit_failures": self.circuit._failure_count,
            },
        )

    def health_endpoint(self) -> dict[str, Any]:
        """/health 接口实现（存活探针）。"""
        status = self.check()
        return {
            "status": "healthy" if status.healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": status.details["uptime"],
        }

    def ready_endpoint(self) -> dict[str, Any]:
        """/ready 接口实现（就绪探针）。"""
        status = self.check()
        return {
            "ready": status.healthy,
            "status": status.details,
            "latency": status.latency,
            "error_rate": status.error_rate,
            "cache_hit_rate": status.cache_hit_rate,
            "circuit_state": status.circuit_state,
        }


class FailoverManager:
    """故障转移管理器：主模型故障时切换到备用模型。"""

    def __init__(self) -> None:
        self._models: list[tuple[str, Callable[[], Any]]] = []
        self._current_index = 0
        self._circuit = CircuitBreaker()

    def add_model(self, name: str, handler: Callable[[], Any]) -> None:
        """添加模型处理器。"""
        self._models.append((name, handler))

    def call(self, *args, **kwargs) -> Any:
        """调用模型，失败时自动故障转移。"""
        if not self._models:
            raise RuntimeError("未配置任何模型处理器")

        last_error: Exception | None = None
        for idx in range(len(self._models)):
            model_idx = (self._current_index + idx) % len(self._models)
            name, handler = self._models[model_idx]
            try:
                if not self._circuit.allow_request():
                    continue
                result = handler(*args, **kwargs)
                self._circuit.record_success()
                if idx > 0:
                    logger.info(f"故障转移到 {name}")
                    self._current_index = model_idx
                return result
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"模型 {name} 调用失败: {exc}")
                self._circuit.record_failure()
                last_error = exc
                continue

        raise RuntimeError(f"所有模型均调用失败，最后错误: {last_error}")


def demo_health_check() -> None:
    """演示健康检查与熔断器。"""
    import random

    checker = HealthChecker()

    print("=== 模拟请求记录 ===")
    for i in range(100):
        latency = random.uniform(0.2, 3.0)
        success = random.random() > 0.05
        cache_hit = random.random() > 0.6
        checker.record_request(latency, success, cache_hit)

    # 健康检查
    health = checker.check()
    print(f"\n健康状态: {health}")

    # /health 接口
    print(f"\n/health: {checker.health_endpoint()}")
    # /ready 接口
    print(f"\n/ready: {checker.ready_endpoint()}")

    # 熔断器演示
    print("\n=== 熔断器演示 ===")
    breaker = CircuitBreaker(CircuitConfig(failure_threshold=3, recovery_timeout=2))
    for i in range(5):
        allowed = breaker.allow_request()
        print(f"请求 {i+1}: 允许={allowed}, 状态={breaker.state.value}")
        if allowed:
            breaker.record_failure()
            print(f"  → 记录失败, 失败计数={breaker._failure_count}")

    print(f"\n熔断后请求: 允许={breaker.allow_request()}, 状态={breaker.state.value}")

    # 故障转移演示
    print("\n=== 故障转移演示 ===")
    manager = FailoverManager()

    def primary_model(prompt: str) -> str:
        raise RuntimeError("主模型不可用")

    def backup_model(prompt: str) -> str:
        return f"备用模型回答: {prompt}"

    manager.add_model("primary", primary_model)
    manager.add_model("backup", backup_model)

    result = manager.call("你好")
    print(f"故障转移结果: {result}")


if __name__ == "__main__":
    demo_health_check()
