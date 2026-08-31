# 文件用途：生产架构设计与实现（完整的 ChainQA 生产架构）
# API 层（FastAPI）/ Chain 层（LCEL 链）/ 模型层（多模型路由）
# 缓存层 / 监控层（Callback）。ProductionChainQA 类
# 运行：uvicorn 01_production_architecture:app --reload --port 8002
# 依赖：pip install langchain langchain-openai langserve fastapi uvicorn python-dotenv pydantic-settings
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.globals import set_llm_cache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langserve import add_routes

load_dotenv()


# ============================================================
# 配置层：Pydantic Settings 管理配置
# ============================================================

class Settings(BaseSettings):
    """应用配置，从环境变量/.env 自动加载"""
    openai_api_key: str = ""
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    timeout: int = 30
    enable_cache: bool = True
    cache_type: str = "memory"  # memory / sqlite

    class Config:
        env_file = ".env"
        env_prefix = "CHAINQA_"


settings = Settings()


# ============================================================
# 监控层：MetricsCallbackHandler 采集生产指标
# ============================================================

class ProductionMetricsHandler(BaseCallbackHandler):
    """生产级监控回调：采集延迟/Token/错误"""

    def __init__(self) -> None:
        self.call_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        self._start: dict[str, float] = {}

    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        self._start[str(run_id)] = time.time()

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self._start[str(run_id)] = time.time()

    def on_llm_end(self, response, *, run_id, **kwargs):
        rid = str(run_id)
        if rid in self._start:
            self.total_latency += time.time() - self._start[rid]
            self.call_count += 1

    def on_error(self, error, *, run_id, **kwargs):
        self.error_count += 1

    def get_stats(self) -> dict:
        return {
            "total_calls": self.call_count,
            "error_count": self.error_count,
            "error_rate": f"{(self.error_count / self.call_count * 100):.1f}%" if self.call_count else "0%",
            "avg_latency": f"{(self.total_latency / self.call_count):.3f}s" if self.call_count else "0s",
        }


metrics_handler = ProductionMetricsHandler()


# ============================================================
# 缓存层：设置 LLM 缓存
# ============================================================

def setup_cache() -> None:
    """初始化 LLM 缓存"""
    if not settings.enable_cache:
        return
    try:
        if settings.cache_type == "sqlite":
            from langchain_community.cache import SQLiteCache
            set_llm_cache(SQLiteCache(database_path="chainqa_cache.db"))
            print("✅ 已启用 SQLite 缓存")
        else:
            from langchain_core.caches import InMemoryCache
            set_llm_cache(InMemoryCache())
            print("✅ 已启用内存缓存")
    except Exception as e:
        print(f"⚠️  缓存初始化失败：{e}")


# ============================================================
# 模型层：多模型路由 + 重试 + 回退
# ============================================================

class ModelLayer:
    """模型层：管理模型实例、路由、重试、回退"""

    def __init__(self) -> None:
        self.primary_model = self._create_model(settings.primary_model)
        self.fallback_model = self._create_model(settings.fallback_model)

        # 主模型 + 回退
        self.model_with_fallback = self.primary_model.with_fallbacks(
            [self.fallback_model]
        )

        # 再加重试
        self.model_with_retry = self.model_with_fallback.with_retry(
            stop_after_attempt=settings.max_retries,
        )

    def _create_model(self, model_name: str) -> ChatOpenAI:
        """创建模型实例"""
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            timeout=settings.timeout,
            max_retries=2,
        )

    def get_model(self) -> Any:
        """获取带重试和回退的模型"""
        return self.model_with_retry

    def route_model(self, question: str) -> Any:
        """根据问题长度路由模型（简单成本控制）"""
        if len(question) < 30:
            # 短问题用小模型（成本低）
            return self.fallback_model
        # 长问题用主模型
        return self.model_with_retry


model_layer = ModelLayer()


# ============================================================
# Chain 层：LCEL 链
# ============================================================

