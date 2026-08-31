# 文件用途：最佳实践综合示例（整合 Day01-Day12 所学）
# Prompt 管理 + LCEL 链 + Memory + Document Loaders + Retriever + Tools
# + Callbacks + LangServe 部署。完整的 ChainQA 生产级应用
# 含配置管理/错误处理/缓存/监控/日志
# 运行：uvicorn 04_best_practices:app --reload --port 8003
# 依赖：pip install langchain langchain-openai langchain-community langserve
#       fastapi uvicorn python-dotenv pydantic-settings
# 需要：在 .env 中配置 OPENAI_API_KEY

"""
ChainQA 生产级应用 - 整合 Day01-Day12 全部最佳实践

架构：
  ┌─ API 层（FastAPI + LangServe）
  ├─ Chain 层（LCEL + 工具调用）
  ├─ 模型层（多模型 + 重试 + 回退）
  ├─ 记忆层（对话历史）
  ├─ 缓存层（LLM Cache）
  └─ 监控层（Callback 指标采集）
"""

from __future__ import annotations

import json
import os
import time
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# LangChain 核心导入
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.caches import InMemoryCache
from langchain_core.documents import Document
from langchain_core.globals import set_llm_cache
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()


# ============================================================
# 1. 配置管理层（Day12：Pydantic Settings）
# ============================================================

class ChainQASettings(BaseSettings):
    """ChainQA 生产配置 - 从环境变量加载，不硬编码密钥"""
    openai_api_key: str = ""
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    timeout: int = 30
    enable_cache: bool = True
    log_file: str = "chainqa.log"

    class Config:
        env_file = ".env"
        env_prefix = "CHAINQA_"


settings = ChainQASettings()


# ============================================================
# 2. 监控层（Day10：Callback 指标采集 + 日志）
# ============================================================

class ProductionMonitor(BaseCallbackHandler):
    """生产监控回调：日志 + 指标双采集"""

    def __init__(self, log_file: str) -> None:
        self.log_file = log_file
        self.call_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        self._starts: dict[str, float] = {}

    def _log(self, event: str, data: dict) -> None:
        entry = {"ts": time.time(), "event": event, **data}
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self._starts[str(run_id)] = time.time()
        self._log("llm_start", {"run_id": str(run_id)})

    def on_llm_end(self, response, *, run_id, **kwargs):
        rid = str(run_id)
        if rid in self._starts:
            elapsed = time.time() - self._starts[rid]
            self.total_latency += elapsed
            self.call_count += 1
            self._log("llm_end", {"run_id": rid, "latency": round(elapsed, 3)})

    def on_error(self, error, *, run_id, **kwargs):
        self.error_count += 1
        self._log("error", {"error": str(error)[:200]})

    def stats(self) -> dict:
        return {
            "calls": self.call_count,
            "errors": self.error_count,
            "avg_latency": f"{self.total_latency / self.call_count:.3f}s" if self.call_count else "0s",
        }


monitor = ProductionMonitor(settings.log_file)


# ============================================================
# 3. 缓存层（Day12：LLM Cache）
# ============================================================

if settings.enable_cache:
    set_llm_cache(InMemoryCache())


# ============================================================
# 4. 模型层（Day02 + Day12：多模型 + 重试 + 回退）
# ============================================================

def create_model() -> Any:
    """创建带重试和回退的生产级模型"""
    primary = ChatOpenAI(
        model=settings.primary_model, temperature=0, timeout=settings.timeout
    )
    fallback = ChatOpenAI(
        model=settings.fallback_model, temperature=0, timeout=settings.timeout
    )
    # 重试 + 回退双重保障
    return primary.with_retry(
        stop_after_attempt=settings.max_retries
    ).with_fallbacks([fallback])


model = create_model()


# ============================================================
# 5. 工具层（Day09：自定义工具 + 错误处理）
# ============================================================

