# 文件用途：FastAPI LLM 服务封装
# 完整的生产级 LLM API 服务，含 /chat /stream /embed /models /health 接口
# 中间件：认证 / 限流 / 日志 / CORS
# 统一错误处理、OpenAPI 文档配置、多模型路由
# 可直接 uvicorn 运行：uvicorn 01_fastapi_service:app --host 0.0.0.0 --port 8000
# Python 3.10+ 可运行
# 依赖：pip install fastapi uvicorn openai redis
# 需配置环境变量：OPENAI_API_KEY

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

# 可选 Redis 缓存
try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("API_KEY", "aisearch-secret-key")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-xxx")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# 模型路由配置：按任务复杂度路由
MODEL_ROUTING = {
    "simple": "gpt-4o-mini",   # 简单任务
    "complex": "gpt-4o",       # 复杂任务
    "default": "gpt-4o-mini",  # 默认
}

# 限流配置：每用户每分钟最大请求数
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT", "60"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aisearch")


# ---------------------------------------------------------------------------
# 缓存
# ---------------------------------------------------------------------------
class ResponseCache:
    """响应缓存（内存版，可选 Redis）。"""

    def __init__(self, use_redis: bool = False) -> None:
        self._redis = None
        self._memory: dict[str, str] = {}
        if use_redis and redis is not None:
            try:
                self._redis = redis.from_url(REDIS_URL, decode_responses=True)
                self._redis.ping()
                logger.info("Redis 缓存已连接")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Redis 连接失败，回退内存缓存: {exc}")
                self._redis = None

    @staticmethod
    def _key(model: str, messages: list[dict[str, str]]) -> str:
        raw = model + json.dumps(messages, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, model: str, messages: list[dict[str, str]]) -> str | None:
        key = self._key(model, messages)
        if self._redis:
            return self._redis.get(key)
        return self._memory.get(key)

    def set(self, model: str, messages: list[dict[str, str]], response: str, ttl: int = 3600) -> None:
        key = self._key(model, messages)
        if self._redis:
            self._redis.setex(key, ttl, response)
        else:
            self._memory[key] = response


# ---------------------------------------------------------------------------
# 限流器
# ---------------------------------------------------------------------------
class RateLimiter:
    """滑动窗口限流器（内存版）。"""

    def __init__(self, max_requests: int = 60, window: int = 60) -> None:
        self.max_requests = max_requests
        self.window = window
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, user_id: str) -> bool:
        now = time.time()
        bucket = self._buckets[user_id]
        # 清理过期记录
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True


# ---------------------------------------------------------------------------
# 模型路由
# ---------------------------------------------------------------------------
class ModelRouter:
    """根据请求复杂度路由到不同模型。"""

    def __init__(self, routing: dict[str, str] | None = None) -> None:
        self.routing = routing or MODEL_ROUTING

    def select(self, messages: list[dict[str, str]]) -> str:
        """简单路由策略：根据用户消息长度判断复杂度。"""
        user_content = ""
        for m in messages:
            if m.get("role") == "user":
                user_content += m.get("content", "")
        # 长问题或包含复杂关键词 → 大模型
        complex_keywords = ["代码", "分析", "对比", "设计", "架构", "推理", "解释"]
        if len(user_content) > 200 or any(kw in user_content for kw in complex_keywords):
            return self.routing["complex"]
        return self.routing["simple"]


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """对话请求。"""

    messages: list[dict[str, str]] = Field(..., description="对话消息列表")
    model: str | None = Field(None, description="模型名，不指定则自动路由")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=1, le=8192)
    stream: bool = Field(False, description="是否流式输出")
    use_cache: bool = Field(True, description="是否使用缓存")


class EmbedRequest(BaseModel):
    """向量生成请求。"""

    input: str | list[str] = Field(..., description="待向量化的文本")
    model: str = Field("text-embedding-3-small")


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    openai: bool
    redis: bool
    uptime: float


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AISearch LLM API",
    description="生产级 LLM API 服务，支持对话、流式、向量生成、多模型路由、缓存与限流",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局组件
