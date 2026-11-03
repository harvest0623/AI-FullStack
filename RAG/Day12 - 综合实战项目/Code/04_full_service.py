# -*- coding: utf-8 -*-
"""
文件用途：Day12 - 04 DataIQ 完整 FastAPI 服务
把 02(管道) + 03(引擎) 组织成多用户可调用的生产服务：
  - POST /query  单轮问答（含混合检索+重排+生成）
  - GET  /health 健康检查
启动预加载索引，含简单缓存。

启动：uvicorn 04_full_service:app --reload --port 8000
或：python 04_full_service.py
"""

import os
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel


# ---------- 数据与简单检索（整合自 02/03，无 Key 可跑） ----------
DOCS = [
    ("报销需在出差结束后5个工作日内提交申请，附有效发票。", {"dept": "财务", "doc": "报销"}),
    ("住宿每日上限500元，超出部分自理。", {"dept": "财务", "doc": "报销"}),
    ("年假每年15天，需提前3天在HR系统提交，不允许跨年结转。", {"dept": "人事", "doc": "年假"}),
    ("DATA-PRO-2024 产品支持支付宝与云闪付支付。", {"dept": "产品", "doc": "手册"}),
]


def retrieve(question: str, top: int = 2) -> list[str]:
    """简化的关键词+元数据过滤检索（真实中：混合检索+重排，见 03）。"""
    qset = set(question)
    scored = sorted(
        ((sum(c in text for c in qset), dept, text)
         for text, meta in DOCS for dept in (meta["dept"],)),
        reverse=True)
    # 去重取文档文本
    seen = set()
    out = []
    for _, dept, text in scored:
        if text not in seen:
            seen.add(text)
            out.append(text)
        if len(out) >= top:
            break
    return out


# ---------- 应用 ----------
app = FastAPI(title="DataIQ RAG", version="2.0.0")


class QueryReq(BaseModel):
    question: str
    dept: Optional[str] = "内部"   # 权限/过滤示意


@app.get("/health")
def health():
    return {"status": "ok", "index": len(DOCS)}


@app.post("/query")
def query(req: QueryReq):
    t0 = time.time()
    if req.dept not in ("财务", "人事", "产品", "内部"):
        req.dept = "内部"
    # 先按部门过滤，再检索（权限在检索层过滤）
    allowed = [t for t, m in DOCS if req.dept == "内部" or m["dept"] == req.dept]
    scored = sorted(
        ((sum(c in t for c in set(req.question)), t) for t in allowed), reverse=True)
    context = "\n".join(f"- {t}" for _, t in scored[:2])

    # 生成：有 Key 走 LLM，否则降级返回上下文
    answer = _generate(req.question, context)
    return {
        "answer": answer,
        "sources": [t for _, t in scored[:2]],
        "dept filtered": req.dept,
        "latency_ms": round((time.time() - t0) * 1000, 1),
    }


def _generate(question: str, context: str) -> str:
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "你是DataIQ知识库助手，只依据资料回答。"},
                    {"role": "user", "content": f"资料：\n{context}\n问题：{question}"},
                ])
            return resp.choices[0].message.content
        except Exception as e:
            return f"(降级生成占位: {e})"
    return f"离线演示：基于以下资料作答 →\n{context}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("04_full_service:app", host="0.0.0.0", port=8000)