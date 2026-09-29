# 文件用途：Ollama 本地调用演示
# 封装 OllamaClient 类，支持对话调用、流式输出、多模型切换、模型管理功能
# 通过 OpenAI SDK 连接 Ollama 本地服务（base_url 指向 localhost:11434）
# Python 3.10+ 可运行，需先安装 ollama 并启动服务：ollama serve
# 依赖：pip install openai

from __future__ import annotations

import os
import time
from typing import Any, Iterator

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


class OllamaClient:
    """Ollama 本地模型客户端，基于 OpenAI SDK 兼容协议调用。"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        default_model: str = "qwen2.5:7b",
    ) -> None:
        if OpenAI is None:
            raise ImportError(
                "未安装 openai 包，请执行: pip install openai"
            )
        self.base_url = base_url
        self.api_key = api_key
        self.default_model = default_model
        # 兼容通过环境变量覆盖配置
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url)
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def check_service(self) -> bool:
        """检查 Ollama 服务是否可用。"""
        try:
            self.client.models.list()
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[OllamaClient] 服务连接失败: {exc}")
            return False

    def list_models(self) -> list[str]:
        """列出本地已安装的模型。"""
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as exc:  # noqa: BLE001
            print(f"[OllamaClient] 获取模型列表失败: {exc}")
            return []

    def chat(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """同步对话调用，返回完整文本。"""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        target_model = model or self.default_model
        start = time.time()
        response = self.client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = time.time() - start
        content = response.choices[0].message.content or ""
        usage = response.usage
        print(
            f"[OllamaClient] 模型={target_model} 耗时={elapsed:.2f}s "
            f"tokens={getattr(usage, 'total_tokens', 'N/A')}"
        )
        return content

    def stream_chat(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """流式对话调用，逐 token 返回。"""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        target_model = model or self.default_model
        stream = self.client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def switch_model(self, model: str) -> "OllamaClient":
        """切换默认模型，支持链式调用。"""
        self.default_model = model
        print(f"[OllamaClient] 已切换默认模型为: {model}")
        return self

    def compare_models(
        self,
        prompt: str,
        models: list[str],
        system: str | None = None,
    ) -> list[dict[str, Any]]:
        """对同一问题在多个模型上对比回答。"""
        results: list[dict[str, Any]] = []
        for model in models:
            start = time.time()
            try:
                answer = self.chat(prompt, model=model, system=system)
                elapsed = time.time() - start
                results.append(
                    {
                        "model": model,
                        "answer": answer,
                        "latency": round(elapsed, 2),
                        "status": "success",
                    }
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "model": model,
                        "answer": "",
                        "latency": round(time.time() - start, 2),
                        "status": f"error: {exc}",
                    }
                )
        return results


def demo_ollama() -> None:
    """演示 OllamaClient 的典型用法。"""
    client = OllamaClient(default_model="qwen2.5:7b")

    # 1. 环境检查
    if not client.check_service():
        print("请先启动 Ollama 服务: ollama serve")
        print("并拉取模型: ollama pull qwen2.5:7b")
        return

    # 2. 列出可用模型
    print("\n=== 本地模型列表 ===")
    models = client.list_models()
    for m in models:
        print(f"  - {m}")

    if not models:
        print("本地暂无模型，请先执行: ollama pull qwen2.5:7b")
        return

    # 3. 普通对话
    print("\n=== 普通对话 ===")
    answer = client.chat(
        prompt="用一句话解释什么是大语言模型。",
        system="你是一个专业的中文技术助手，回答简洁。",
    )
    print(answer)

    # 4. 流式输出
    print("\n=== 流式输出 ===")
    for token in client.stream_chat(prompt="写一首关于秋天的两行小诗。"):
        print(token, end="", flush=True)
    print()

    # 5. 多模型对比
    if len(models) >= 2:
        print("\n=== 多模型对比 ===")
        results = client.compare_models(
            prompt="什么是 PagedAttention？",
            models=models[:2],
        )
        for r in results:
            print(f"\n[模型: {r['model']}] 耗时={r['latency']}s")
            print(r["answer"][:200])


if __name__ == "__main__":
    demo_ollama()
