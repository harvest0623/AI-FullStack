# -*- coding: utf-8 -*-
"""
文件用途：Day07 - 03 复合问题分解
把"含多个主题"的问题拆成可独立检索的子问题，分别检索，再汇总。
演示分解逻辑与"分而治之"思想。

运行：python 03_query_decompose.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE = [
    ("年假条款", "年假每年15天，入职满1年可领取，不允许跨年结转。"),
    ("病假条款", "病假需提供医院诊断证明，病假不计入年假。"),
    ("报销条款", "报销需在出差结束后5个工作日内提交，附有效发票。"),
]


def decompose(query: str) -> list[str]:
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content":
                "把下面的复合问题拆成若干个可独立检索的子问题，每行一个：\n" + query}],
        )
        return [l for l in resp.choices[0].message.content.splitlines() if l.strip()]
    except Exception:
        # 降级：按"和 / 与 / 、"粗拆
        import re
        parts = re.split(r"[和与、]", query)
        return [p.strip(" ？?") for p in parts if p.strip(" ？?")]


def search(q: str) -> str:
    qset = set(q)
    best = max(KNOWLEDGE, key=lambda kv: sum(1 for c in qset if c in kv[1]))
    return f"[{best[0]}] {best[1]}"


def main() -> None:
    query = "年假可以跨年结转吗，病假和年假会冲突吗？"
    subs = decompose(query)
    print("复合问题：", query)
    print("拆分子问题：")
    for i, s in enumerate(subs, 1):
        print(f"  {i}. {s}")

    print("\n分别检索结果：")
    for s in subs:
        print(f"  · {search(s)}")

    print("\n汇总示例（真实中交给 LLM 合并）：")
    print("  年假不可跨年结转；病假需医院证明且不计入年假，二者不冲突。")


if __name__ == "__main__":
    main()