# 文件用途：LangServe 基础 API 部署
# 创建 Chain → FastAPI app → add_routes 注册 → 自动生成端点 → 启动服务
# 场景：ChainQA API 服务基础版
# 运行：uvicorn 01_langserve_basic:app --reload --port 8000
# 依赖：pip install langchain langchain-openai langserve fastapi uvicorn python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langserve import add_routes

load_dotenv()


# ============================================================
# 1. 创建 ChainQA 问答 Chain
# ============================================================

def build_chainqa_chain():
    """构建 ChainQA 问答链：prompt | model | parser"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手，请用准确简洁的中文回答用户问题。"),
        ("human", "{question}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()
    # LCEL 链式组合
    return prompt | model | parser


def build_summary_chain():
    """构建摘要链：输入文本，输出摘要"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "请将用户提供的文本总结为 50 字以内的中文摘要。"),
        ("human", "{text}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()
    return prompt | model | parser


# ============================================================
# 2. 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title="ChainQA API",
    description="基于 LangServe 部署的 ChainQA 智能问答 API",
    version="1.0.0",
)


# ============================================================
# 3. 健康检查端点（自定义）
# ============================================================

@app.get("/")
def root():
    """根路径：API 信息"""
    return {
        "service": "ChainQA API",
        "version": "1.0.0",
        "endpoints": [
            "/chainqa/invoke - 问答调用",
            "/chainqa/batch - 批量调用",
            "/chainqa/stream - 流式调用",
            "/chainqa/playground - 在线调试",
            "/summary/invoke - 摘要调用",
            "/docs - API 文档（Swagger）",
        ],
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok", "service": "ChainQA API"}


# ============================================================
# 4. add_routes 注册 Chain 为 API 端点
# ============================================================

# 注册 ChainQA 问答链
# 访问路径：POST /chainqa/invoke, /chainqa/batch, /chainqa/stream, GET /chainqa/playground
add_routes(
    app,
    build_chainqa_chain(),
    path="/chainqa",
    # 可选：禁用某些端点
    # disabled_endpoints=["playground"],
)

# 注册摘要链
add_routes(
    app,
    build_summary_chain(),
    path="/summary",
)


# ============================================================
# 5. 直接运行（开发模式）
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Day11 - 01 LangServe 基础 API 部署")
    print("ChainQA API 服务")
    print("=" * 60)
    print("\n🚀 启动服务...")
    print("\n服务启动后，可访问以下端点：")
    print("  📖 API 文档:     http://localhost:8000/docs")
    print("  🎮 Playground:   http://localhost:8000/chainqa/playground")
    print("  ❤️  健康检查:     http://localhost:8000/health")
    print("\n调用示例：")
    print('  curl -X POST http://localhost:8000/chainqa/invoke \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"input": {"question": "什么是 LangChain？"}}\'')
    print("=" * 60)

    uvicorn.run(
        "01_langserve_basic:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
