# -*- coding: utf-8 -*-
"""
文件用途：Day10 - 02 生成层指标判定
用规则近似判定回答的 faithfulness（忠实性）与 relevancy（相关性），
帮助理解"防幻觉"与"答非所问"的评判逻辑。

运行：python 02_generation_metrics.py（无需联网）
"""

# 每个样例: (回答, 上下文, 问题)
CASES = [
    ("报销需在5个工作日内提交，住宿每日上限500元。",
     "报销需在出差结束后5个工作日内提交，附发票。住宿每日上限500元。",
     "住宿报销上限是多少？", True),
    ("报销需在5个工作日内提交，且公司提供额外交通补贴1000元。",
     "报销需在出差结束后5个工作日内提交，附发票。",
     "住宿报销上限是多少？", True),
    ("今天天气很好，阳光明媚。",
     "报销需在出差结束后5个工作日内提交，附发票。",
     "住宿报销上限是多少？", True),
]


def faithfulness_rule(answer, context):
    """近似：判断回答中是否出现"上下文没有"的关键新增信息。简化演示。"""
    context_set = set(context.replace("，", " ").replace("。", " ").split())
    extra_markers = ["1000元", "补贴"]
    return not any(m in answer for m in extra_markers)


def relevancy_rule(answer, question):
    q_kw = {"报销", "上限", "提交", "住宿"}
    a_kw = {c for c in answer}
    return any(k in a_kw for k in q_kw)


def main() -> None:
    print("生成层指标判定（简化规则演示，真实用 LLM judge）\n")
    for ans, ctx, q, _ in CASES:
        f = faithfulness_rule(ans, ctx)
        r = relevancy_rule(ans, q)
        verdict = []
        if not f:
            verdict.append("幻觉风险(忠忠实性低)")
        if not r:
            verdict.append("答非所问(相关性低)")
        if not verdict:
            verdict.append("合格")
        print(f"Q: {q}")
        print(f"A: {ans}")
        print(f"   忠实性={'OK' if f else 'LOW'}  相关性={'OK' if r else 'LOW'}  → {', '.join(verdict)}")
        print()


if __name__ == "__main__":
    main()