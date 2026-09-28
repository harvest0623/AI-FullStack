# 文件用途：多模型输出对比工具
# 对同一输入并行/串行调用多个 LLM（OpenAI / Anthropic / 通义千问），
# 收集输出文本、响应时间、Token 消耗与估算成本，并排展示对比结果。
# 适用场景：模型选型阶段的质量与成本对比。
# 运行前：在 .env 中配置 OPENAI_API_KEY / ANTHROPIC_API_KEY / DASHSCOPE_API_KEY

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Callable

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# 价格表（美元 / 1M token，示例值，请以官方最新定价为准）
# ---------------------------------------------------------------------------
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4-turbo": (10.0, 30.0),
    "o1-mini": (3.0, 12.0),
    # Anthropic
    "claude-3-5-sonnet-20240620": (3.0, 15.0),
    "claude-3-opus-20240229": (15.0, 75.0),
    # 通义千问（OpenAI 兼容入口）
    "qwen-turbo": (0.05, 0.2),
    "qwen-plus": (0.4, 1.2),
}


@dataclass
class ModelResult:
    """单个模型对一次调用的结果记录。"""

    model: str
    output: str = ""
    latency_sec: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class ComparisonReport:
    """一次对比测试的整体报告。"""

    prompt: str
    results: list[ModelResult] = field(default_factory=list)

    def add(self, result: ModelResult) -> None:
        self.results.append(result)

    def render(self) -> str:
        """渲染为可读的 Markdown 文本并打印到控制台。"""
        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("多模型对比报告")
        lines.append("=" * 80)
        lines.append(f"输入 Prompt：{self.prompt[:200]}{'...' if len(self.prompt) > 200 else ''}")
        lines.append("-" * 80)

        # 概览表
        lines.append(f"{'模型':<32}{'延迟(s)':>10}{'输入tok':>10}{'输出tok':>10}{'成本($)':>12}{'状态':>8}")
        for r in self.results:
            status = "OK" if r.ok else "FAIL"
            lines.append(
                f"{r.model:<32}{r.latency_sec:>10.2f}{r.prompt_tokens:>10}"
                f"{r.completion_tokens:>10}{r.cost_usd:>12.6f}{status:>8}"
            )
        lines.append("-" * 80)

        # 各模型输出
        for r in self.results:
            lines.append(f"\n【{r.model}】")
            if r.ok:
                lines.append(r.output)
            else:
                lines.append(f"[错误] {r.error}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


class ModelComparator:
    """
    多模型对比器。

    使用方式：
        comparator = ModelComparator()
        comparator.register_openai("gpt-4o")
        comparator.register_openai("gpt-4o-mini")
        comparator.register_anthropic("claude-3-5-sonnet-20240620")
        report = comparator.compare("用一句话解释什么是 RAG")
        print(report.render())
    """

    def __init__(self) -> None:
        # 每个 provider 是 (model_name, callable) 的工厂
        self._callers: list[tuple[str, Callable[[str], ModelResult]]] = []
        self._openai_client = None
        self._anthropic_client = None

    # ------------------------- 客户端懒加载 -------------------------
    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY，请在 .env 中设置")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError("未安装 anthropic 包，请 pip install anthropic") from exc

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 ANTHROPIC_API_KEY，请在 .env 中设置")
            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self._anthropic_client

    # ------------------------- 模型注册 -------------------------
    def register_openai(self, model: str, base_url: str | None = None) -> None:
        """注册一个 OpenAI 兼容模型（含通义千问 OpenAI 兼容入口）。"""
        self._callers.append((model, lambda prompt, m=model, b=base_url: self._call_openai(m, prompt, b)))

    def register_anthropic(self, model: str) -> None:
        """注册一个 Anthropic Claude 模型。"""
        self._callers.append((model, lambda prompt, m=model: self._call_anthropic(m, prompt)))

    # ------------------------- 实际调用 -------------------------
    def _call_openai(self, model: str, prompt: str, base_url: str | None) -> ModelResult:
        result = ModelResult(model=model)
        start = time.perf_counter()
        try:
            kwargs = {"api_key": os.getenv("OPENAI_API_KEY")}
            if base_url:
                kwargs["base_url"] = base_url
            # 若指定了 base_url（如通义千问），单独构造客户端
            if base_url:
                from openai import OpenAI

                client = OpenAI(**kwargs)
            else:
                client = self._get_openai_client()

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            result.output = resp.choices[0].message.content or ""
            usage = resp.usage
            result.prompt_tokens = usage.prompt_tokens if usage else 0
            result.completion_tokens = usage.completion_tokens if usage else 0
            result.total_tokens = usage.total_tokens if usage else 0
            result.cost_usd = self._compute_cost(model, result.prompt_tokens, result.completion_tokens)
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
        finally:
            result.latency_sec = time.perf_counter() - start
        return result

    def _call_anthropic(self, model: str, prompt: str) -> ModelResult:
        result = ModelResult(model=model)
        start = time.perf_counter()
        try:
            client = self._get_anthropic_client()
            resp = client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            # content 是 list[ContentBlock]，拼接文本
            result.output = "".join(block.text for block in resp.content if hasattr(block, "text"))
            usage = resp.usage
            result.prompt_tokens = usage.input_tokens if usage else 0
            result.completion_tokens = usage.output_tokens if usage else 0
            result.total_tokens = result.prompt_tokens + result.completion_tokens
            result.cost_usd = self._compute_cost(model, result.prompt_tokens, result.completion_tokens)
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
        finally:
            result.latency_sec = time.perf_counter() - start
        return result

    # ------------------------- 成本计算 -------------------------
    @staticmethod
    def _compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return 0.0
        in_price, out_price = pricing
        return (prompt_tokens / 1_000_000) * in_price + (completion_tokens / 1_000_000) * out_price

    # ------------------------- 对比入口 -------------------------
    def compare(self, prompt: str) -> ComparisonReport:
        """对同一 prompt 调用所有已注册模型，返回对比报告。"""
        report = ComparisonReport(prompt=prompt)
        for model_name, caller in self._callers:
            print(f"  → 调用 {model_name} ...")
            result = caller(prompt)
            report.add(result)
        return report


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    """演示：对比 OpenAI / Anthropic / 通义千问 三家模型。"""
    comparator = ModelComparator()

    # 1. OpenAI 两档模型
    if os.getenv("OPENAI_API_KEY"):
        comparator.register_openai("gpt-4o-mini")
        comparator.register_openai("gpt-4o")
    else:
        print("[警告] 未配置 OPENAI_API_KEY，跳过 OpenAI 模型")

    # 2. Anthropic Claude
    if os.getenv("ANTHROPIC_API_KEY"):
        comparator.register_anthropic("claude-3-5-sonnet-20240620")
    else:
        print("[警告] 未配置 ANTHROPIC_API_KEY，跳过 Claude 模型")

    # 3. 通义千问（OpenAI 兼容入口）
    if os.getenv("DASHSCOPE_API_KEY"):
        comparator.register_openai(
            "qwen-turbo",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    else:
        print("[警告] 未配置 DASHSCOPE_API_KEY，跳过通义千问模型")

    if not comparator._callers:
        print("[错误] 没有可用的模型客户端，请至少配置一个 API Key")
        return

    prompt = "用三句话向一名初中生解释什么是大语言模型（LLM）。"
    print(f"\n对比 Prompt：{prompt}\n")

    report = comparator.compare(prompt)
    print()
    print(report.render())


if __name__ == "__main__":
    demo()
