# -*- coding: utf-8 -*-
"""
文件用途：Day11 - 04 FastAPI 生产 RAG 服务
把 QueryEngine 封装为 REST API：健康检查、单轮问答、多轮对话、触发入库。
启动时预加载索引，请求复用；带缓存层与观测打点。

启动：uvicorn 04_fastapi_rag:app --reload --port 8000
或在脚本内直接运行 python 04_fastapi_rag.py
依赖：fastapi uvicorn pydantic langchain-community faiss-cpu（可降级）
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 简单向量库 + 降级嵌入
def hash_vec(text: str, dim: int = 16):
    return [(int(hashlib.md5(f"{text}|{i}".encode()).hexdigest()[:8], 16) % 2000)/1000.0 - 1.0 for i in range(dim)]

import hashlib


def build_index():
    try:
        from langchain_openai import OpenAIEmbeddings
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
    except Exception:
        class H:
            def embed_documents(self, texts): return [hash_vec(t) for t in texts]
            def embed_query(self, text): return hash_vec(text)
        emb = H()
    from langchain_community.vectorstores import FAISS
    docs = [
        "报销需在出差结束后5个工作日内提交申请，附有效发票。",
        "住宿每日上限500元，超出部分自理。",
        "年假每年15天，需提前3天在HR系统提交。",
        "DATA-PRO-2024 支持支付宝与云闪付支付。",
    ]
    return FAISS.from_texts(docs, emb)


index = build_index()
cache: dict[str, dict] = {}


app = FastAPI(title="DataIQ RAG Service", version="1.0.0")


class QueryReq(BaseModel):
    question: str


class ChatMsg(BaseModel):
    role: str
    content: str


class ChatReq(BaseModel):
    messages: list[ChatMsg] = []  # 多轮对话历史


@app.get("/health")
def health():
    return {"status": "ok", "index_size": 4}


@app.post("/query")
def query(req: QueryReq):
    t0 = time.time()
    q = req.question
    if q in cache:
        hit = cache[q]
        hit["cache_hit"] = True
        return {**hit, "latency_ms": round((time.time() - t0) * 1000, 1)}
    hits = index.similarity_search_with_score(q, k=2)
    docs = [(d.page_content, round(s, 3)) for d, s in hits]
    # 真实中调用 LLM 生成；此处演示检索上下文返回
    answer = docs[0][0] if docs else "知识库中暂未找到相关内容。"
    payload = {"answer": answer, "sources": docs, "cache_hit": False}
    cache[q] = payload
    return {**payload, "latency_ms": round((time.time() - t0) * 1000, 1)}


@app.post("/chat")
def chat(req: ChatReq):
    # 多轮会话示意：取最后一条内容做检索
    last = req.messages[-1].content if req.messages else "你好"
    return query(QueryReq(question=last))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("04_fastapi_rag:app", host="0.0.0.0", port=8000)