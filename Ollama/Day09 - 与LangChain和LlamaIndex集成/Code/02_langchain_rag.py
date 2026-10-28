# -*- coding: utf-8 -*-
"""
Day09 - 02 LangChain 本地 RAG

模板：用 Ollama 当 Embedding + LLM，配内存向量存储做一个最小 RAG。
需要 `pip install langchain-ollama langchain-community`（Chroma 可选）。
未安装或未检测到 Ollama 时，打印指引并给出结构说明。

运行：
python 02_langchain_rag.py
"""


def template() -> str:
    return r'''
# ---- 真实接入模板（本机装好依赖 + Ollama 后解开）----
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

# 1) 底座：Ollama 同时提供 LLM 与 Embedding
llm = ChatOllama(model="llama3.1")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2) 文档 -> 切块
text = "我们的退货政策：签收7天内可无理由退货，退款3-5个工作日原路退回。"
docs = [text]
splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
chunks = splitter.split_text(text)

# 3) 嵌入入库（这里存入内存向量库）
store = Chroma.from_texts(chunks, embeddings)

# 4) 检索 + 问答
retriever = store.as_retriever(search_kwargs={"k": 2})
question = "我退货多久能收到退款？"
context = "\n".join(d.page_content for d in retriever.invoke(question))

prompt = ChatPromptTemplate.from_messages([
    ("system", "仅依据以下内容回答：\n{context}"),
    ("user", "{question}"),
])
chain = prompt | llm
print(chain.invoke({"context": context, "question": question}).content)
'''


def main():
    print(">> LangChain 本地 RAG（模板）\n")
    print("依赖：pip install langchain-ollama  (Chroma 需 langchain-community)")
    try:
        import langchain_ollama  # noqa
        from langchain_ollama import ChatOllama, OllamaEmbeddings
        print("  已安装 langchain-ollama ✓")
        from ollama_util import is_ollama_available
        if is_ollama_available("llama3.1"):
            print("  检测到 Ollama + llama3.1 ✓，可直接运行上面模板")
        else:
            print("  未检测到 Ollama 模型，先 ollama pull llama3.1 nomic-embed-text")
    except ImportError:
        print("  未安装 langchain-ollama，当前打印结构说明。")
    print("\n最小 RAG 步骤：切块 → OllamaEmbeddings 入库 → 检索 → ChatOllama 生成")
    print(template())


if __name__ == "__main__":
    main()