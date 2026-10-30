# -*- coding: utf-8 -*-
"""
Day11 - 04 成本优化：缓存 / 模型分级 / 上下文压缩

演示内容：
1. 精确缓存：完全相同的输入直接复用结果
2. 语义缓存：语义相同的不同表述也可命中（基于关键词/向量相似度模拟）
3. 模型分级路由：简单任务走小模型、复杂任务走旗舰模型，成本对比
4. 上下文压缩：长对话历史压缩为摘要，Token 从线性膨胀变为近似恒定

离线可运行。
"""

import hashlib
import re
from dataclasses import dataclass, field


# ============================================================
# 第一部分：缓存层（精确 + 语义）
# ============================================================

@dataclass
class CacheEntry:
    query: str
    answer: str
    embedding: set   # 简化：用关键词集合模拟向量


def simple_embed(text: str) -> set:
    """模拟向量化：分词取关键词（生产中用 Embedding 模型）"""
    return set(re.findall(r"[\w\u4e00-\u9fa5]+", text.lower()))


def similarity(a: set, b: set) -> float:
    """Jaccard 相似度模拟向量余弦相似度"""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class SemanticCache:
    """
    语义缓存：
    - 先查精确匹配
    - 再查语义相似度 >= 阈值的条目
    - 都未命中才调用 LLM（模拟），并把结果写回缓存
    """

    def __init__(self, threshold: float = 0.7):
        self.entries: list[CacheEntry] = []
        self.threshold = threshold
        self.stats = {"hit_exact": 0, "hit_semantic": 0, "miss": 0}

    def _llm_call(self, query: str) -> str:
        """模拟昂贵的 LLM 调用"""
        return f"[LLM生成] 关于「{query}」的完整回答"

    def get(self, query: str) -> tuple:
        """返回 (回答, 命中类型)"""
        # 1) 精确匹配
        for e in self.entries:
            if e.query == query:
                self.stats["hit_exact"] += 1
                return e.answer, "精确命中"

        # 2) 语义匹配
        q_emb = simple_embed(query)
        best, best_sim = None, 0.0
        for e in self.entries:
            sim = similarity(q_emb, e.embedding)
            if sim > best_sim:
                best, best_sim = e, sim

        if best and best_sim >= self.threshold:
            self.stats["hit_semantic"] += 1
            return best.answer, f"语义命中（相似度 {best_sim:.2f}，复用「{best.query}」的回答）"

        # 3) 未命中：调用 LLM 并写回缓存
        self.stats["miss"] += 1
        answer = self._llm_call(query)
        self.entries.append(CacheEntry(query, answer, q_emb))
        return answer, "未命中（缓存穿透，调 LLM 后写回）"


# ============================================================
# 第二部分：模型分级路由
# ============================================================

MODEL_PRICES = {  # 元 / 千 token
    "small":  0.001,
    "medium": 0.010,
    "large":  0.030,
}


@dataclass
class RouteRule:
    pattern: str
    model: str


ROUTE_RULES = [
    RouteRule(r"(翻译|格式|转换|大小写)", "small"),      # 机械任务 -> 小模型
    RouteRule(r"(总结|摘要|分类|打标签)", "medium"),       # 常规任务 -> 中档
    RouteRule(r"(分析|推理|规划|代码|为什么)", "large"),   # 复杂任务 -> 旗舰
]


class ModelRouter:
    """按任务类型路由到不同档位的模型"""

    def route(self, query: str) -> tuple:
        for rule in ROUTE_RULES:
            if re.search(rule.pattern, query):
                return rule.model, rule.pattern
        return "medium", "默认规则"

    def estimate_cost(self, query: str, tokens: int = 2000) -> float:
        model, _ = self.route(query)
        return MODEL_PRICES[model] * tokens / 1000 * 1000  # 每千token价格


def compare_routing_vs_always_large(queries: list[str]):
    """分级路由 vs 全部用旗舰模型的成本对比"""
    total_routed = sum(MODEL_PRICES[ModelRouter().route(q)[0]] for q in queries)
    total_large = len(queries) * MODEL_PRICES["large"]
    saving = (1 - total_routed / total_large) * 100
    return total_routed, total_large, saving


# ============================================================
# 第三部分：上下文压缩
# ============================================================