@tool
def search_knowledge_base(query: str) -> str:
    """在 ChainQA 知识库中搜索信息。

    当用户询问 LangChain、LCEL、Memory、Tools 等技术概念时使用本工具。

    参数:
        query: 搜索关键词
    """
    # 模拟知识库（真实场景用 VectorStore + Retriever）
    kb = {
        "langchain": "LangChain 是 LLM 应用开发框架，提供模型调用/Prompt/链式组合等能力",
        "lcel": "LCEL 是 LangChain 表达式语言，用管道符 | 组合组件",
        "memory": "Memory 管理多轮对话历史，包括 Buffer/Summary/Window 等策略",
        "tools": "Tools 让 LLM 调用外部函数，实现 Tool Calling",
    }
    key = query.lower().strip()
    for k, v in kb.items():
        if k in key:
            return v
    return f"知识库中未找到关于 '{query}' 的信息"


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。当用户需要数学计算时使用。

    参数:
        expression: 数学表达式，如 "1+2*3"
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败：{e}"


TOOL_MAP = {
    "search_knowledge_base": search_knowledge_base,
    "calculator": calculator,
}


# ============================================================
# 6. Chain 层（Day05 LCEL + Day09 Tools + Day06 Memory）
# ============================================================

class ChainQAPipeline:
    """ChainQA 生产级流水线

    整合：
    - Prompt 管理（Day03）
    - LCEL 链（Day05）
    - 工具调用（Day09）
    - 错误处理（Day12）
    - 监控（Day10）
    - 缓存（Day12）
    """

    def __init__(self) -> None:
        self.model_with_tools = model.bind_tools([search_knowledge_base, calculator])
        # 对话历史（简化版，生产用 RunnableWithMessageHistory）
        self.conversation_history: list = []

        # Prompt 模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是 ChainQA 智能问答助手。可以调用工具获取信息，用准确简洁的中文回答。"),
            MessagesPlaceholder("history", optional=True),
            ("human", "{question}"),
        ])

    def answer(self, question: str) -> dict:
        """回答问题（含工具调用完整流程）"""
        start = time.time()
        history = list(self.conversation_history[-6:])  # 保留最近3轮

        # 构造消息
        messages = self.prompt.format_messages(
            question=question,
            history=history,
        )

        # 步骤1：模型决定是否调用工具
        ai_msg = self.model_with_tools.invoke(
            messages, config={"callbacks": [monitor]}
        )

        # 步骤2：执行工具（如有调用）
        if ai_msg.tool_calls:
            messages.append(ai_msg)
            for tc in ai_msg.tool_calls:
                selected = TOOL_MAP.get(tc["name"])
                if selected:
                    result = selected.invoke(tc["args"])
                else:
                    result = f"工具 {tc['name']} 不存在"
                messages.append(ToolMessage(
                    content=result, tool_call_id=tc["id"]
                ))
            # 步骤3：基于工具结果生成最终回复
            final = self.model_with_tools.invoke(
                messages, config={"callbacks": [monitor]}
            )
            answer = final.content
        else:
            answer = ai_msg.content

        # 更新对话历史
        self.conversation_history.append(HumanMessage(content=question))
        self.conversation_history.append(ai_msg)

        return {
            "question": question,
            "answer": answer,
            "latency_ms": int((time.time() - start) * 1000),
            "tools_used": [tc["name"] for tc in ai_msg.tool_calls] if ai_msg.tool_calls else [],
        }


pipeline = ChainQAPipeline()


# ============================================================
# 7. 简单 RAG 检索链（Day08：Retriever 模式演示）
# ============================================================

def build_simple_rag_chain() -> Any:
    """构建简单的 RAG 检索链（Day08 基础演示）

    真实场景用 VectorStore + Embeddings，这里用关键词匹配简化。
    """
    # 模拟文档库
    docs = [
        Document(page_content="LangChain 0.3 是最新稳定版，推荐使用 LCEL 语法"),
        Document(page_content="LangGraph 用于编排复杂工作流，支持循环和分支"),
        Document(page_content="LangServe 把 Chain 部署为 REST API"),
        Document(page_content="LangSmith 是追踪和评估平台"),
    ]

    def retrieve(query: dict) -> dict:
        """简单关键词检索"""
        question = query["question"]
        # 关键词匹配（真实用向量相似度）
        results = [d for d in docs if any(w in d.page_content for w in question.split())]
        context = "\n".join(d.page_content for d in results) if results else "无相关文档"
        return {"context": context, "question": question}

    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", "基于以下上下文回答问题。若上下文不足请说明。\n\n上下文：{context}"),
        ("human", "{question}"),
    ])

    return (
        RunnablePassthrough()
        | RunnableLambda(retrieve)
        | rag_prompt
        | model
        | StrOutputParser()
    )


