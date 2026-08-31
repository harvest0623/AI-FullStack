# 文件用途：缓存与重试机制
# set_llm_cache 设置 LLM 缓存 / InMemoryCache / SQLiteCache
# .with_retry() 重试配置 / .with_fallbacks() 模型回退
# 展示缓存命中率和重试效果。CacheRetryManager 类
# 运行：python 02_caching_retry.py
# 依赖：pip install langchain langchain-openai python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from langchain_community.cache import SQLiteCache
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# CacheRetryManager：缓存与重试管理器
# ============================================================

class CacheRetryManager:
    """管理 LLM 缓存、重试、回退的管理器

    功能：
    - 设置 LLM 缓存（内存 / SQLite）
    - 配置重试（指数退避）
    - 配置模型回退（主模型故障→备用模型）
    - 测量缓存命中率和重试效果
    """

    def __init__(self, cache_type: str = "memory") -> None:
        self.cache_type = cache_type
        self.cache_hits = 0
        self.cache_misses = 0
        self.retry_attempts = 0
        self.fallback_used = 0
        self._setup_cache()

    def _setup_cache(self) -> None:
        """初始化缓存"""
        if self.cache_type == "sqlite":
            cache_path = "chainqa_cache.db"
            # 删除旧缓存以便演示
            if os.path.exists(cache_path):
                os.remove(cache_path)
            set_llm_cache(SQLiteCache(database_path=cache_path))
            print(f"✅ 已启用 SQLite 缓存（{cache_path}）")
        else:
            set_llm_cache(InMemoryCache())
            print("✅ 已启用内存缓存（InMemoryCache）")

    # ── 模型创建（含重试和回退） ──

    def create_robust_model(
        self,
        primary_model: str = "gpt-4o-mini",
        fallback_model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
    ) -> Any:
        """创建带重试和回退的健壮模型

        层级：primary → (失败重试3次) → fallback → (失败重试3次)
        """
        primary = ChatOpenAI(model=primary_model, temperature=0, timeout=30)
        fallback = ChatOpenAI(model=fallback_model, temperature=0, timeout=30)

        # 主模型 + 重试
        primary_with_retry = primary.with_retry(
            stop_after_attempt=max_retries,
        )
        # 备用模型 + 重试
        fallback_with_retry = fallback.with_retry(
            stop_after_attempt=max_retries,
        )
        # 主模型（含重试） + 回退到备用模型（含重试）
        return primary_with_retry.with_fallbacks([fallback_with_retry])

    # ── 缓存效果测量 ──

    def measure_cache_effect(self, model: Any, question: str, label: str = "") -> dict:
        """测量单次调用的缓存效果"""
        prompt = ChatPromptTemplate.from_messages([
            ("human", "{question}"),
        ])
        chain = prompt | model | StrOutputParser()

        start = time.time()
        result = chain.invoke({"question": question})
        elapsed = time.time() - start

        # 判断是否缓存命中（缓存命中通常耗时极短）
        is_hit = elapsed < 0.1  # 简单启发：小于 100ms 视为命中
        if is_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        return {
            "label": label,
            "question": question[:50],
            "answer": result[:50],
            "latency_ms": int(elapsed * 1000),
            "cache_hit": is_hit,
        }

    # ── 指标报告 ──

    def get_report(self) -> dict:
        """生成缓存与重试指标报告"""
        total = self.cache_hits + self.cache_misses
        return {
            "cache_type": self.cache_type,
            "total_calls": total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{(self.cache_hits / total * 100):.1f}%" if total else "0%",
            "retry_attempts": self.retry_attempts,
            "fallback_used": self.fallback_used,
        }


# ============================================================
# 演示1：缓存效果演示
# ============================================================

def demo_cache_effect() -> None:
    """演示缓存命中效果"""
    print("\n" + "=" * 60)
    print("演示1：LLM 缓存效果")
    print("=" * 60)

    manager = CacheRetryManager(cache_type="memory")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    questions = [
        "什么是 LangChain？",
        "什么是 LangChain？",      # 重复问题，应命中缓存
        "什么是 LangChain？",      # 再次重复
        "LCEL 是什么？",
        "什么是 LangChain？",      # 又重复
    ]

    print("\n依次调用（注意重复问题的耗时）：")
    results = []
    for i, q in enumerate(questions, 1):
        r = manager.measure_cache_effect(model, q, label=f"调用{i}")
        results.append(r)
        hit_tag = "🎯 缓存命中" if r["cache_hit"] else "🌐 调用 LLM"
        print(f"  [{i}] {hit_tag} | {r['latency_ms']}ms | {q}")
        print(f"      回答: {r['answer']}...")

    print(f"\n📊 缓存报告：{manager.get_report()}")


