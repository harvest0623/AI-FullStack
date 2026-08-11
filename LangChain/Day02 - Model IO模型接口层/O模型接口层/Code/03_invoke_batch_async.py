# 文件用途：三种调用方式对比（invoke / batch / stream / ainvoke）
# 同一任务用四种方式实现，对比执行速度和输出格式
# 展示 batch 的并行处理能力，含性能计时

import os
import sys
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. invoke 单次调用
# ============================================================
def demo_invoke():
    """invoke 单次调用"""
    print("=" * 60)
    print("【1】invoke 单次调用")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = "用一句话解释什么是 Python。"

    start = time.perf_counter()
    result = model.invoke([HumanMessage(content=prompt)])
    elapsed = time.perf_counter() - start

    print(f"  Prompt：{prompt}")
    print(f"  回复：{result.content}")
    print(f"  耗时：{elapsed:.3f} 秒")
    print(f"  返回类型：{type(result).__name__}")
    print(f"  Token：{result.usage_metadata}\n")


# ============================================================
# 2. batch 批量调用
# ============================================================
def demo_batch():
    """batch 批量调用（并行处理多个输入）"""
    print("=" * 60)
    print("【2】batch 批量调用")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompts = [
        "用一句话解释什么是 Python。",
        "用一句话解释什么是 JavaScript。",
        "用一句话解释什么是 Go。",
    ]

    inputs = [[HumanMessage(content=p)] for p in prompts]

    # batch 并行处理
    start = time.perf_counter()
    results = model.batch(inputs)
    elapsed_batch = time.perf_counter() - start

    print("  批量结果：")
    for prompt, result in zip(prompts, results):
        print(f"    [{prompt}] → {result.content}")
    print(f"  batch 总耗时：{elapsed_batch:.3f} 秒\n")

    # 对比：用 for 循环逐个调用
    print("  对比：for 循环逐个调用（串行）")
    start = time.perf_counter()
    for prompt in prompts:
        model.invoke([HumanMessage(content=prompt)])
    elapsed_loop = time.perf_counter() - start
    print(f"  for 循环总耗时：{elapsed_loop:.3f} 秒\n")

    print(f"  ⚡ batch 比 for 循环快约 {elapsed_loop / elapsed_batch:.1f} 倍")
    print(f"  （batch 并行发送请求，for 循环串行等待）\n")


# ============================================================
# 3. stream 流式输出
# ============================================================
def demo_stream():
    """stream 流式输出"""
    print("=" * 60)
    print("【3】stream 流式输出")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from langchain_core.messages import AIMessageChunk

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    prompt = "用三句话介绍 LangChain 框架。"

    print(f"  Prompt：{prompt}")
    print("  流式输出：\n")

    start = time.perf_counter()
    first_chunk_time = None
    full_content = ""
    chunk_count = 0

    # stream 返回 AIMessageChunk 迭代器
    for chunk in model.stream([HumanMessage(content=prompt)]):
        if first_chunk_time is None:
            first_chunk_time = time.perf_counter() - start
        chunk_count += 1
        print(chunk.content, end="", flush=True)
        full_content += chunk.content

    elapsed = time.perf_counter() - start

    print(f"\n\n  首字延迟：{first_chunk_time:.3f} 秒")
    print(f"  总耗时：{elapsed:.3f} 秒")
    print(f"  分片数：{chunk_count}")
    print(f"  总字符数：{len(full_content)}")
    print(f"  分片类型：{AIMessageChunk.__name__}\n")


# ============================================================
# 4. ainvoke 异步调用
# ============================================================
async def _async_invoke(model, prompt):
    """单个异步调用"""
    from langchain_core.messages import HumanMessage
    return await model.ainvoke([HumanMessage(content=prompt)])


def demo_ainvoke():
    """ainvoke 异步调用"""
    print("=" * 60)
    print("【4】ainvoke 异步调用")
    print("=" * 60)

    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompts = [
        "用一句话解释什么是 Python。",
        "用一句话解释什么是 Java。",
        "用一句话解释什么是 Rust。",
    ]

    # 方式 A：异步并发调用（同时发 3 个请求）
    async def concurrent_call():
        start = time.perf_counter()
        # asyncio.gather 并发执行多个 ainvoke
        tasks = [_async_invoke(model, p) for p in prompts]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
        return results, elapsed

    results, elapsed = asyncio.run(concurrent_call())

    print("  异步并发调用结果：")
    for prompt, result in zip(prompts, results):
        print(f"    [{prompt}] → {result.content}")
    print(f"  异步并发总耗时：{elapsed:.3f} 秒")
    print(f"  （3 个请求并发，总耗时约等于单个请求耗时）\n")


# ============================================================
# 5. 性能对比汇总
# ============================================================
def performance_summary():
    """性能对比汇总"""
    print("=" * 60)
    print("【5】四种调用方式对比汇总")
    print("=" * 60)

    print("""
┌──────────┬────────┬──────────┬─────────────────────────────────────┐
│ 方式     │ 同步性 │ 输出类型  │ 适用场景                            │
├──────────┼────────┼──────────┼─────────────────────────────────────┤
│ invoke   │ 同步   │ AIMessage │ 单次请求，简单场景                  │
│ batch    │ 同步   │ List     │ 批量处理，并行高效                  │
│ stream   │ 同步   │ Chunk    │ 实时显示，聊天界面                  │
│ ainvoke  │ 异步   │ AIMessage │ 高并发，Web 服务                    │
│ abatch   │ 异步   │ List     │ 大批量异步并发                      │
└──────────┴────────┴──────────┴─────────────────────────────────────┘

选择建议：
  • 单个请求      → invoke
  • 多个请求      → batch（比 for+invoke 快很多）
  • 实时显示      → stream（首字延迟低）
  • Web 高并发    → ainvoke / abatch
""")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day02 - 三种调用方式对比\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  请先配置 OPENAI_API_KEY")
        sys.exit(1)
    else:
        demo_invoke()
        demo_batch()
        demo_stream()
        demo_ainvoke()

    performance_summary()

    print("=" * 60)
    print("✅ 调用方式对比完成")
    print("=" * 60)
