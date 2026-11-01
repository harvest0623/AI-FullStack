# -*- coding: utf-8 -*-
"""
文件用途：Day07 - 04 查询路由
把用户问题分发到正确的数据源（子库），演示两类路由：
  - LLM 路由：让 LLM 选工具/库
  - 关键词路由（降级）：用关键词匹配各库描述

运行：python 04_query_router.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

# 各子库及其"描述词 / 代表关键词"
INDICES = {
    "财务库": {
        "desc": "报销、发票、预算、差旅、账务",
        "data": ["报销需5个工作日内提交，附发票", "住宿每日上限500元"],
    },
    "人事库": {
        "desc": "年假、请假、病假、绩效、体检",
        "data": ["年假每年15天，需提前提交", "病假需医院证明"],
    },
    "产品库": {
        "desc": "产品功能、文档、支付、API",
        "data": ["支持支付宝、微信、对公转账", "产品采用云原生架构"],
    },
}


def route_with_llm(query: str) -> str:
    import openai
    client = openai.OpenAI()
    options = "、".join(INDICES.keys())
    desc = "\n".join(f"{k}: {v['desc']}" for k, v in INDICES.items())
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content":
            f"给定子库：{options}\n描述：\n{desc}\n只输出最适合下面的问题的一个库名：\n{query}"}],
    )
    name = resp.choices[0].message.content.strip()
    return name if name in INDICES else next(iter(INDICES))


def route_keyword(query: str) -> str:
    """降级：按关键词命中最多的库路由。"""
    best, best_score = None, -1
    for name, info in INDICES.items():
        score = sum(1 for kw in info["desc"].split("、") if kw and kw in query)
        if score > best_score:
            best, best_score = name, score
    return best or "财务库"


def retrieve_from(query: str, index_name: str) -> str:
    qset = set(query)
    data = INDICES[index_name]["data"]
    return max(data, key=lambda t: sum(1 for c in qset if c in t))


def main() -> None:
    questions = ["差旅费怎么报销？", "年假有几天？", "你们支持哪些支付方式？"]
    print("===== 查询路由演示 =====\n")
    for q in questions:
        if os.getenv("OPENAI_API_KEY"):
            idx = route_with_llm(q)
            method = "LLM"
        else:
            idx = route_keyword(q)
            method = "关键词(降级)"
        hit = retrieve_from(q, idx)
        print(f"问题：{q}\n  路由[{method}]→ {idx}\n  命中：{hit}\n")


if __name__ == "__main__":
    main()