# ============================================================
# 演示2：重试机制演示
# ============================================================

def demo_retry_mechanism() -> None:
    """演示重试机制"""
    print("\n\n" + "=" * 60)
    print("演示2：重试机制（.with_retry）")
    print("=" * 60)

    # 创建带重试的模型
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=30)
    retry_model = model.with_retry(stop_after_attempt=3)

    print("\n使用带重试的模型调用：")
    prompt = ChatPromptTemplate.from_messages([("human", "{question}")])
    chain = prompt | retry_model | StrOutputParser()

    try:
        start = time.time()
        result = chain.invoke({"question": "用一句话解释什么是重试机制"})
        elapsed = time.time() - start
        print(f"  ✅ 调用成功 | 耗时 {elapsed:.2f}s")
        print(f"  回答: {result[:100]}...")
    except Exception as e:
        print(f"  ❌ 调用失败（已重试 3 次）：{type(e).__name__}: {e}")


# ============================================================
# 演示3：模型回退演示
# ============================================================

def demo_fallback_mechanism() -> None:
    """演示模型回退机制"""
    print("\n\n" + "=" * 60)
    print("演示3：模型回退（.with_fallbacks）")
    print("=" * 60)

    # 主模型故意用一个不存在的模型名，触发回退
    try:
        primary = ChatOpenAI(model="nonexistent-model-xxx", temperature=0, timeout=10)
        fallback = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=30)

        # 主模型失败 → 自动切到备用模型
        model_with_fallback = primary.with_fallbacks([fallback])

        prompt = ChatPromptTemplate.from_messages([("human", "{question}")])
        chain = prompt | model_with_fallback | StrOutputParser()

        print("\n主模型故意配错（nonexistent-model-xxx），应自动回退到 gpt-4o-mini：")
        result = chain.invoke({"question": "用一句话说明模型回退的作用"})
        print(f"  ✅ 回退成功 | 回答: {result[:100]}...")
    except Exception as e:
        print(f"  ⚠️  回退演示需 API 可用：{type(e).__name__}: {e}")


# ============================================================
# 演示4：SQLite 持久化缓存
# ============================================================

def demo_sqlite_cache() -> None:
    """演示 SQLite 持久化缓存"""
    print("\n\n" + "=" * 60)
    print("演示4：SQLite 持久化缓存")
    print("=" * 60)

    manager = CacheRetryManager(cache_type="sqlite")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    question = "解释什么是语义缓存？"
    print(f"\n第一次调用（写入缓存）：")
    r1 = manager.measure_cache_effect(model, question, "首次")
    print(f"  耗时 {r1['latency_ms']}ms | 命中: {r1['cache_hit']}")

    print(f"\n第二次调用相同问题（应命中 SQLite 缓存）：")
    r2 = manager.measure_cache_effect(model, question, "二次")
    print(f"  耗时 {r2['latency_ms']}ms | 命中: {r2['cache_hit']}")

    print(f"\n📊 报告：{manager.get_report()}")
    print("💡 SQLite 缓存会在程序重启后保留（持久化）")


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day12 - 02 缓存与重试机制演示")
    print("CacheRetryManager")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    # 演示1：缓存效果
    demo_cache_effect()

    # 演示2：重试机制
    demo_retry_mechanism()

    # 演示3：模型回退
    demo_fallback_mechanism()

    # 演示4：SQLite 缓存
    demo_sqlite_cache()

    print("\n\n" + "=" * 60)
    print("✅ 缓存与重试机制演示完成")
    print("要点：")
    print("  1. set_llm_cache 开启缓存，相同输入直接返回缓存结果")
    print("  2. InMemoryCache 内存缓存（快但重启丢失），SQLiteCache 持久化")
    print("  3. .with_retry() 配置重试（指数退避），应对临时故障")
    print("  4. .with_fallbacks() 配置回退，主模型故障自动切备用")
    print("  5. 生产环境三者组合使用：缓存降本 + 重试容错 + 回退保障")
    print("=" * 60)


if __name__ == "__main__":
    main()
