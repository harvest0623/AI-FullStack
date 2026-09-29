# 文件用途：异步批量调用
# AsyncBatchProcessor 类：用 asyncio.gather 并发调用多个 LLM 请求，
# 信号量控制并发数。展示串行 vs 并发的性能对比。
# 适用场景：批量翻译 / 分类 / 摘要。
# 运行前：pip install openai python-dotenv；在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BatchResult:
    """单个批量请求结果。"""

    index: int
    prompt: str
    output: str = ""
    latency_sec: float = 0.0
    error: str | None = None


@dataclass
class BatchReport:
    """批量处理报告。"""

    mode: str  # serial / concurrent
    concurrency: int
    results: list[BatchResult] = field(default_factory=list)
    total_sec: float = 0.0

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.error is None)

    @property
    def avg_latency(self) -> float:
        ok = [r for r in self.results if r.error is None]
        return sum(r.latency_sec for r in ok) / max(len(ok), 1)

    def summary(self) -> str:
        return (
            f"[{self.mode}] 并发数={self.concurrency} | "
            f"总数={len(self.results)} | 成功={self.ok_count} | "
            f"总耗时={self.total_sec:.2f}s | 平均单请求={self.avg_latency:.2f}s"
        )


class AsyncBatchProcessor:
    """
    异步批量处理器。

    使用方式：
        processor = AsyncBatchProcessor(model="gpt-4o-mini")
        # 串行
        report_s = processor.run_serial(prompts)
        # 并发（限 5）
        report_c = asyncio.run(processor.run_concurrent(prompts, concurrency=5))
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._async_client = None

    def _get_client(self):
        if self._async_client is None:
            from openai import AsyncOpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY")
            self._async_client = AsyncOpenAI(api_key=api_key)
        return self._async_client

    async def _call_one(self, prompt: str, index: int, sem: asyncio.Semaphore | None = None) -> BatchResult:
        """单个异步调用。"""
        result = BatchResult(index=index, prompt=prompt)
        start = time.perf_counter()
        try:
            client = self._get_client()
            if sem is not None:
                async with sem:
                    resp = await client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                        max_tokens=256,
                    )
            else:
                resp = await client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=256,
                )
            result.output = resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
        finally:
            result.latency_sec = time.perf_counter() - start
        return result

    # ------------------------- 串行 -------------------------
    async def run_serial_async(self, prompts: list[str]) -> BatchReport:
        """异步串行：一个接一个，无并发。"""
        report = BatchReport(mode="serial", concurrency=1)
        start = time.perf_counter()
        for i, p in enumerate(prompts):
            r = await self._call_one(p, i)
            report.results.append(r)
            print(f"  [{i + 1}/{len(prompts)}] {r.latency_sec:.2f}s {'OK' if r.error is None else 'FAIL'}")
        report.total_sec = time.perf_counter() - start
        return report

    def run_serial(self, prompts: list[str]) -> BatchReport:
        """同步入口：跑异步串行。"""
        return asyncio.run(self.run_serial_async(prompts))

    # ------------------------- 并发 -------------------------
    async def run_concurrent(self, prompts: list[str], concurrency: int = 5) -> BatchReport:
        """并发执行：用 Semaphore 限制最大并发数。"""
        report = BatchReport(mode="concurrent", concurrency=concurrency)
        sem = asyncio.Semaphore(concurrency)
        start = time.perf_counter()
        tasks = [self._call_one(p, i, sem) for i, p in enumerate(prompts)]
        # gather 保持顺序
        results = await asyncio.gather(*tasks)
        for r in results:
            report.results.append(r)
            print(f"  [{r.index + 1}/{len(prompts)}] {r.latency_sec:.2f}s {'OK' if r.error is None else 'FAIL'}")
        report.total_sec = time.perf_counter() - start
        return report


# ---------------------------------------------------------------------------
# 演示：串行 vs 并发对比
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    # 模拟批量翻译任务
    prompts = [f"把下面这句英文翻译成中文，只输出译文：Hello world number {i}." for i in range(1, 11)]
    print(f"任务：翻译 {len(prompts)} 条短句\n")

    processor = AsyncBatchProcessor(model="gpt-4o-mini")

    print("=" * 60)
    print("1. 串行执行")
    print("=" * 60)
    report_s = processor.run_serial(prompts)
    print(report_s.summary())

    print("\n" + "=" * 60)
    print("2. 并发执行（concurrency=3）")
    print("=" * 60)
    report_c = asyncio.run(processor.run_concurrent(prompts, concurrency=3))
    print(report_c.summary())

    print("\n" + "=" * 60)
    print("3. 并发执行（concurrency=5）")
    print("=" * 60)
    report_c5 = asyncio.run(processor.run_concurrent(prompts, concurrency=5))
    print(report_c5.summary())

    # 对比
    print("\n" + "=" * 60)
    print("性能对比")
    print("=" * 60)
    speedup_s_c3 = report_s.total_sec / max(report_c.total_sec, 0.001)
    speedup_s_c5 = report_s.total_sec / max(report_c5.total_sec, 0.001)
    print(f"串行 → 并发(3)：{report_s.total_sec:.2f}s → {report_c.total_sec:.2f}s，加速 {speedup_s_c3:.2f}x")
    print(f"串行 → 并发(5)：{report_s.total_sec:.2f}s → {report_c5.total_sec:.2f}s，加速 {speedup_s_c5:.2f}x")


if __name__ == "__main__":
    demo()