class ChainLayer:
    """Chain 层：构建业务链"""

    def __init__(self) -> None:
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是 ChainQA 智能问答助手，请用准确简洁的中文回答。"),
            ("human", "{question}"),
        ])
        self.parser = StrOutputParser()

    def build_qa_chain(self) -> Any:
        """构建问答链：prompt | model | parser"""
        return self.prompt | model_layer.get_model() | self.parser

    def build_summary_chain(self) -> Any:
        """构建摘要链"""
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "请将用户文本总结为 50 字以内的中文摘要。"),
            ("human", "{text}"),
        ])
        return summary_prompt | model_layer.get_model() | self.parser


chain_layer = ChainLayer()


# ============================================================
# ProductionChainQA：整合所有层
# ============================================================

class ProductionChainQA:
    """生产级 ChainQA：整合 API 层 / Chain 层 / 模型层 / 缓存层 / 监控层"""

    def __init__(self) -> None:
        # 缓存层
        setup_cache()
        # Chain 层
        self.qa_chain = chain_layer.build_qa_chain().with_config(
            callbacks=[metrics_handler]
        )
        self.summary_chain = chain_layer.build_summary_chain().with_config(
            callbacks=[metrics_handler]
        )

    def answer(self, question: str) -> dict:
        """回答问题"""
        start = time.time()
        answer = self.qa_chain.invoke({"question": question})
        return {
            "question": question,
            "answer": answer,
            "latency_ms": int((time.time() - start) * 1000),
        }

    def summarize(self, text: str) -> dict:
        """生成摘要"""
        start = time.time()
        summary = self.summary_chain.invoke({"text": text})
        return {
            "summary": summary,
            "latency_ms": int((time.time() - start) * 1000),
        }


production_chainqa = ProductionChainQA()


# ============================================================
# API 网关层：FastAPI 应用
# ============================================================

app = FastAPI(
    title="ChainQA 生产版",
    description="完整 5 层架构的生产级 ChainQA 服务",
    version="3.0.0",
)


# 请求日志中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """记录所有请求的路径、耗时、状态码"""
    start = time.time()
    response = await call_next(request)
    latency = int((time.time() - start) * 1000)
    print(f"[API] {request.method} {request.url.path} → {response.status_code} ({latency}ms)")
    return response


# 自定义数据模型
class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QAResponse(BaseModel):
    question: str
    answer: str
    latency_ms: int


@app.get("/")
def root():
    return {
        "service": "ChainQA 生产版",
        "version": "3.0.0",
        "architecture": ["API层", "Chain层", "模型层", "缓存层", "监控层"],
        "endpoints": ["/api/qa", "/api/summary", "/metrics", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "ChainQA 生产版"}


@app.get("/metrics")
def metrics():
    """返回生产监控指标"""
    return metrics_handler.get_stats()


@app.post("/api/qa", response_model=QAResponse)
def api_qa(req: QARequest):
    """问答接口"""
    result = production_chainqa.answer(req.question)
    return QAResponse(**result)


@app.post("/api/summary")
def api_summary(text: str):
    """摘要接口"""
    return production_chainqa.summarize(text)


# LangServe 标准端点
add_routes(app, chain_layer.build_qa_chain(), path="/chainqa")


# ============================================================
# 直接运行
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Day12 - 01 生产架构设计与实现")
    print("ChainQA 生产版（5 层架构）")
    print("=" * 60)
    print("\n🏗️  架构层级：")
    print("   ├─ API 网关层（FastAPI + 中间件）")
    print("   ├─ Chain 层（LCEL 链）")
    print("   ├─ 模型层（多模型 + 重试 + 回退）")
    print("   ├─ 缓存层（LLM Cache）")
    print("   └─ 监控层（MetricsCallbackHandler）")
    print("\n🚀 启动服务...")
    print("\n服务启动后可访问：")
    print("  📖 API 文档:  http://localhost:8002/docs")
    print("  ❤️  健康检查:  http://localhost:8002/health")
    print("  📊 监控指标:  http://localhost:8002/metrics")
    print("  💬 问答接口:  POST http://localhost:8002/api/qa")
    print("=" * 60)

    uvicorn.run(
        "01_production_architecture:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
    )
