# -*- coding: utf-8 -*-
"""
文件用途：Day07 - 01 查询改写
用 LLM 把口语化问题改写成适合检索的正式查询，并对比改写前后的相关命中。
无 LLM 时用简单的"近义词规范化"降级演示。

运行：python 01_query_rewrite.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE = [
    "报销流程：员工需在出差结束后5个工作日内提交报销申请，附有效发票。",
    "住宿标准：住宿每日上限500元，超出部分自理。",
    "请假制度：年假每年15天，病假需提供医院证明。",
    "远程办公：每周最多3天在家办公，需保持上午10点到下午4点在线。",
]


def keyword_score(query: str, text: str) -> int:
    q = {c for c in query if c not in "的了吗呢？便咋报销咱们转化成我们"} 
    t = set(text)
    return len(q & t)


def rewrite_with_llm(query: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content":
                "你是信息检索查询改写器。把下面的口语化问题改写为适合在企业制度"
                "知识库中检索的正式、含关键词的查询，只输出改写结果：\n" + query}],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        # 降级：简单替换口语词
        mapping = {"咋": "怎么", "报销": "报销", "能多少天": "几天", "咱们": "员工"}
        new = query
        for k, v in mapping.items():
            new = new.replace(k, v)
        return new


def main() -> None:
    raw = "咱们出差回来，住宿一天能报多少？"
    rewritten = rewrite_with_llm(raw)
    print("原始问题：", raw)
    print("改写后  ：", rewritten)

    print("\n命中对比（用关键词重叠近似检索）：")
    r_raw = max(keyword_score(raw, t) for t in KNOWLEDGE)
    r_rew = max(keyword_score(rewritten, t) for t in KNOWLEDGE)
    print(f"  原始问题最高命中分：{r_raw}")
    print(f"  改写问题最高命中分：{r_rew}")
    print("\n结论：改写让查询更贴近文档表达，有助于提升命中与相似度。")


if __name__ == "__main__":
    main()