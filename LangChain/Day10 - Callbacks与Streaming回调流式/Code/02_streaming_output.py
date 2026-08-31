# 文件用途：流式输出实现（同步 stream / 异步 astream / AIMessageChunk 拼接 / 打字机效果）
# 场景：ChainQA 流式问答输出
# 运行：python 02_streaming_output.py
# 依赖：pip install langchain langchain-openai python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import asyncio
import os
import time
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# 流式 Callback：on_llm_new_token 逐 Token 触发
# ============================================================

class StreamingCallbackHandler(BaseCallbackHandler):
    """流式输出回调：在每个 Token 生成时打印（打字机效果）"""

    def __init__(self) -> None:
        self.token_count = 0
        self.start_time: float | None = None

    def on_llm_start(self, serialized, prompts, *, run_id: UUID, **kwargs) -> None:
        self.start_time = time.time()
        self.token_count = 0
        print("🤖 ChainQA 回复：", end="", flush=True)

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """每个 Token 生成时触发——打字机效果核心"""
        self.token_count += 1
        # 直接打印 Token，不换行，立即刷新
        print(token, end="", flush=True)

    def on_llm_end(self, response, *, run_id: UUID, **kwargs) -> None:
        elapsed = time.time() - (self.start_time or time.time())
        print(f"\n\n📊 流式统计：共 {self.token_count} 个 Token，耗时 {elapsed:.2f}s")


# ============================================================
# 构建 ChainQA 流式链
# ============================================================

def build_chainqa_chain():
    """构建 ChainQA 问答链"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手，请用清晰有条理的中文回答。"),
        ("human", "{question}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    parser = StrOutputParser()
    return prompt | model | parser


# ============================================================
# 方式一：同步流式 .stream()
# ============================================================

def demo_sync_stream(question: str) -> None:
    """同步流式输出：逐 chunk 拼接"""
    print(f"\n📝 问题：{question}")
    print("─" * 60)

    chain = build_chainqa_chain()

    # 方式A：直接遍历 .stream()，逐 chunk 打印
    print("方式A：遍历 .stream() 输出（含 chunk 拼接）")
    full_output = ""
    chunk_count = 0
    start = time.time()

    for chunk in chain.stream({"question": question}):
        # chunk 是字符串（因为末尾是 StrOutputParser）
        # 如果没有 parser，chunk 会是 AIMessageChunk，需要 .content
        print(chunk, end="", flush=True)
        full_output += chunk
        chunk_count += 1

    elapsed = time.time() - start
    print(f"\n\n📊 同步流式：{chunk_count} 个 chunk，耗时 {elapsed:.2f}s")
    print(f"完整输出长度：{len(full_output)} 字符")


# ============================================================
# 方式二：流式 + Callback（on_llm_new_token 触发打字机）
# ============================================================

def demo_stream_with_callback(question: str) -> None:
    """流式输出配合 Callback：on_llm_new_token 逐 Token 触发"""
    print(f"\n📝 问题：{question}")
    print("─" * 60)
    print("方式B：流式 + StreamingCallbackHandler（on_llm_new_token）")

    chain = build_chainqa_chain()
    handler = StreamingCallbackHandler()

    # 注意：当模型开启 streaming=True，on_llm_new_token 会逐 Token 触发
    # .stream() 本身也会返回 chunk，这里我们用 invoke + callback 展示回调触发
    result = chain.invoke(
        {"question": question},
        config={"callbacks": [handler]},
    )


# ============================================================
# 方式三：异步流式 .astream()
# ============================================================

async def demo_async_stream(question: str) -> None:
    """异步流式输出：async for 遍历"""
    print(f"\n📝 问题：{question}")
    print("─" * 60)
    print("方式C：异步流式 .astream()")

    chain = build_chainqa_chain()
    full_output = ""
    chunk_count = 0
    start = time.time()

    async for chunk in chain.astream({"question": question}):
        print(chunk, end="", flush=True)
        full_output += chunk
        chunk_count += 1

    elapsed = time.time() - start
    print(f"\n\n📊 异步流式：{chunk_count} 个 chunk，耗时 {elapsed:.2f}s")


# ============================================================
# 方式四：AIMessageChunk 拼接演示（不接 parser）
# ============================================================

def demo_chunk_concat(question: str) -> None:
    """演示 AIMessageChunk 拼接（不接 StrOutputParser）"""
    print(f"\n📝 问题：{question}")
    print("─" * 60)
    print("方式D：AIMessageChunk 拼接（无 parser，直接处理 model 输出）")

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)

    full_chunk = None
    for chunk in model.stream(question):
        # chunk 是 AIMessageChunk
        if full_chunk is None:
            full_chunk = chunk
        else:
            # AIMessageChunk 支持 + 拼接
            full_chunk = full_chunk + chunk
        print(chunk.content, end="", flush=True)

    print(f"\n\n📊 拼接后完整消息类型: {type(full_chunk).__name__}")
    print(f"完整内容长度: {len(full_chunk.content)} 字符")
    # 拼接后的 full_chunk 是完整的 AIMessage（功能等价）
    print(f"usage_metadata: {getattr(full_chunk, 'usage_metadata', 'N/A')}")


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day10 - 02 流式输出实现演示")
    print("场景：ChainQA 流式问答（打字机效果）")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    question = "请用 3 句话介绍 LangChain 框架的核心能力"

    # 方式一：同步流式
    print("\n" + "=" * 60)
    print("演示1：同步流式 .stream()")
    print("=" * 60)
    demo_sync_stream(question)

    # 方式二：流式 + Callback
    print("\n\n" + "=" * 60)
    print("演示2：流式 + StreamingCallbackHandler")
    print("=" * 60)
    demo_stream_with_callback(question)

    # 方式三：异步流式
    print("\n\n" + "=" * 60)
    print("演示3：异步流式 .astream()")
    print("=" * 60)
    asyncio.run(demo_async_stream(question))

    # 方式四：Chunk 拼接
    print("\n\n" + "=" * 60)
    print("演示4：AIMessageChunk 拼接")
    print("=" * 60)
    demo_chunk_concat(question)

    print("\n\n" + "=" * 60)
    print("✅ 流式输出演示完成")
    print("要点：")
    print("  1. .stream() 同步流式，.astream() 异步流式")
    print("  2. 流式返回 AIMessageChunk，可用 + 拼接为完整消息")
    print("  3. 模型需 streaming=True，on_llm_new_token 才会逐 Token 触发")
    print("  4. 打字机效果：print(token, end='', flush=True)")
    print("=" * 60)


if __name__ == "__main__":
    main()
