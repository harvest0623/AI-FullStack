# 文件用途：流式输出实现
# StreamingClient 类：封装 OpenAI 同步流式 + 异步流式 + Anthropic 流式调用。
# 实现打字机效果输出，含流中断处理。展示三种流式调用方式。
# 运行前：pip install openai anthropic python-dotenv；在 .env 配置 API Key

from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import AsyncIterator, Iterator

from dotenv import load_dotenv

load_dotenv()


class StreamingClient:
    """
    流式输出客户端封装。

    使用方式：
        client = StreamingClient()
        client.stream_openai_sync("讲个笑话", typewriter=True)
        asyncio.run(client.stream_openai_async("讲个笑话"))
        client.stream_anthropic("讲个笑话")
    """

    def __init__(self) -> None:
        self._openai_sync = None
        self._openai_async = None
        self._anthropic = None

    # ------------------------- 客户端懒加载 -------------------------
    def _get_openai_sync(self):
        if self._openai_sync is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY")
            self._openai_sync = OpenAI(api_key=api_key)
        return self._openai_sync

    def _get_openai_async(self):
        if self._openai_async is None:
            from openai import AsyncOpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY")
            self._openai_async = AsyncOpenAI(api_key=api_key)
        return self._openai_async

    def _get_anthropic(self):
        if self._anthropic is None:
            import anthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 ANTHROPIC_API_KEY")
            self._anthropic = anthropic.Anthropic(api_key=api_key)
        return self._anthropic

    # ------------------------- OpenAI 同步流式 -------------------------
    def stream_openai_sync(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        typewriter: bool = False,
        char_delay: float = 0.03,
    ) -> str:
        """
        OpenAI 同步流式输出。
        typewriter=True 时启用打字机效果（逐字延迟）。
        返回完整文本。
        """
        client = self._get_openai_sync()
        chunks: list[str] = []
        first_token = False
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=True,
                stream_options={"include_usage": True},
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    if not first_token:
                        first_token = True
                        # 清除"正在思考..."提示
                        sys.stdout.write("\r" + " " * 20 + "\r")
                    chunks.append(delta)
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                    if typewriter:
                        time.sleep(char_delay)
            sys.stdout.write("\n")
        except Exception as exc:  # noqa: BLE001
            sys.stdout.write(f"\n[流式中断] {type(exc).__name__}: {exc}\n")
        return "".join(chunks)

    # ------------------------- OpenAI 异步流式 -------------------------
    async def stream_openai_async(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
    ) -> str:
        """OpenAI 异步流式输出。"""
        client = self._get_openai_async()
        chunks: list[str] = []
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    chunks.append(delta)
                    sys.stdout.write(delta)
                    sys.stdout.flush()
            sys.stdout.write("\n")
        except Exception as exc:  # noqa: BLE001
            sys.stdout.write(f"\n[流式中断] {type(exc).__name__}: {exc}\n")
        return "".join(chunks)

    # ------------------------- Anthropic 流式 -------------------------
    def stream_anthropic(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20240620",
    ) -> str:
        """Anthropic Claude 流式输出。"""
        client = self._get_anthropic()
        chunks: list[str] = []
        try:
            with client.messages.stream(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    chunks.append(text)
                    sys.stdout.write(text)
                    sys.stdout.flush()
            sys.stdout.write("\n")
        except Exception as exc:  # noqa: BLE001
            sys.stdout.write(f"\n[流式中断] {type(exc).__name__}: {exc}\n")
        return "".join(chunks)

    # ------------------------- 流式迭代器（供上层消费） -------------------------
    def iter_openai_stream(self, prompt: str, model: str = "gpt-4o-mini") -> Iterator[str]:
        """以生成器形式产出增量文本，便于上层自定义处理。"""
        client = self._get_openai_sync()
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo_sync() -> None:
    print("=" * 60)
    print("演示 1：OpenAI 同步流式（打字机效果）")
    print("=" * 60)
    client = StreamingClient()
    sys.stdout.write("正在思考...")
    sys.stdout.flush()
    text = client.stream_openai_sync("用 50 字解释什么是 RAG", typewriter=True)
    print(f"\n（完整文本共 {len(text)} 字）")


async def demo_async() -> None:
    print("\n" + "=" * 60)
    print("演示 2：OpenAI 异步流式")
    print("=" * 60)
    client = StreamingClient()
    text = await client.stream_openai_async("用一句话解释什么是 Embedding")
    print(f"（完整文本共 {len(text)} 字）")


def demo_anthropic() -> None:
    print("\n" + "=" * 60)
    print("演示 3：Anthropic 流式")
    print("=" * 60)
    client = StreamingClient()
    text = client.stream_anthropic("用一句话解释什么是 Token")
    print(f"（完整文本共 {len(text)} 字）")


def demo_iterator() -> None:
    print("\n" + "=" * 60)
    print("演示 4：流式迭代器（自定义处理）")
    print("=" * 60)
    client = StreamingClient()
    count = 0
    for delta in client.iter_openai_stream("数 1 到 5"):
        count += 1
        print(f"[chunk {count}] {delta!r}")
    print(f"共收到 {count} 个 chunk")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY")
        return

    demo_sync()
    asyncio.run(demo_async())
    demo_iterator()

    if os.getenv("ANTHROPIC_API_KEY"):
        demo_anthropic()
    else:
        print("\n[跳过] 未配置 ANTHROPIC_API_KEY")


if __name__ == "__main__":
    main()
