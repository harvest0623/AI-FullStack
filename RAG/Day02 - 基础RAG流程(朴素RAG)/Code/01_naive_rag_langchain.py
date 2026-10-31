# -*- coding: utf-8 -*-
"""
文件用途：Day02 - 01 LangChain 朴素 RAG 完整实现
演示用 LangChain 搭建一条可运行的朴素 RAG 管道：
  Load → Split → Embed → Store → Retrieve → Prompt → Generate

场景：DataIQ 企业知识库（内置示例制度文档）。
运行：python 01_naive_rag_langchain.py
依赖：langchain-core langchain-community langchain-openai faiss-cpu python-dotenv
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------- 1. 内置示例文档（无 API Key 时也可演示流程） ----------
DATA_MD = "dataiq.md"


def ensure_sample_doc() -> None:
    if os.path.exists(DATA_MD):
        return
    content = """# DataIQ 员工制度手册

## 报销规则
差旅报销需在出差结束后 5 个工作日内提交。住宿每天上限 500 元。
升级舱位需提前向直属经理邮件申请获准。

## 年假规则
DataIQ 提供每年 15 天带薪年假，入职满 1 年即可领取。
年假需提前 3 天在 HR 系统提交，不允许跨年累计。

## 支付规则
DataIQ 支持支付宝、微信支付、对公转账与云闪付支付。
不支持货到付款，大额交易需走对公转账。
"""
    with open(DATA_MD, "w", encoding="utf-8") as f:
        f.write(content)


# ---------- 2. 构建 RAG ----------
def build_components():
    from langchain_community.document_loaders import TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Load
    loader = TextLoader(DATA_MD, encoding="utf-8")
    docs = loader.load()

    # Split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200, chunk_overlap=20, separators=["\n\n", "\n", "。", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    print(f"[Split] 得到 {len(chunks)} 个块")

    # Embed + Store（无 Key 时用本地沿用 debug 的降级跳过）
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        print("[Store] 已嵌入并写入 FAISS 向量库")

        llm = None
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        except Exception as e:
            print(f"[!] LLM 初始化失败（跳过生成）: {e}")
        return vectorstore, llm
    except Exception as e:
        print(f"[!] 未检测到 OPENAI_API_KEY 或依赖缺失，仅演示链路: {e}")
        return None, None


def answer(vectorstore, llm, question: str) -> None:
    if vectorstore is None:
        print("无法检索（无 Key）。请配置 OPENAI_API_KEY 后重跑。")
        return

    # Retrieve
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    hits = retriever.invoke(question)
    print(f"\n[Retrieve] 召回 {len(hits)} 个块：")
    for h in hits:
        print(f"  score≈ 文本: {h.page_content[:40]}...")

    if llm is None:
        # 用本地规则演示"注入 Prompt 生成"
        context = "\n\n".join(h.page_content for h in hits)
        prompt = f"依据资料：\n{context}\n\n问题：{question}\n回答：请依据资料作答。"
        print("\n[Generate]（降级演示）注入 Prompt：")
        print(prompt)
        return

    # Generate（注入 Prompt 后交 LLM）
    from langchain_core.prompts import ChatPromptTemplate

    prompt_tpl = ChatPromptTemplate.from_template(
        "你是 DataIQ 知识库助手。只依据资料回答，没有的内容说不知道。"
        "资料：\n{context}\n问题：{question}"
    )
    context = "\n\n".join(h.page_content for h in hits)
    messages = prompt_tpl.format_messages(context=context, question=question)
    answer = llm.invoke(messages).content
    print("\n[Generate] 回答：")
    print(answer)


def main() -> None:
    ensure_sample_doc()
    print("===== 朴素 RAG（LangChain） =====")
    vectorstore, llm = build_components()
    answer(vectorstore, llm, "员工出差住宿每天最多报销多少钱？")


if __name__ == "__main__":
    main()