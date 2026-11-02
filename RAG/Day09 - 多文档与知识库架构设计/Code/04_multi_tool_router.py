# -*- coding: utf-8 -*-
"""
文件用途：Day09 - 04 多工具/多库 Router 调度
实现一个 Router，把问题调度到对应子库工具，作为多文档 + 工具编排的入口。

运行：python 04_multi_tool_router.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

TOOLS = {
    "财务检索": ("报销、发票、预算、差旅、住宿", ["报销需5个工作日内提交发票", "住宿每日上限500元"]),
    "人事检索": ("年假、请假、病假、绩效、体检", ["年假每年15天", "病假需医院证明"]),
    "产品检索": ("产品、手册、API、支付", ["DATA-PRO-2024 支持云闪付", "产品云原生架构"]),
    "通用问答": ("闲聊、综合、其他", ["员工可以咨询各类制度问题"]),
}


def route(query: str) -> str:
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai
            client = openai.OpenAI()
            desc = "\n".join(f"{k}: {v[0]}" for k, v in TOOLS.items())
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content":
                    f"工具箱：\n{desc}\n只输出最适合下面问题的一个工具名：\n{query}"}],
                temperature=0,
            )
            name = resp.choices[0].message.content.strip()
            return name if name in TOOLS else "通用问答"
        except Exception:
            pass
    # 关键词路由（降级）
    best, best_score = "通用问答", -1
    for name, (desc, _) in TOOLS.items():
        score = sum(1 for kw in desc.split("、") if kw and kw in query)
        if score > best_score:
            best, best_score = name, score
    return best


def call_tool(tool: str, query: str) -> str:
    _, data = TOOLS[tool]
    qset = set(query)
    return max(data, key=lambda t: sum(1 for c in qset if c in t))


def main() -> None:
    for q in ["住宿报销怎么处理？", "怎么请年假？", "产品支持哪些支付？", "你最近怎么样？"]:
        tool = route(q)
        result = call_tool(tool, q) if tool != "通用问答" else "（通用对话：不检索知识库）"
        print(f"Q: {q}\n  → 路由到『{tool}』 命中：{result}\n")


if __name__ == "__main__":
    main()