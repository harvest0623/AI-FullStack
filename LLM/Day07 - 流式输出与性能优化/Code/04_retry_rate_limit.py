# 文件用途：重试与限流
# 1. 指数退避重试装饰器 @retry：可重试/不可重试错误区分、抖动 Jitter
# 2. TokenBucket 限流器：令牌桶算法
# 3. RateLimitHandler 类：含重试 + 限流 + 超时处理，封装 LLM 调用
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import asyncio
import functools
import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# 1. 指数退避重试装饰器
# ---------------------------------------------------------------------------
# 可重试异常名（按类名字符串匹配，避免强依赖 openai 的异常类型）
RETRYABLE_ERRORS = {
    "RateLimitError",       # 429
    "APITimeoutError",      # 408
    "APIConnectionError",   # 网络错误
    "InternalServerError",  # 500
    "APIError",             # 5xx 通用
    "TimeoutError",
    "ConnectionError",
}


def is_retryable(exc: Exception) -> bool:
    """判断异常是否可重试。"""
    name = type(exc).__name__
    if name in RETRYABLE_ERRORS:
        return True
    # 状态码判断（部分异常带 status_code 属性）
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status is not None:
        try:
            return int(status) in {429, 408, 500, 502, 503, 504}
        except (TypeError, ValueError):
            pass
    return False


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_check: Callable[[Exception], bool] = is_retryable,
):
    """
    指数退避重试装饰器（同步函数）。

    参数：
        max_attempts: 最大尝试次数（含首次）
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟上限
        jitter: 是否加抖动
        retryable_check: 判断异常是否可重试的函数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    if attempt >= max_attempts or not retryable_check(exc):
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay += random.uniform(0, 1)
                    print(f"  [retry] {func.__name__} 第 {attempt} 次失败 ({type(exc).__name__})，"
                          f"{delay:.2f}s 后重试...")
                    time.sleep(delay)

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_check: Callable[[Exception], bool] = is_retryable,
):
    """指数退避重试装饰器（异步函数）。"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    if attempt >= max_attempts or not retryable_check(exc):
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay += random.uniform(0, 1)
                    print(f"  [async_retry] {func.__name__} 第 {attempt} 次失败 ({type(exc).__name__})，"
                          f"{delay:.2f}s 后重试...")
                    await asyncio.sleep(delay)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# 2. Token Bucket 限流器
# ---------------------------------------------------------------------------
@dataclass
class TokenBucket:
    """
    令牌桶限流器。

    参数：
        capacity: 桶容量（最大突发）
        refill_rate: 每秒补充的令牌数
    """

    capacity: float
    refill_rate: float
    _tokens: float = 0.0
    _last_refill: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self._tokens = self.capacity

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def acquire(self, tokens: float = 1.0, timeout: float | None = None) -> bool:
        """
        尝试获取令牌。返回 True 表示获取成功。
        若不足且 timeout=None 立即返回 False；否则阻塞等待。
        """
        deadline = (time.time() + timeout) if timeout is not None else None
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                need = tokens - self._tokens
                wait = need / self.refill_rate
            if deadline is None:
                return False
            remaining = deadline - time.time()
            if remaining <= 0:
                return False
            time.sleep(min(wait, remaining))


# ---------------------------------------------------------------------------
# 3. RateLimitHandler：重试 + 限流 + 超时 一体化封装
# ---------------------------------------------------------------------------
class RateLimitHandler:
    """
    含重试 + 限流 + 超时的 LLM 调用封装。

    使用方式：
        handler = RateLimitHandler(rpm=60, max_attempts=3)
        output = handler.call_llm("讲个笑话", model="gpt-4o-mini")
    """

    def __init__(
        self,
        rpm: int = 60,
        max_attempts: int = 3,
        timeout: float = 30.0,
    ) -> None:
        # 每分钟 rpm 个请求 → 每秒 rpm/60 个令牌
        self.bucket = TokenBucket(capacity=float(rpm), refill_rate=rpm / 60.0)
        self.max_attempts = max_attempts
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY")
            self._client = OpenAI(api_key=api_key, timeout=self.timeout)
        return self._client

    @retry(max_attempts=3, base_delay=1.0)
    def _call_with_retry(self, prompt: str, model: str) -> str:
        """带重试的实际调用（被装饰器包裹）。"""
        # 限流：先拿令牌
        if not self.bucket.acquire(tokens=1.0, timeout=self.timeout):
            raise RuntimeError("限流等待超时")
        client = self._get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=256,
        )
        return resp.choices[0].message.content or ""

    def call_llm(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """对外入口：限流 + 重试 + 超时。"""
        return self._call_with_retry(prompt, model)


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------
def demo_retry() -> None:
    print("=" * 60)
    print("演示 1：重试装饰器（用模拟失败函数）")
    print("=" * 60)

    call_count = {"n": 0}

    @retry(max_attempts=4, base_delay=0.5, jitter=False)
    def flaky_call():
        call_count["n"] += 1
        # 前 3 次抛可重试异常，第 4 次成功
        if call_count["n"] < 4:
            raise ConnectionError("模拟网络错误")
        return "成功！"

    try:
        result = flaky_call()
        print(f"结果：{result}（共调用 {call_count['n']} 次）")
    except Exception as exc:
        print(f"最终失败：{exc}")

    # 不可重试异常演示
    print("\n--- 不可重试异常（立即失败）---")
    call_count["n"] = 0

    @retry(max_attempts=3)
    def bad_request():
        call_count["n"] += 1
        raise ValueError("参数错误（不可重试）")

    try:
        bad_request()
    except ValueError as exc:
        print(f"立即失败：{exc}（共调用 {call_count['n']} 次）")


def demo_token_bucket() -> None:
    print("\n" + "=" * 60)
    print("演示 2：Token Bucket 限流")
    print("=" * 60)
    # 容量 5，每秒补 2 个令牌
    bucket = TokenBucket(capacity=5, refill_rate=2.0)
    print("容量=5，每秒补 2 个。连续尝试获取 8 次：")
    for i in range(8):
        ok = bucket.acquire(timeout=2.0)
        print(f"  第 {i + 1} 次：{'✓' if ok else '✗'}  剩余令牌≈{bucket._tokens:.2f}")
        time.sleep(0.2)


def demo_handler() -> None:
    print("\n" + "=" * 60)
    print("演示 3：RateLimitHandler 完整调用")
    print("=" * 60)
    if not os.getenv("OPENAI_API_KEY"):
        print("[跳过] 未配置 OPENAI_API_KEY")
        return
    handler = RateLimitHandler(rpm=60, max_attempts=3, timeout=30.0)
    for i in range(3):
        out = handler.call_llm(f"用一句话回答：什么是 AI？（第 {i + 1} 次）")
        print(f"  [{i + 1}] {out[:50]}")


def main() -> None:
    demo_retry()
    demo_token_bucket()
    demo_handler()


if __name__ == "__main__":
    main()
