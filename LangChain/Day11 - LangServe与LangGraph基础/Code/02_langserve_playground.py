# 文件用途：LangServe Playground + 自定义端点 + 认证中间件 + CORS 配置
# 场景：ChainQA API 服务增强版
# 运行：uvicorn 02_langserve_playground:app --reload --port 8001
# 依赖：pip install langchain langchain-openai langserve fastapi uvicorn python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langserve import add_routes

load_dotenv()


# ============================================================
# 1. 创建 ChainQA 增强版 Chain
# ============================================================

def build_chainqa_chain():
    """ChainQA 问答链"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手，请用准确简洁的中文回答。"),
        ("human", "{question}"),
    ])
    return prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0) | StrOutputParser()


def build_translate_chain():
    """翻译链：中文↔英文"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是翻译助手。如果输入是中文则翻译为英文，如果是英文则翻译为中文。只输出译文。"),
        ("human", "{text}"),
    ])
    return prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0) | StrOutputParser()


# ============================================================
# 2. 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title="ChainQA API 增强版",
    description="含 Playground、自定义端点、认证、CORS 的 ChainQA 服务",
    version="2.0.0",
)


# ============================================================
# 3. CORS 配置（允许前端跨域调用）
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # React 开发服务器
        "http://localhost:5173",     # Vite 开发服务器
        "http://localhost:8080",     # Vue 开发服务器
        "*",                         # 生产环境应限制为具体域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 4. 简单认证中间件（演示用，生产用 JWT/OAuth）
# ============================================================

API_TOKEN = os.getenv("CHAINQA_API_TOKEN", "demo-token-12345")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """简单的 API Token 认证中间件

    跳过：根路径、健康检查、文档、playground
    """
    # 不需要认证的路径
    skip_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    path = request.url.path

    # playground 和 input_schema/output_schema 也放行（演示用）
    if any(path.startswith(sp) for sp in skip_paths) or "playground" in path or "schema" in path:
        return await call_next(request)

    # 检查 Authorization header
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return JSONResponse(
            status_code=401,
            content={"detail": "未授权：请提供有效的 API Token"},
        )

    return await call_next(request)


# ============================================================
# 5. 自定义数据模型
# ============================================================

class QuestionRequest(BaseModel):
    """问答请求模型"""
    question: str = Field(description="用户问题", min_length=1, max_length=1000)
    context: str = Field(default="", description="可选的上下文")


class QAResponse(BaseModel):
    """问答响应模型"""
    answer: str = Field(description="回答内容")
    latency_ms: int = Field(description="耗时（毫秒）")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    uptime: str


# ============================================================
# 6. 自定义 API 端点
# ============================================================

START_TIME = time.time()


@app.get("/", response_model=dict)
def root():
    """API 信息"""
    return {
        "service": "ChainQA API 增强版",
        "version": "2.0.0",
        "docs": "/docs",
        "playground": "/chainqa/playground",
        "auth_required": True,
        "auth_header": f"Authorization: Bearer {API_TOKEN}",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    """健康检查（无需认证）"""
    return HealthResponse(
        status="ok",
        service="ChainQA API",
        version="2.0.0",
        uptime=f"{time.time() - START_TIME:.0f}s",
    )


@app.post("/api/qa", response_model=QAResponse)
def custom_qa(req: QuestionRequest):
    """自定义问答端点（带上下文、返回耗时）

    这个端点展示如何在自定义路由中调用 Chain
    """
    start = time.time()
    chain = build_chainqa_chain()

    # 构造输入
    input_data = {"question": req.question}
    if req.context:
        # 把上下文拼到问题前
        input_data["question"] = f"上下文：{req.context}\n问题：{req.question}"

    answer = chain.invoke(input_data)
    latency = int((time.time() - start) * 1000)

    return QAResponse(answer=answer, latency_ms=latency)


@app.post("/api/translate")
def custom_translate(text: str):
    """自定义翻译端点"""
    chain = build_translate_chain()
    result = chain.invoke({"text": text})
    return {"original": text, "translated": result}


# ============================================================
# 7. 注册 LangServe 标准端点
# ============================================================

# ChainQA 标准端点（/chainqa/invoke 等）
add_routes(app, build_chainqa_chain(), path="/chainqa")

# 翻译标准端点
add_routes(app, build_translate_chain(), path="/translate")


# ============================================================
# 8. 直接运行
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Day11 - 02 LangServe Playground 与自定义端点")
    print("ChainQA API 服务增强版")
    print("=" * 60)
    print(f"\n🔐 API Token: {API_TOKEN}")
    print(f"   （请求时需带 Header: Authorization: Bearer {API_TOKEN}）")
    print("\n🚀 启动服务...")
    print("\n服务启动后可访问：")
    print("  📖 API 文档:        http://localhost:8001/docs")
    print("  🎮 ChainQA 调试:    http://localhost:8001/chainqa/playground")
    print("  🎮 翻译调试:        http://localhost:8001/translate/playground")
    print("  ❤️  健康检查:        http://localhost:8001/health")
    print("\n调用示例（需带 Token）：")
    print(f'  curl -X POST http://localhost:8001/api/qa \\')
    print(f'       -H "Authorization: Bearer {API_TOKEN}" \\')
    print(f'       -H "Content-Type: application/json" \\')
    print(f'       -d \'{{"question": "什么是 LangChain？"}}\'')
    print("=" * 60)

    uvicorn.run(
        "02_langserve_playground:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
