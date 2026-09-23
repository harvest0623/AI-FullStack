#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: FastAPI 封装 —— 把 GraphFlow 图暴露为 REST API(可 uvicorn 直接运行)
# 说明: 提供 POST /analyze(一次性)、POST /stream(流式)、GET /health(健康检查)、统一错误处理。
# 运行: uvicorn 03_fastapi_service:app --reload     或  python 03_fastapi_service.py
# 依赖: pip install fastapi uvicorn langgraph langchain pydantic python-dotenv

from typing import TypedDict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

load_dotenv()


# ---------------- 状态与图 ----------------
class State(TypedDict):
    input_text: str
    risk_level: str


def analyze_node(state: State) -> dict:
    """审核节点:关键词规则(可替换为 LLM)。"""
    hits = [w for w in ["稳赚", "诱导", "链接", "涨幅"] if w in state["input_text"]]
    level = "high" if len(hits) >= 2 else ("medium" if hits else "low")
    return {"risk_level": level}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("analyze", analyze_node)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", END)
    return builder.compile()


_graph = build_graph()


# ---------------- 请求模型 ----------------
class AnalyzeRequest(BaseModel):
    text: str
    thread_id: str = "default"
    user_id: str = "anonymous"


# ---------------- 应用 ----------------
app = FastAPI(title="GraphFlow API", version="1.0.0")


@app.get("/health")
def health():
    """健康检查。"""
    return {"status": "ok", "service": "graphflow"}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """一次性审核:返回完整结果。"""
    config = {"configurable": {"thread_id": req.thread_id, "user_id": req.user_id}}
    try:
        result = await _graph.ainvoke({"input_text": req.text}, config=config)
        return {"risk_level": result["risk_level"]}
    except Exception as e:  # 统一错误处理,避免 5xx 泄漏堆栈
        raise HTTPException(status_code=500, detail=f"graph execution failed: {e}")


@app.post("/stream")
async def stream(req: AnalyzeRequest):
    """流式审核:逐节点/逐 chunk 输出过程。"""
    config = {"configurable": {"thread_id": req.thread_id, "user_id": req.user_id}}

    async def event_gen():
        # 用 stream_mode="updates" 逐节点产出增量
        async for update in _graph.astream(
            {"input_text": req.text}, config=config, stream_mode="updates"
        ):
            for node_name, payload in update.items():
                yield f"node={node_name} payload={payload}\n"
        yield "done\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_gen(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("03_fastapi_service:app", host="0.0.0.0", port=8000, reload=False)