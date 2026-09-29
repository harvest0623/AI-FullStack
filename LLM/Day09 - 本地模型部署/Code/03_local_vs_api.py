# 文件用途：本地模型 vs API 性能对比
# 对比同一任务在本地模型和 API 模型上的响应时间、输出质量、Token 消耗、成本
# 生成对比报告，含延迟和吞吐量基准测试
# Python 3.10+ 可运行
# 依赖：pip install openai
# 需配置环境变量：OPENAI_API_KEY、OLLAMA_BASE_URL（默认 http://localhost:11434/v1）

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


@dataclass
class ModelEndpoint:
    """模型端点配置。"""

    name: str
    base_url: str
    api_key: str
    model: str
    input_price: float = 0.0   # 每 1K token 输入价格（美元）
    output_price: float = 0.0  # 每 1K token 输出价格（美元）
    is_local: bool = False


class LocalVsAPIComparator:
    """本地模型与 API 模型性能对比器。"""

    def __init__(self, endpoints: list[ModelEndpoint]) -> None:
        if OpenAI is None:
            raise ImportError("未安装 openai 包，请执行: pip install openai")
        self.endpoints = endpoints

    def _build_client(self, ep: ModelEndpoint) -> Any:
        return OpenAI(base_url=ep.base_url, api_key=ep.api_key)

    def single_test(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 512,
    ) -> list[dict[str, Any]]:
        """单次对比测试，返回各端点的指标。"""
        results: list[dict[str, Any]] = []
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for ep in self.endpoints:
            client = self._build_client(ep)
            start = time.time()
            try:
                resp = client.chat.completions.create(
                    model=ep.model,
                    messages=messages,
                    max_tokens=max_tokens,
                )
                elapsed = time.time() - start
                content = resp.choices[0].message.content or ""
                usage = resp.usage
                in_tokens = getattr(usage, "prompt_tokens", 0) or 0
                out_tokens = getattr(usage, "completion_tokens", 0) or 0
                cost = (in_tokens / 1000) * ep.input_price + (
                    out_tokens / 1000
                ) * ep.output_price
                results.append(
                    {
                        "endpoint": ep.name,
                        "is_local": ep.is_local,
                        "model": ep.model,
                        "latency": round(elapsed, 3),
                        "input_tokens": in_tokens,
                        "output_tokens": out_tokens,
                        "total_tokens": in_tokens + out_tokens,
                        "cost_usd": round(cost, 6),
                        "answer": content,
                        "status": "success",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "endpoint": ep.name,
                        "is_local": ep.is_local,
                        "model": ep.model,
                        "latency": round(time.time() - start, 3),
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "cost_usd": 0.0,
                        "answer": "",
                        "status": f"error: {exc}",
                    }
                )
        return results

    def batch_test(
        self,
        prompts: list[str],
        system: str | None = None,
        max_tokens: int = 512,
    ) -> dict[str, Any]:
        """批量测试，汇总统计指标。"""
        all_results: list[dict[str, Any]] = []
        for prompt in prompts:
            all_results.extend(self.single_test(prompt, system, max_tokens))

        # 按端点聚合
        summary: dict[str, dict[str, Any]] = {}
        for r in all_results:
            name = r["endpoint"]
            summary.setdefault(
                name,
                {
                    "endpoint": name,
                    "is_local": r["is_local"],
                    "model": r["model"],
                    "count": 0,
                    "success": 0,
                    "latencies": [],
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "answers": [],
                },
            )
            s = summary[name]
            s["count"] += 1
            if r["status"] == "success":
                s["success"] += 1
                s["latencies"].append(r["latency"])
                s["total_tokens"] += r["total_tokens"]
                s["total_cost"] += r["cost_usd"]
                s["answers"].append(r["answer"])

        # 计算最终统计
        report: list[dict[str, Any]] = []
        for name, s in summary.items():
            lats = s.pop("latencies")
            report.append(
                {
                    **s,
                    "avg_latency": round(sum(lats) / len(lats), 3) if lats else 0,
                    "min_latency": round(min(lats), 3) if lats else 0,
                    "max_latency": round(max(lats), 3) if lats else 0,
                    "avg_tokens": round(s["total_tokens"] / s["success"], 1)
                    if s["success"]
                    else 0,
                    "total_cost_usd": round(s["total_cost"], 6),
                }
            )
        return {"detail": all_results, "summary": report}

    def throughput_test(
        self,
        prompt: str,
        concurrency: int = 4,
        rounds: int = 16,
    ) -> list[dict[str, Any]]:
        """并发吞吐量测试，返回各端点 QPS。"""
        results: list[dict[str, Any]] = []
        messages = [{"role": "user", "content": prompt}]

        for ep in self.endpoints:
            client = self._build_client(ep)

            def one_request(_i: int) -> float:
                start = time.time()
                try:
                    client.chat.completions.create(
                        model=ep.model,
                        messages=messages,
                        max_tokens=128,
                    )
                    return time.time() - start
                except Exception:  # noqa: BLE001
                    return -1

            start = time.time()
            lats: list[float] = []
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [pool.submit(one_request, i) for i in range(rounds)]
                for fut in as_completed(futures):
                    lats.append(fut.result())
            total = time.time() - start
            valid = [x for x in lats if x > 0]
            results.append(
                {
                    "endpoint": ep.name,
                    "concurrency": concurrency,
                    "total_requests": rounds,
                    "success": len(valid),
                    "total_time": round(total, 3),
                    "qps": round(len(valid) / total, 3) if total > 0 else 0,
                    "avg_latency": round(sum(valid) / len(valid), 3) if valid else 0,
                }
            )
        return results

    @staticmethod
    def print_report(report: dict[str, Any]) -> None:
        """打印对比报告。"""
        print("\n" + "=" * 70)
        print("本地 vs API 性能对比报告")
        print("=" * 70)
        print(f"{'端点':<12}{'模型':<28}{'成功':<6}{'平均延迟':<10}{'Token':<10}{'成本$':<10}")
        print("-" * 70)
        for s in report["summary"]:
            print(
                f"{s['endpoint']:<12}{s['model']:<28}"
                f"{s['success']:<6}{s['avg_latency']:<10}"
                f"{s['avg_tokens']:<10}{s['total_cost_usd']:<10}"
            )
        print("=" * 70)


