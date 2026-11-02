# -*- coding: utf-8 -*-
"""
文件用途：Day11 - 02 缓存层
实现"检索缓存 + 生成缓存"，相同问题命中缓存避免重复调用，降低延迟和成本。

运行：python 02_cache_layer.py（无需真正调用 LLM）
"""

import time

# 模拟昂贵调用（真实中是检索+LLM）
def expensive_rag(question: str) -> str:
    time.sleep(0.3)  # 模拟耗时
    return f"关于「{question}」的回答（来自检索+生成）"


class RetrieveCache:
    def __init__(self, ttl: int = 3600):
        self.store = {}      # question -> (answer, expire_at)
        self.hits = 0
        self.misses = 0
        self.ttl = ttl

    def get_or_call(self, question: str) -> tuple[str, bool]:
        now = time.time()
        if question in self.store:
            ans, exp = self.store[question]
            if now < exp:
                self.hits += 1
                return ans, True  # cache hit
        ans = expensive_rag(question)
        self.store[question] = (ans, now + self.ttl)
        self.misses += 1
        return ans, False        # cache miss


def main() -> None:
    cache = RetrieveCache()
    q = "报销住宿上限是多少？"
    print("第一次（miss）:")
    ans, hit = cache.get_or_call(q)
    print("  ", ans, "cache=", hit)
    print("第二次（应 hit）:")
    ans, hit = cache.get_or_call(q)
    print("  ", ans, "cache=", hit)
    print("第三次（不同问题，miss）:")
    ans, hit = cache.get_or_call("年假几天？")
    print("  ", ans, "cache=", hit)
    print(f"\n统计：命中 {cache.hits} 次，未命中 {cache.misses} 次")
    print("生产用 Redis + TTL，并需在文档更新时使相关缓存失效。")


if __name__ == "__main__":
    main()