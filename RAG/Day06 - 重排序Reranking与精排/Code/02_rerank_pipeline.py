# -*- coding: utf-8 -*-
"""
文件用途：Day06 - 02 检索 + 重排 + 生成 完整管道
实现"粗召回(Top-30) → 重排精排(Top-3) → 注入生成"的 RAG 增强管道。
重排器可选：
  - Cohere Rerank（API，需 COHERE_API_KEY）
  - 本地 bge-reranker（需 pip install FlagEmbedding, 首次会自动下载模型）
  - 无可用时降级为"相似度重排"演示流程

运行：python 02_rerank_pipeline.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

KB = {
    "报销制度": "差旅报销需在出差结束后5个工作日内提交申请，附发票。",
    "差旅住宿": "住宿每天上限500元，超出部分自理；升级舱位需提前申请。",
    "年假规则": "年假每年15天，入职满1年可领取，需提前3天在HR系统提交。",
    "支付规则": "支持支付宝、微信支付、对公转账与云闪付，不支持货到付款。",
    "体检安排": "员工年度体检于每年春季统一安排，项目含血常规等。",
}

# 模拟"粗召回"：返回所有块及其简单相关分（真实中用向量库，见 Day05）
def rough_recall(query: str, top: int = 30) -> list[tuple[str, str, float]]:
    """用词重叠做粗召回，返回 [(title, text, score)]，按分降序。"""
    qwords = set(query.replace("，", " ").replace("。", " ").replace("？", " ").split())
    scored = []
    for title, text in KB.items():
        twords = set(text.replace("，", " ").replace("。", " ").split())
        scored.append((title, text, float(len(qwords & twords))))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top]


def build_reranker():
    # 1) Cohere
    if os.getenv("COHERE_API_KEY"):
        import cohere
        co = cohere.Client(os.getenv("COHERE_API_KEY"))
        return ("Cohere", lambda pid, texts, query, top: rerank_cohere(co, pid, texts, query, top))
    # 2) 本地 bge
    try:
        from FlagEmbedding import FlagReranker
        model = FlagReranker("BAAI/bge-reranker-base", use_fp16=False)
        return ("bge-reranker", lambda pid, texts, query, top: rerank_local(model, pid, texts, query, top))
    except Exception:
        # 3) 降级：按 word-overlap 重排（仅演示流程）
        return ("similarity-fallback", lambda pid, texts, query, top: rerank_fallback(pid, texts, query, top))


def rerank_cohere(co, pid, texts, query, top):
    """先按简单相关粗排，再交给 cohere 重排（此骨架保留调用结构）。"""
    resp = co.rerank(query=query, documents=list(texts), top_n=top, model="rerank-multilingual-v3.0" if False else None)
    # cohere 较新版本顶层参数为 top_n/model；此处兼容性保护
    pairs = sorted(zip(pid, texts), key=lambda p: query.count(p[1][:5]), reverse=True)
    # 真实场景用 resp.results 的 index；演示仅做顺序占位并解释
    return [p for _, p in pairs[:top]]


def rerank_local(model, pid, texts, query, top):
    pairs = [[query, t] for t in texts]
    scores = model.compute_score(pairs, normalize=True) if isinstance(pairs[0], list) else None
    # compute_score 可能返回浮点或列表
    if isinstance(scores, (int, float)):
        scores = [scores] * len(texts)
    order = sorted(range(len(texts)), key=lambda i: scores[i], reverse=True)
    return [texts[i] for i in order[:top]]


def rerank_fallback(pid, texts, query, top):
    qset = set(query)
    order = sorted(range(len(texts)), key=lambda i: sum(1 for c in qset if c in texts[i]), reverse=True)
    return [(texts[i]) for i in order[:top]]


def main() -> None:
    query = "出差住酒店每天能报销多少钱？"
    cands = rough_recall(query)
    titles = [t for t, _, _ in cands]
    texts = [t for _, t, _ in cands]

    name, rerank = build_reranker()
    print(f"粗召回 {len(cands)} 块 → 使用重排器 [{name}] 精排 Top-3\n")

    top_texts = rerank(titles, texts, query, 3)
    print("精排后的 Top-3：")
    for i, t in enumerate(top_texts, 1):
        print(f"  {i}. {t}")

    # 注入生成（无 LLM 时打印 Prompt）
    context = "\n".join(top_texts)
    print("\n=== 注入生成 Prompt ===")
    print(f"资料：\n{context}\n问题：{query}\n回答：请依据资料作答。")
    print("\n说明：此处核心是『粗召回→精排→生成』结构；重排器可按需替换为 Cohere/本地。")


if __name__ == "__main__":
    main()