_cache = ResponseCache(use_redis=True)
_limiter = RateLimiter(max_requests=RATE_LIMIT_PER_MINUTE)
_router = ModelRouter()
_start_time = time.time()

# OpenAI 客户端
_openai_client = None
if OpenAI is not None:
    _openai_client = OpenAI(
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY,
    )


# ---------------------------------------------------------------------------
# 中间件
# ---------------------------------------------------------------------------
@app.middleware("http")
async def auth_and_log_middleware(request: Request, call_next):
    """认证与日志中间件。"""
    start = time.time()

    # 健康检查接口跳过认证
    if request.url.path in ("/health", "/ready", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    # API Key 认证
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "未提供有效的 Authorization 头"},
        )
    token = auth[7:]
    if token != API_KEY:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "API Key 无效"},
        )

    # 限流（基于 API Key）
    user_id = token[:8]
    if not _limiter.allow(user_id):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "请求过于频繁，请稍后再试"},
        )

    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} latency={elapsed:.3f}s"
    )
    response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
    return response


# ---------------------------------------------------------------------------
# 统一错误处理
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "内部服务器错误", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# 接口
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["运维"])
async def health_check():
    """健康检查接口。"""
    openai_ok = _openai_client is not None
    redis_ok = _cache._redis is not None
    return HealthResponse(
        status="healthy" if openai_ok else "degraded",
        openai=openai_ok,
        redis=redis_ok,
        uptime=round(time.time() - _start_time, 2),
    )


@app.get("/ready", tags=["运维"])
async def readiness_check():
    """就绪检查接口。"""
    if _openai_client is None:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "OpenAI 客户端未初始化"},
        )
    return {"status": "ready"}


@app.get("/models", tags=["模型"])
async def list_models():
    """列出可用模型。"""
    return {
        "models": [
            {"id": v, "tier": k, "description": f"{'复杂' if k == 'complex' else '简单'}任务模型"}
            for k, v in MODEL_ROUTING.items()
            if k != "default"
        ],
        "default": MODEL_ROUTING["default"],
    }


@app.post("/chat", tags=["对话"])
async def chat(req: ChatRequest):
    """同步对话接口。"""
    if _openai_client is None:
        raise HTTPException(503, "OpenAI 客户端未初始化，请检查 API Key 配置")

    # 模型路由
    model = req.model or _router.select(req.messages)

    # 缓存查询
    if req.use_cache and not req.stream:
        cached = _cache.get(model, req.messages)
        if cached:
            logger.info(f"缓存命中 model={model}")
            return {"response": cached, "model": model, "cached": True}

    try:
        resp = _openai_client.chat.completions.create(
            model=model,
            messages=req.messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        content = resp.choices[0].message.content or ""
        usage = resp.usage

        # 写入缓存
        if req.use_cache:
            _cache.set(model, req.messages, content)

        return {
            "response": content,
            "model": model,
            "cached": False,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            },
        }
    except Exception as exc:
        logger.error(f"对话调用失败: {exc}")
        raise HTTPException(502, f"模型调用失败: {exc}")


@app.post("/stream", tags=["对话"])
async def stream_chat(req: ChatRequest):
    """流式对话接口（SSE）。"""
    if _openai_client is None:
        raise HTTPException(503, "OpenAI 客户端未初始化")

    model = req.model or _router.select(req.messages)

    def event_stream():
        try:
            stream = _openai_client.chat.completions.create(
                model=model,
                messages=req.messages,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'content': delta, 'model': model}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'model': model}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/embed", tags=["向量"])
async def embed(req: EmbedRequest):
    """向量生成接口。"""
    if _openai_client is None:
        raise HTTPException(503, "OpenAI 客户端未初始化")

    try:
        resp = _openai_client.embeddings.create(
            input=req.input,
            model=req.model,
        )
        return {
            "embeddings": [d.embedding for d in resp.data],
            "model": req.model,
            "count": len(resp.data),
        }
    except Exception as exc:
        logger.error(f"向量生成失败: {exc}")
        raise HTTPException(502, f"向量生成失败: {exc}")


# ---------------------------------------------------------------------------
# 启动入口（支持 python 01_fastapi_service.py 直接运行）
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "01_fastapi_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