class ContextCompressor:
    """
    长对话的上下文管理：
    - 最近 K 轮保留原文
    - 更早的压缩成一句摘要
    """

    def __init__(self, keep_recent: int = 2):
        self.keep_recent = keep_recent
        self.history: list[tuple[str, str]] = []  # (role, content)

    def add(self, role: str, content: str):
        self.history.append((role, content))

    def render(self) -> str:
        if len(self.history) <= self.keep_recent:
            return "\n".join(f"{r}: {c}" for r, c in self.history)

        old = self.history[:-self.keep_recent]
        recent = self.history[-self.keep_recent:]

        # 模拟摘要压缩：多轮压成一句
        summary = (
            f"[早期对话摘要] 用户咨询了 {len([1 for r, _ in old if r == 'user'])} 个问题，"
            f"涵盖：{'、'.join(c[:12] for _, c in old[:3])}...，已解决。"
        )
        recent_text = "\n".join(f"{r}: {c}" for r, c in recent)
        return summary + "\n" + recent_text

    def token_count_naive(self, text: str) -> int:
        return len(text) * 2  # 粗略：中文 1 字约 2 token


# ============================================================
# 演示
# ============================================================

def main():
    print("=" * 56)
    print("1. 语义缓存：命中率与成本节省")
    print("=" * 56)
    cache = SemanticCache(threshold=0.6)
    queries = [
        "今天北京的天气怎么样",      # miss，写回
        "今天北京的天气怎么样",      # 精确命中
        "北京今日天气如何",          # 语义命中
        "上海有什么好吃的推荐",      # miss
        "帮我写一首关于秋天的诗",    # miss
    ]
    for q in queries:
        answer, hit = cache.get(q)
        print(f"  「{q}」 -> {hit}")
        print(f"    {answer[:40]}")

    s = cache.stats
    total = sum(s.values())
    print(f"\n  统计：精确命中 {s['hit_exact']} | 语义命中 {s['hit_semantic']} | 未命中 {s['miss']}")
    print(f"  缓存命中率 {(s['hit_exact'] + s['hit_semantic']) / total:.0%}，命中的请求 LLM 成本为 0")

    print()
    print("=" * 56)
    print("2. 模型分级路由：成本对比")
    print("=" * 56)
    router = ModelRouter()
    tasks = [
        "把这段英文翻译成中文",
        "总结一下这篇文章的要点",
        "分析一下销售下滑的根本原因并给出改进规划",
        "帮我写一个排序算法的 Python 代码",
        "这篇文章分到哪个类别",
    ]
    for t in tasks:
        model, rule = router.route(t)
        print(f"  「{t[:18]}」-> {model:<7}（规则：{rule}）")

    routed, large, saving = compare_routing_vs_always_large(tasks)
    print(f"\n  全部用旗舰模型成本：{large:.3f} 元/千token单位")
    print(f"  分级路由后成本    ：{routed:.3f} 元/千token单位")
    print(f"  节省：{saving:.0f}%")

    print()
    print("=" * 56)
    print("3. 上下文压缩：Token 从线性膨胀变为近似恒定")
    print("=" * 56)
    comp = ContextCompressor(keep_recent=2)
    # 模拟 10 轮对话
    for i in range(1, 11):
        comp.add("user", f"第 {i} 个问题：关于产品功能 {i} 的详细咨询，这是一个比较长的问题描述。")
        comp.add("assistant", f"关于功能 {i} 的回答要点：第一、第二、第三点详细说明。")

    full_history = "\n".join(f"{r}: {c}" for r, c in comp.history)
    compressed = comp.render()

    print("--- 压缩后发给模型的上下文 ---")
    print(compressed[:300] + "...")
    print(f"\n  不压缩 Token：{comp.token_count_naive(full_history)}")
    print(f"  压缩后 Token：{comp.token_count_naive(compressed)}")
    print(f"  压缩率 {(1 - comp.token_count_naive(compressed) / comp.token_count_naive(full_history)):.0%}"
          f"（对话越长收益越大）")

    print()
    print("=" * 56)
    print("成本优化三板斧总结")
    print("=" * 56)
    print("  1. 语义缓存：相似问题零成本复用（注意阈值防误命中）")
    print("  2. 模型分级：小模型干小活，旗舰模型留给硬骨头")
    print("  3. 上下文压缩：老对话变摘要，Token 不随轮数线性膨胀")


if __name__ == "__main__":
    main()
