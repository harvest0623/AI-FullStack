# 文件用途：成本与延迟分析
# CostLatencyAnalyzer 类：实测各模型的 TTFT（首字延迟）/ 生成速度 / 总延迟 /
# Token 消耗 / 成本，并生成对比报告。含月度成本估算功能。
# 运行前：在 .env 中配置 OPENAI_API_KEY（如需测试 Anthropic，配 ANTHROPIC_API_KEY）

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Callable

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# 价格表（美元 / 1M token）
# ---------------------------------------------------------------------------
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "o1-mini": (3.0, 12.0),
    "claude-3-5-sonnet-20240620": (3.0, 15.0),
}


@dataclass
class LatencyRecord:
    """一次调用的延迟与成本记录。"""

    model: str
    ttft_sec: float = 0.0          # 首字延迟
    total_sec: float = 0.0         # 总延迟
    completion_tokens: int = 0
    tokens_per_sec: float = 0.0    # 生成速度
    prompt_tokens: int = 0
    cost_usd: float = 0.0
    output: str = ""
    error: str | None = None


@dataclass
class LatencyReport:
    """多模型延迟对比报告。"""

    prompt: str
    records: list[LatencyRecord] = field(default_factory=list)

    def add(self, r: LatencyRecord) -> None:
        self.records.append(r)

    def to_markdown(self) -> str:
        lines = [
            "# 成本与延迟对比报告",
            "",
            f"测试 Prompt：{self.prompt[:120]}{'...' if len(self.prompt) > 120 else ''}",
            "",
            "| 模型 | TTFT(s) | 总延迟(s) | 生成速度(tok/s) | 输入tok | 输出tok | 成本($) | 状态 |",
            "|------|---------|-----------|----------------|---------|---------|---------|------|",
        ]
        for r in self.records:
            status = "OK" if r.error is None else "FAIL"
            lines.append(
                f"| {r.model} | {r.ttft_sec:.3f} | {r.total_sec:.3f} | "
                f"{r.tokens_per_sec:.1f} | {r.prompt_tokens} | {r.completion_tokens} | "
                f"{r.cost_usd:.6f} | {status} |"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 分析器
# ---------------------------------------------------------------------------
class CostLatencyAnalyzer:
    """
    成本与延迟分析器。

    使用方式：
        analyzer = CostLatencyAnalyzer()
        analyzer.register_openai("gpt-4o-mini")
        analyzer.register_openai("gpt-4o")
        report = analyzer.measure("用 100 字解释 RAG", repeat=3)
        print(report.to_markdown())
        analyzer.estimate_monthly_cost(report.records, daily_requests=1000)
    """

    def __init__(self) -> None:
        self._callers: list[tuple[str, Callable[[str], LatencyRecord]]] = []
        self._openai_client = None
        self._anthropic_client = None

    # ------------------------- 客户端 -------------------------
    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            import anthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 ANTHROPIC_API_KEY")
            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self._anthropic_client

    # ------------------------- 注册 -------------------------
    def register_openai(self, model: str) -> None:
        self._callers.append((model, lambda prompt, m=model: self._call_openai_stream(m, prompt)))

    def register_anthropic(self, model: str) -> None:
        self._callers.append((model, lambda prompt, m=model: self._call_anthropic_stream(m, prompt)))

    # ------------------------- 流式调用：测 TTFT / 速度 -------------------------
    def _call_openai_stream(self, model: str, prompt: str) -> LatencyRecord:
        rec = LatencyRecord(model=model)
        client = self._get_openai_client()
        chunks: list[str] = []
        start = time.perf_counter()
        first_chunk_time: float | None = None
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                stream=True,
                stream_options={"include_usage": True},
            )
            for chunk in stream:
                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()
                if chunk.choices and chunk.choices[0].delta.content:
                    chunks.append(chunk.choices[0].delta.content)
                # usage 在最后一个 chunk
                if getattr(chunk, "usage", None):
                    rec.prompt_tokens = chunk.usage.prompt_tokens or 0
                    rec.completion_tokens = chunk.usage.completion_tokens or 0
            rec.ttft_sec = (first_chunk_time - start) if first_chunk_time else 0.0
            rec.total_sec = time.perf_counter() - start
            rec.output = "".join(chunks)
            if rec.completion_tokens and rec.total_sec > rec.ttft_sec:
                gen_time = rec.total_sec - rec.ttft_sec
                rec.tokens_per_sec = rec.completion_tokens / gen_time if gen_time > 0 else 0.0
            rec.cost_usd = self._compute_cost(model, rec.prompt_tokens, rec.completion_tokens)
        except Exception as exc:  # noqa: BLE001
            rec.error = f"{type(exc).__name__}: {exc}"
            rec.total_sec = time.perf_counter() - start
        return rec

    def _call_anthropic_stream(self, model: str, prompt: str) -> LatencyRecord:
        rec = LatencyRecord(model=model)
        client = self._get_anthropic_client()
        chunks: list[str] = []
        start = time.perf_counter()
        first_chunk_time: float | None = None
        try:
            with client.messages.stream(
                model=model,
                max_tokens=512,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    if first_chunk_time is None:
                        first_chunk_time = time.perf_counter()
                    chunks.append(text)
                final = stream.get_final_message()
            rec.ttft_sec = (first_chunk_time - start) if first_chunk_time else 0.0
            rec.total_sec = time.perf_counter() - start
            rec.output = "".join(chunks)
            rec.prompt_tokens = final.usage.input_tokens
            rec.completion_tokens = final.usage.output_tokens
            if rec.completion_tokens and rec.total_sec > rec.ttft_sec:
                gen_time = rec.total_sec - rec.ttft_sec
                rec.tokens_per_sec = rec.completion_tokens / gen_time if gen_time > 0 else 0.0
            rec.cost_usd = self._compute_cost(model, rec.prompt_tokens, rec.completion_tokens)
        except Exception as exc:  # noqa: BLE001
            rec.error = f"{type(exc).__name__}: {exc}"
            rec.total_sec = time.perf_counter() - start
        return rec

    # ------------------------- 成本计算 -------------------------
    @staticmethod
    def _compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return 0.0
        in_p, out_p = pricing
        return (prompt_tokens / 1_000_000) * in_p + (completion_tokens / 1_000_000) * out_p

    # ------------------------- 测量入口 -------------------------
    def measure(self, prompt: str, repeat: int = 1) -> LatencyReport:
        """对同一 prompt 调用所有已注册模型，可选重复多次取平均。"""
        report = LatencyReport(prompt=prompt)
        for model_name, caller in self._callers:
            print(f"  → 测量 {model_name} (repeat={repeat}) ...")
            records: list[LatencyRecord] = []
            for _ in range(repeat):
                r = caller(prompt)
                records.append(r)
            # 取平均
            avg = self._average(records, model_name)
            report.add(avg)
        return report

    @staticmethod
    def _average(records: list[LatencyRecord], model: str) -> LatencyRecord:
        ok = [r for r in records if r.error is None]
        if not ok:
            return records[0]
        n = len(ok)
        return LatencyRecord(
            model=model,
            ttft_sec=sum(r.ttft_sec for r in ok) / n,
            total_sec=sum(r.total_sec for r in ok) / n,
            completion_tokens=int(sum(r.completion_tokens for r in ok) / n),
            tokens_per_sec=sum(r.tokens_per_sec for r in ok) / n,
            prompt_tokens=int(sum(r.prompt_tokens for r in ok) / n),
            cost_usd=sum(r.cost_usd for r in ok) / n,
            output=ok[-1].output,
        )

    # ------------------------- 月度成本估算 -------------------------
    @staticmethod
    def estimate_monthly_cost(records: list[LatencyRecord], daily_requests: int = 1000) -> str:
        """根据单次成本估算月度成本（30 天）。"""
        lines = [
            "",
            "## 月度成本估算",
            "",
            f"假设日请求量：{daily_requests} 次（30 天共 {daily_requests * 30} 次）",
            "",
            "| 模型 | 单次成本 | 日成本 | 月成本 |",
            "|------|---------|--------|--------|",
        ]
        for r in records:
            if r.error is not None:
                continue
            daily = r.cost_usd * daily_requests
            monthly = daily * 30
            lines.append(
                f"| {r.model} | ${r.cost_usd:.6f} | ${daily:.2f} | ${monthly:.2f} |"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    analyzer = CostLatencyAnalyzer()
    analyzer.register_openai("gpt-4o-mini")
    analyzer.register_openai("gpt-4o")

    prompt = "用 100 字解释什么是检索增强生成（RAG）。"
    print(f"\n测试 Prompt：{prompt}\n")

    report = analyzer.measure(prompt, repeat=2)
    print("\n" + "=" * 60)
    print(report.to_markdown())
    print(analyzer.estimate_monthly_cost(report.records, daily_requests=1000))


if __name__ == "__main__":
    demo()
