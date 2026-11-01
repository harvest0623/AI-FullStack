# -*- coding: utf-8 -*-
"""
文件用途：Day07 - 02 多查询（Multi-Query）
从一个问题生成多个 PV 子查询，分别检索后合并去重，
提升召回覆盖。演示"多查询 → 合并候选"的流程。

运行：python 02_multi_query.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE = [
    ("财务", "报销需在出差结束后5个工作日内提交申请，附有效发票。"),
    ("财务", "住宿每日上限500元，超出部分自理。"),
    ("人事", "年假每年15天，需提前3天在HR系统提交申请。"),
    ("行政", "远程办公每周最多3天，需保持在线。"),
]


def gen_queries(query: str, n: int) -> list[str]:
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content":
                f"为下面的问题生成{n}个不同角度的检索子查询，每行一个，只输出子查询：\n{query}"}],
        )
        return [l.strip() for l in resp.choices[0].message.content.splitlines() if l.strip()][:n]
    except Exception:
        # 降级：围绕关键词的简单改写
        kws = ["报销", "提交", "发票", "申请"]
        return [query] + [f"{query} {k}" for k in kws[:n - 1]]


def search(q: str) -> list[str]:
    qset = set(q)
    scored = sorted(((sum(1 for c in qset if c in text), title)
                     for title, text in KNOWLEDGE), reverse=True)
    return [title for _, title in scored]


def main() -> None:
    query = "出差后怎么报销？"
    n = 3
    queries = gen_queries(query, n)
    print("生成", len(queries), "个子查询：")
    for q in queries:
        print("  ·", q)

    merged = set()
    for q in queries:
        for title in search(q):
            merged.add(title)
    print("\n合并去重后命中的知识块：", sorted(merged))
    print("\n结论：多查询从不同角度召回，合并后比单一查询覆盖更广；"
          "代价是检索次数翻倍，可在重排后取精。")


if __name__ == "__main__":
    main()