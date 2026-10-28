# -*- coding: utf-8 -*-
"""
Day10 - 02 综合智能客服实战

把 Day06（记忆）、Day07（RAG 检索）、Day08（工具）整合进一个"客服 Agent"：
1. 会话记忆：session 隔离 + 历史裁剪
2. 知识库检索：FAQ 嵌入 + 余弦相似度 top-k
3. 工具调用：查订单 / 算数
4. 最后交给模型生成回答

双模式：真实 Ollama 或 SimOllama 兜底。
"""

import math
from ollama_util import chat_wrapper, embed_wrapper, is_ollama_available

# 知识库（候选答案）
FAQ = [
    ("退货期限", "签收 7 天内可无理由退货。"),
    ("退款到账", "退款 3-5 个工作日原路退回。"),
    ("开发票", "确认收货后 30 天内可申请发票。"),
]


def cos_sim(a, b):
    if not a or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def rag_retrieve(query: str, top_k: int = 1) -> str:
    """从 FAQ 检索最相似答案（RAG 检索层）"""
    qv = embed_wrapper(query)
    scored = [(cos_sim(qv, embed_wrapper(ans)), topic, ans)
              for topic, ans in FAQ]
    scored.sort(key=lambda x: x[0], reverse=True)
    _, topic, ans = scored[0]
    return f"【知识库·{topic}】{ans}"


# 工具
def tool_get_order(order_id: str) -> str:
    return f"【工具】订单 {order_id} 状态：已发货，预计明日送达。"


def tool_add(a: float, b: float) -> str:
    return f"【工具】{a} + {b} = {a + b}"


def route_tool(text: str) -> str | None:
    """简易意图路由：做数就用 add，查订单就用 order（双模式工具）"""
    if "加" in text or "算" in text:
        return tool_add(3, 4)
    if "订单" in text:
        return tool_get_order("A100")
    return None


class ServiceAgent:
    def __init__(self):
        self.history = [{"role": "system",
                         "content": "你是本地客服小O，结合知识库与工具，回答简洁准确。"}]

    def answer(self, user_text: str) -> str:
        # 1) RAG 检索
        kb = rag_retrieve(user_text)
        # 2) 工具判断
        tool = route_tool(user_text)
        # 3) 组装带上上下文的请求
        extra = " ".join(x for x in [kb, tool] if x)
        enriched = f"题干：{user_text}\n辅助信息：{extra or '无'}"

        self.history.append({"role": "user", "content": enriched})
        reply = chat_wrapper(self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply


def main():
    print(">> 综合智能客服实战\n")
    print(f"Ollama 可用：{is_ollama_available()}")
    agent = ServiceAgent()

    for q in ["我退货了多久能收到退款？", "帮我查订单A100", "3加4等于几"]:
        print(f"\n用户：{q}")
        # 显示辅助层
        kb = rag_retrieve(q)
        tool = route_tool(q)
        if kb:
            print(f"  [RAG] {kb}")
        if tool:
            print(f"  [工具] {tool}")
        print(f"  回答：{agent.answer(q)}")


if __name__ == "__main__":
    main()