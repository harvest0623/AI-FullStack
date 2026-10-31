# -*- coding: utf-8 -*-
"""
文件用途：Day02 - 02 LlamaIndex 朴素 RAG 完整实现
用 LlamaIndex 搭建等价的朴素 RAG，体会其"一站式"风格：
  SimpleDirectoryReader(load) → VectorStoreIndex(from_documents=切块+嵌入+入库)
  → as_query_engine(检索+生成) → query()

场景：DataIQ 企业知识库（与 LangChain 版同一份示例文档）。
运行：python 02_naive_rag_llama.py
依赖：llama-index llama-index-embeddings-openai llama-index-llms-openai python-dotenv
"""

import os
from dotenv import load_dotenv

load_dotenv()

DATA_MD = "dataiq.md"


def ensure_sample_doc() -> None:
    if os.path.exists(DATA_MD):
        return
    content = """# DataIQ 员工制度手册

## 报销规则
差旅报销需在出差结束后 5 个工作日内提交。住宿每天上限 500 元。

## 年假规则
DataIQ 提供每年 15 天带薪年假，入职满 1 年即可领取，不允许跨年累计。

## 支付规则
DataIQ 支持支付宝、微信支付、对公转账与云闪付支付，不支持货到付款。
"""
    with open(DATA_MD, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    ensure_sample_doc()
    print("===== 朴素 RAG（LlamaIndex） =====")

    try:
        from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
    except ImportError:
        print("请先安装：pip install llama-index")
        return

    # 全局配置（无 Key 时用 HashEmbedding 离线演示，不可用于语义检索）
    api_key = os.getenv("OPENAI_API_KEY")

    class _HashEmbedding:
        # 极简降级嵌入，仅供无 Key 时跑通流程
        def get_text_embedding(self, text):
            import hashlib
            return [int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16) for i in range(16)]
        def get_query_embedding(self, text):
            return self.get_text_embedding(text)

    if api_key:
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)
        print("[Settings] 使用 OpenAI 嵌入 + LLM")
    else:
        from llama_index.core.embeddings import BaseEmbedding

        class HashEmbedding(BaseEmbedding):
            def _get_text_embedding(self, text): return _HashEmbedding().get_text_embedding(text)
            def _get_query_embedding(self, text): return _HashEmbedding().get_query_embedding(text)

        Settings.embed_model = HashEmbedding()
        # 无 LLM 时用最简单的"读取文本"合成器；这里直接打印检索结果
        print("[Settings] 未检测到 KEY，使用降级 HashEmbedding（仅演示切块+入库+检索）")

    # Load（SimpleDirectoryReader 自动读取目录下文档）
    documents = SimpleDirectoryReader("./").load_data()
    print(f"[Load] 加载 {len(documents)} 个文档")

    # Index：from_documents 自动做"切块 + 嵌入 + 入库"
    index = VectorStoreIndex.from_documents(documents)
    print("[Index] 索引构建完成")

    if api_key:
        # Query（检索 + 生成封装）
        query_engine = index.as_query_engine(similarity_top_k=3)
        resp = query_engine.query("员工出差住宿每天最多报销多少钱？")
        print("\n[Generate] 回答：")
        print(resp)
        print("\n来源节点：")
        for nw in resp.source_nodes:
            print(f"  - {nw.node.text[:40]}... (score={nw.score:.4f})")
    else:
        # 降级：仅演示检索
        retriever = index.as_retriever(similarity_top_k=3)
        hits = retriever.retrieve("员工出差住宿每天最多报销多少钱？")
        print("\n[Retrieve]（降级，仅检索演示）")
        for nw in hits:
            print(f"  - {nw.node.text[:40]}... (score={nw.score:.4f})")


if __name__ == "__main__":
    main()