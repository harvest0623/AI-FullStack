"""
04_memory_score.py
记忆打分与淘汰：重要性 × 使用频率 × 时间衰减，
容量超限时淘汰总分最低的记忆，防止记忆腐化、检索噪声变大。

运行：python 04_memory_score.py
"""

import math
from dataclasses import dataclass


@dataclass
class MemoryItem:
    text: str
    importance: float      # 0-10：事实/经验高，闲聊低
    created_day: int        # 写入"天"数（演示用整数天）
    last_used_day: int     # 最近使用"天"数
    use_count: int = 0      # 被召回次数

    def score(self, today: int, lam: float = 0.1) -> float:
        """score = importance × (1 + log(1+use_count)) × e^(-λ·未使用天数)"""
        freq = 1 + math.log(1 + self.use_count)
        recency = math.exp(-lam * (today - self.last_used_day))
        return round(self.importance * freq * recency, 3)


class MemoryBank:
    """带容量上限与淘汰机制的记忆库。"""

    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.items: list[MemoryItem] = []

    def write(self, text, importance, today, **kw):
        self.items.append(MemoryItem(text, importance, today, today, **kw))
        if len(self.items) > self.capacity:
            self._evict(today)

    def recall(self, keyword, today):
        """召回时更新使用信息（召回即强化）。"""
        hits = [it for it in self.items if keyword in it.text]
        for it in hits:
            it.use_count += 1
            it.last_used_day = today
        return hits

    def _evict(self, today: int):
        scored = sorted(self.items, key=lambda it: it.score(today))
        victim = scored[0]
        self.items.remove(victim)
        print(f"    [淘汰] 容量超限，移除低分记忆：'{victim.text[:24]}…' "
              f"(score={victim.score(today)})")

    def report(self, today: int):
        print(f"  记忆库（{len(self.items)}/{self.capacity}）按分数排序：")
        for it in sorted(self.items, key=lambda x: -x.score(today)):
            print(f"    score={it.score(today):>6}  imp={it.importance}  "
                  f"used={it.use_count}  '{it.text[:26]}'")


def main():
    bank = MemoryBank(capacity=5)

    print("=" * 62)
    print("Day10：写入一批记忆")
    print("=" * 62)
    bank.write("用户称呼为张工", importance=9, today=10)
    bank.write("用户时区 Asia/Shanghai", importance=8, today=10)
    bank.write("经验：算环比要先取两期数据", importance=7, today=10)
    bank.write("用户随口说了今天天气不错", importance=2, today=10)
    bank.write("经验：品类明细要带 category 参数", importance=6, today=10)
    bank.report(10)

    print("\n" + "=" * 62)
    print("Day10-Day40：『张工』相关记忆被频繁召回（使用强化）")
    print("=" * 62)
    for day in (12, 18, 25, 33, 40):
        bank.recall("张工", day)
    print("  召回 5 次『用户称呼为张工』后，其 use_count 增长、last_used 更新")

    print("\n" + "=" * 62)
    print("Day40：再写两条新记忆（触发淘汰）")
    print("=" * 62)
    bank.write("用户新手机号 138****", importance=8, today=40)
    bank.write("昨天聊了个周末计划", importance=3, today=40)
    bank.report(40)

    print("\n要点：")
    print("  1. 打分=重要性 × 频率(log) × 时效(e^-λΔt)：常用的越用越强，久置的自然衰减")
    print("  2. 召回即强化：被用到的记忆 last_used 与 use_count 更新（类似 LRU）")
    print("  3. 淘汰低分而非最旧：闲聊且久未使用者优先出局")
    print("  4. λ 控制遗忘速度：业务变化快(如联系方式)用大 λ，长期事实用小 λ")


if __name__ == "__main__":
    main()