def build_default_endpoints() -> list[ModelEndpoint]:
    """构建默认对比端点：本地 Ollama + OpenAI API。"""
    api_key = os.environ.get("OPENAI_API_KEY", "sk-xxx")
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    return [
        ModelEndpoint(
            name="本地-Ollama",
            base_url=ollama_url,
            api_key="ollama",
            model="qwen2.5:7b",
            input_price=0.0,
            output_price=0.0,
            is_local=True,
        ),
        ModelEndpoint(
            name="API-GPT4o-mini",
            base_url="https://api.openai.com/v1",
            api_key=api_key,
            model="gpt-4o-mini",
            input_price=0.00015,
            output_price=0.0006,
            is_local=False,
        ),
    ]


def demo_compare() -> None:
    """演示本地 vs API 对比流程。"""
    endpoints = build_default_endpoints()
    comparator = LocalVsAPIComparator(endpoints)

    test_prompts = [
        "用一句话解释什么是 RAG。",
        "写一个 Python 函数计算斐波那契数列第 n 项。",
        "对比 TCP 和 UDP 的主要区别。",
    ]

    report = comparator.batch_test(
        prompts=test_prompts,
        system="你是一个专业的技术助手，回答简洁准确。",
        max_tokens=256,
    )
    comparator.print_report(report)

    print("\n--- 吞吐量测试 ---")
    throughput = comparator.throughput_test(
        prompt="简述什么是 Transformer 架构。",
        concurrency=4,
        rounds=12,
    )
    for t in throughput:
        print(t)


if __name__ == "__main__":
    demo_compare()
