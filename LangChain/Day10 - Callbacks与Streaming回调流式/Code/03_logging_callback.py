# 文件用途：日志与指标采集（MetricsCallbackHandler）
# 采集延迟(P50/P95) / Token 消耗 / 成本估算 / 错误率，生成指标报告
# 日志持久化到文件。场景：ChainQA 生产监控数据采集
# 运行：python 03_logging_callback.py
# 依赖：pip install langchain langchain-openai python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import json
import os
import statistics
import time
from datetime import datetime
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# MetricsCallbackHandler：生产级指标采集
# ============================================================

class MetricsCallbackHandler(BaseCallbackHandler):
    """采集 Chain 执行指标的回调处理器。

    采集指标：
    - 延迟：单次调用耗时、P50、P95
    - Token 消耗：输入/输出 Token 数
    - 成本估算：按模型价格计算
    - 错误率：成功/失败次数
    """

    # 简化的模型定价（USD / 1K tokens），仅作演示
    PRICING = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, model_name: str = "gpt-4o-mini", log_file: str = "chainqa_metrics.log") -> None:
        self.model_name = model_name
        self.log_file = log_file
        # 指标存储
        self._latencies: list[float] = []          # 每次调用耗时
        self._token_counts: list[int] = []         # 每次调用 Token 数
        self._costs: list[float] = []              # 每次调用成本
        self._success_count: int = 0
        self._error_count: int = 0
        # 临时状态
        self._start_times: dict[UUID, float] = {}
        self._current_tokens: dict[UUID, int] = {}

    def _log(self, event: str, data: dict) -> None:
        """写入日志文件（JSON Lines 格式，便于后续分析）"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── LLM 指标 ──
    def on_llm_start(self, serialized, prompts, *, run_id: UUID, **kwargs) -> None:
        self._start_times[run_id] = time.time()
        self._current_tokens[run_id] = 0
        self._log("llm_start", {"run_id": str(run_id), "model": self.model_name})

    def on_chat_model_start(self, serialized, messages, *, run_id: UUID, **kwargs) -> None:
        self._start_times[run_id] = time.time()
        self._current_tokens[run_id] = 0
        self._log("chat_model_start", {"run_id": str(run_id), "model": self.model_name})

    def on_llm_new_token(self, token: str, *, run_id: UUID, **kwargs) -> None:
        self._current_tokens[run_id] = self._current_tokens.get(run_id, 0) + 1

    def on_llm_end(self, response, *, run_id: UUID, **kwargs) -> None:
        elapsed = time.time() - self._start_times.get(run_id, time.time())
        tokens = self._current_tokens.get(run_id, 0)

        self._latencies.append(elapsed)
        self._token_counts.append(tokens)

        # 成本估算（按输出 Token 计算，简化处理）
        price = self.PRICING.get(self.model_name, {"input": 0, "output": 0})
        cost = (tokens / 1000) * price["output"]
        self._costs.append(cost)

        self._log("llm_end", {
            "run_id": str(run_id),
            "latency_sec": round(elapsed, 4),
            "tokens": tokens,
            "cost_usd": round(cost, 6),
        })

    # ── 错误 ──
    def on_error(self, error: BaseException, *, run_id: UUID, **kwargs) -> None:
        self._error_count += 1
        self._log("error", {
            "run_id": str(run_id),
            "error_type": type(error).__name__,
            "error_msg": str(error)[:200],
        })

    # ── Chain 结束时计数成功 ──
    def on_chain_end(self, outputs, *, run_id: UUID, **kwargs) -> None:
        # 只有顶层 chain 结束才计为一次成功调用
        if run_id in self._start_times:
            self._success_count += 1

    # ── 指标报告 ──
    def get_metrics_report(self) -> dict:
        """生成指标报告"""
        total_calls = self._success_count + self._error_count
        return {
            "model": self.model_name,
            "total_calls": total_calls,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "error_rate": (self._error_count / total_calls * 100) if total_calls else 0,
            "latency": {
                "avg": round(statistics.mean(self._latencies), 4) if self._latencies else 0,
                "p50": round(statistics.median(self._latencies), 4) if self._latencies else 0,
                "p95": round(self._percentile(self._latencies, 95), 4) if self._latencies else 0,
                "min": round(min(self._latencies), 4) if self._latencies else 0,
                "max": round(max(self._latencies), 4) if self._latencies else 0,
            },
            "tokens": {
                "total": sum(self._token_counts),
                "avg_per_call": round(statistics.mean(self._token_counts), 1) if self._token_counts else 0,
                "max": max(self._token_counts) if self._token_counts else 0,
            },
            "cost_usd": {
                "total": round(sum(self._costs), 6),
                "avg_per_call": round(statistics.mean(self._costs), 6) if self._costs else 0,
            },
        }

    @staticmethod
    def _percentile(data: list[float], p: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (p / 100)
        f = int(k)
        c = min(f + 1, len(sorted_data) - 1)
        if f == c:
            return sorted_data[f]
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def print_report(self) -> None:
        """打印指标报告"""
        report = self.get_metrics_report()
        print("\n" + "=" * 60)
        print("📊 ChainQA 生产监控指标报告")
        print("=" * 60)
        print(f"模型: {report['model']}")
        print(f"调用次数: {report['total_calls']} (成功 {report['success_count']}, 失败 {report['error_count']})")
        print(f"错误率: {report['error_rate']:.2f}%")
        print(f"\n延迟 (秒):")
        print(f"  平均: {report['latency']['avg']} | P50: {report['latency']['p50']} | P95: {report['latency']['p95']}")
        print(f"  最小: {report['latency']['min']} | 最大: {report['latency']['max']}")
        print(f"\nToken 消耗:")
        print(f"  总计: {report['tokens']['total']} | 平均/次: {report['tokens']['avg_per_call']} | 最大: {report['tokens']['max']}")
        print(f"\n成本 (USD):")
        print(f"  总计: ${report['cost_usd']['total']} | 平均/次: ${report['cost_usd']['avg_per_call']}")
        print("=" * 60)


# ============================================================
# 构建 ChainQA 链
# ============================================================

def build_chainqa_chain():
    """构建 ChainQA 问答链"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手，请简洁回答。"),
        ("human", "{question}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    parser = StrOutputParser()
    return prompt | model | parser


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day10 - 03 日志与指标采集演示")
    print("场景：ChainQA 生产监控数据采集")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    # 清空旧日志
    log_file = "chainqa_metrics.log"
    if os.path.exists(log_file):
        os.remove(log_file)

    # 创建指标采集 Handler
    metrics_handler = MetricsCallbackHandler(model_name="gpt-4o-mini", log_file=log_file)

    # 构建链并绑定 Handler
    chain = build_chainqa_chain().with_config(callbacks=[metrics_handler])

    # 模拟多次调用（采集统计样本）
    questions = [
        "什么是 LangChain？",
        "LCEL 是什么？",
        "解释 Tool Calling 的流程",
        "Memory 有哪些类型？",
        "什么是 Retriever？",
    ]

    print(f"\n模拟 {len(questions)} 次问答调用，采集指标...\n")
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] 问题：{q}")
        try:
            result = chain.invoke({"question": q})
            print(f"    回答（前 50 字）：{result[:50]}...\n")
        except Exception as e:
            print(f"    ❌ 调用失败：{e}\n")

    # 打印指标报告
    metrics_handler.print_report()

    # 展示日志文件内容
    print(f"\n📁 日志文件 {log_file} 内容（前 3 行）：")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f.readlines()[:3], 1):
                print(f"  {line.strip()}")

    print("\n" + "=" * 60)
    print("✅ 指标采集演示完成")
    print("要点：")
    print("  1. MetricsCallbackHandler 采集延迟/Token/成本/错误率")
    print("  2. P50/P95 百分位数反映延迟分布（优于平均值）")
    print("  3. 日志用 JSON Lines 格式，便于后续 ELK/Grafana 分析")
    print("  4. 生产环境可结合 LangSmith 做更完整的追踪")
    print("=" * 60)


if __name__ == "__main__":
    main()