rag_chain = build_simple_rag_chain().with_config(callbacks=[monitor])


# ============================================================
# 8. API 网关层（Day11：FastAPI + LangServe）
# ============================================================

app = FastAPI(
    title="ChainQA 生产级应用",
    description="整合 Day01-Day12 最佳实践的完整 ChainQA 服务",
    version="4.0.0",
)


# 请求日志中间件
@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = int((time.time() - start) * 1000)
    print(f"[{time.strftime('%H:%M:%S')}] {request.method} {request.url.path} → {response.status_code} ({latency}ms)")
    return response


# 请求/响应模型
class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QAResponse(BaseModel):
    question: str
    answer: str
    latency_ms: int
    tools_used: list[str] = []


@app.get("/")
def root():
    return {
        "service": "ChainQA 生产级应用",
        "version": "4.0.0",
        "features": [
            "Prompt 管理", "LCEL 链", "工具调用", "对话记忆",
            "RAG 检索", "缓存", "重试回退", "监控日志", "LangServe API",
        ],
        "endpoints": ["/api/qa", "/api/rag", "/api/history", "/metrics", "/health", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "ChainQA", "version": "4.0.0"}


@app.get("/metrics")
def metrics():
    return monitor.stats()


@app.post("/api/qa", response_model=QAResponse)
def api_qa(req: QARequest):
    """智能问答（含工具调用）"""
    result = pipeline.answer(req.question)
    return QAResponse(**result)


@app.post("/api/rag")
def api_rag(req: QARequest):
    """RAG 检索问答"""
    start = time.time()
    answer = rag_chain.invoke({"question": req.question})
    return {
        "question": req.question,
        "answer": answer,
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.get("/api/history")
def api_history():
    """查看对话历史"""
    return {
        "history_count": len(pipeline.conversation_history),
        "recent": [
            {"role": type(m).__name__, "content": str(m.content)[:100]}
            for m in pipeline.conversation_history[-10:]
        ],
    }


# 注册 LangServe 标准端点（Day11）
from langserve import add_routes
add_routes(app, rag_chain, path="/rag")


# ============================================================
# 9. 直接运行
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Day12 - 04 ChainQA 最佳实践综合示例")
    print("整合 Day01-Day12 全部所学")
    print("=" * 60)
    print("\n🏗️  整合能力清单：")
    print("   Day01-02: LangChain 基础 + Model I/O")
    print("   Day03:    Prompt 管理（ChatPromptTemplate）")
    print("   Day04:    Output Parsers（StrOutputParser）")
    print("   Day05:    LCEL 链（管道符组合）")
    print("   Day06:    Memory（对话历史）")
    print("   Day07:    Document（知识库文档）")
    print("   Day08:    Retriever（RAG 检索链）")
    print("   Day09:    Tools（工具调用）")
    print("   Day10:    Callbacks（监控采集）")
    print("   Day11:    LangServe（API 部署）")
    print("   Day12:    生产最佳实践（配置/缓存/重试/回退/日志）")
    print("\n🚀 启动服务...")
    print("\n服务启动后可访问：")
    print("  📖 API 文档:    http://localhost:8003/docs")
    print("  ❤️  健康检查:    http://localhost:8003/health")
    print("  📊 监控指标:    http://localhost:8003/metrics")
    print("  💬 智能问答:    POST http://localhost:8003/api/qa")
    print("  🔍 RAG 问答:    POST http://localhost:8003/api/rag")
    print("  📜 对话历史:    GET  http://localhost:8003/api/history")
    print("  🎮 Playground:  http://localhost:8003/rag/playground")
    print("\n调用示例：")
    print('  curl -X POST http://localhost:8003/api/qa \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"question": "什么是 LangChain？"}\'')
    print("=" * 60)

    uvicorn.run(
        "04_best_practices:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )
