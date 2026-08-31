# 文件用途：自定义 Callback Handler（LoggingCallbackHandler）
# 记录 Chain 执行各阶段的时间/输入/输出/Token 数/错误
# 场景：ChainQA 执行过程日志记录
# 运行：python 01_callback_handler.py
# 依赖：pip install langchain langchain-openai python-dotenv
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
import time
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler, StdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# 自定义 LoggingCallbackHandler：完整执行过程追踪
# ============================================================

class LoggingCallbackHandler(BaseCallbackHandler):
    """记录 Chain 执行全过程的自定义回调处理器。

    追踪：
    - 各阶段时间戳与耗时
    - LLM 调用的输入输出
    - Token 生成（流式时）
    - Chain 的输入输出
    - 错误信息
    """

    def __init__(self, name: str = "ChainQA-Logger") -> None:
        self.name = name
        self._start_times: dict[UUID, float] = {}  # run_id → 开始时间
        self._llm_token_count: dict[UUID, int] = {}  # run_id → Token 数

    # ── LLM 相关 ──
    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """LLM 调用开始"""
        self._start_times[run_id] = time.time()
        self._llm_token_count[run_id] = 0
        model_name = serialized.get("name", "unknown")
        print(f"\n[{self.name}] 🟢 LLM 开始 | model={model_name} | run_id={run_id}")
        print(f"[{self.name}]    输入 prompts: {str(prompts)[:120]}...")

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """ChatModel 调用开始"""
        self._start_times[run_id] = time.time()
        self._llm_token_count[run_id] = 0
        print(f"\n[{self.name}] 🟢 ChatModel 开始 | run_id={run_id}")
        # 打印最后一条消息（通常是用户问题）
        if messages and messages[0]:
            last_msg = messages[0][-1]
            print(f"[{self.name}]    最后消息: {str(last_msg)[:120]}...")

    def on_llm_new_token(self, token: str, *, run_id: UUID, **kwargs: Any) -> None:
        """LLM 生成新 Token（流式时触发）"""
        self._llm_token_count[run_id] = self._llm_token_count.get(run_id, 0) + 1

    def on_llm_end(self, response, *, run_id: UUID, **kwargs: Any) -> None:
        """LLM 调用结束"""
        elapsed = time.time() - self._start_times.get(run_id, time.time())
        token_count = self._llm_token_count.get(run_id, 0)
        # 提取输出文本
        output = ""
        if response.generators:
            pass
        try:
            output = response.llm_output or ""
        except Exception:
            pass
        print(f"[{self.name}] 🔴 LLM 结束 | 耗时={elapsed:.3f}s | tokens≈{token_count}")
        if output:
            print(f"[{self.name}]    输出: {str(output)[:120]}...")

    # ── Chain 相关 ──
    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Chain 开始"""
        self._start_times[run_id] = time.time()
        chain_name = serialized.get("name", "chain")
        print(f"\n[{self.name}] 🟦 Chain 开始 | name={chain_name} | run_id={run_id}")
        print(f"[{self.name}]    输入: {str(inputs)[:120]}...")

    def on_chain_end(self, outputs: dict[str, Any], *, run_id: UUID, **kwargs: Any) -> None:
        """Chain 结束"""
        elapsed = time.time() - self._start_times.get(run_id, time.time())
        print(f"[{self.name}] 🟥 Chain 结束 | 耗时={elapsed:.3f}s")
        print(f"[{self.name}]    输出: {str(outputs)[:120]}...")

    # ── 工具相关 ──
    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """工具开始"""
        self._start_times[run_id] = time.time()
        tool_name = serialized.get("name", "tool")
        print(f"\n[{self.name}] 🟡 Tool 开始 | name={tool_name} | run_id={run_id}")
        print(f"[{self.name}]    输入: {input_str[:120]}")

    def on_tool_end(self, output: str, *, run_id: UUID, **kwargs: Any) -> None:
        """工具结束"""
        elapsed = time.time() - self._start_times.get(run_id, time.time())
        print(f"[{self.name}] 🟠 Tool 结束 | 耗时={elapsed:.3f}s")
        print(f"[{self.name}]    输出: {str(output)[:120]}...")

    # ── 错误处理 ──
    def on_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        """错误发生"""
        elapsed = time.time() - self._start_times.get(run_id, time.time())
        print(f"\n[{self.name}] ❌ 错误 | 耗时={elapsed:.3f}s")
        print(f"[{self.name}]    错误类型: {type(error).__name__}")
        print(f"[{self.name}]    错误信息: {error}")

    # ── 文本输出 ──
    def on_text(self, text: str, *, run_id: UUID, **kwargs: Any) -> None:
        """文本输出（通用）"""
        # 仅在调试时打印，避免过多输出
        pass


# ============================================================
# 构建 ChainQA 问答链
# ============================================================

def build_chainqa_chain():
    """构建 ChainQA 简单问答链：prompt | model | parser"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是 ChainQA 智能问答助手，请用简洁准确的中文回答用户问题。"),
        ("human", "{question}"),
    ])
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()
    # LCEL 链式组合
    return prompt | model | parser


# ============================================================
# 主流程：演示 Callback 配置方式
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day10 - 01 自定义 Callback Handler 演示")
    print("场景：ChainQA 执行过程日志记录")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    # 构建 ChainQA 链
    chain = build_chainqa_chain()

    # 创建自定义 Handler
    custom_handler = LoggingCallbackHandler("ChainQA-Logger")
    # 内置 Handler（控制台打印）
    stdout_handler = StdOutCallbackHandler()

    # ── 演示1：使用 config 配置 Callback（最常用） ──
    print("\n" + "─" * 60)
    print("演示1：使用 config={'callbacks': [...]} 配置自定义 Handler")
    print("─" * 60)
    result = chain.invoke(
        {"question": "用一句话解释什么是 LangChain？"},
        config={"callbacks": [custom_handler]},
    )
    print(f"\n最终回答：{result}")

    # ── 演示2：使用 .with_config() 绑定 Callback ──
    print("\n\n" + "─" * 60)
    print("演示2：使用 .with_config(callbacks=[...]) 绑定 Handler")
    print("─" * 60)
    chain_with_cb = chain.with_config(callbacks=[custom_handler])
    # 之后调用无需再传 callbacks
    result = chain_with_cb.invoke({"question": "LCEL 是什么？"})
    print(f"\n最终回答：{result}")

    # ── 演示3：同时使用多个 Handler（自定义 + 内置） ──
    print("\n\n" + "─" * 60)
    print("演示3：同时使用自定义 Handler + StdOutCallbackHandler")
    print("─" * 60)
    result = chain.invoke(
        {"question": "什么是 Memory？"},
        config={"callbacks": [custom_handler, stdout_handler]},
    )
    print(f"\n最终回答：{result}")

    print("\n" + "=" * 60)
    print("✅ 自定义 Callback Handler 演示完成")
    print("要点：")
    print("  1. 继承 BaseCallbackHandler，重写需要的 on_xxx 方法")
    print("  2. run_id 用于关联同一次执行的多个阶段")
    print("  3. config={'callbacks': [...]} 是最常用的配置方式")
    print("  4. 可同时挂多个 Handler（如自定义日志 + 内置 StdOut）")
    print("=" * 60)


if __name__ == "__main__":
    main()
