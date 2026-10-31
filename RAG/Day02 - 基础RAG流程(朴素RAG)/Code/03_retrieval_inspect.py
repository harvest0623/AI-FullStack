# -*- coding: utf-8 -*-
"""
文件用途：Day02 - 03 查看检索结果（TopK 与来源）
独立演示"检索返回什么"，不涉及生成，帮助理解 Top-K 与相似度得分。
可调整 k 对比召回内容差异。

运行：python 03_retrieval_inspect.py
依赖：langchain-core langchain-community langchain-openai faiss-cpu
"""

import os
from dotenv import load_dotenv

load_dotenv()

DOCS = [
    "远程办公制度：员工每周最多可以在家办公三天，需保证上午10点到下午4点在线。",
    "报销规则：差旅报销需在出差结束后5个工作日内提交，住宿每天上限500元。",
    "年假规则：DataIQ提供每年15天带薪年假，入职满1年即可领取。",
    "支付规则：支持支付宝、微信支付、对公转账与云闪付，不支持货到付款。",
    "公积金政策：员工参与年度体检计划，每年春季由公司统一组织团体体检。",
    "网络安全：所有员工需每季度完成安全培训，强密码策略已强制启用。",
]


def main() -> None:
    question = "员工出差住宿报销标准是多少？"
    k = int(os.getenv("TOP_K", "3"))

    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
    except ImportError:
        print("请安装 langchain-openai langchain-community faiss-cpu 与配置 OPENAI_API_KEY")
        return

    print(f"问题：{question}\n知识库共 {len(DOCS)} 块，查询 Top-{k}\n")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # 直接把文本列表向量化并检索（从一个空的 FAISS 建索引）
    vectorstore = FAISS.from_texts(DOCS, embeddings)
    hits = vectorstore.similarity_search_with_score(question, k=k)

    print("=" * 60)
    print("检索结果（按相关性排序）：")
    for i, (doc, score) in enumerate(hits, 1):
        # FAISS 返回的 score 越小表示越相关（L2 距离），这里换算成展示用相似度
        print(f"\n#{i}  距离={score:.4f}")
        print(f"    文本: {doc.page_content}")
    print("=" * 60)
    print("说明：距离越小越相关；分数会随 k、文档内容变化。")


if __name__ == "__main__":
    main()