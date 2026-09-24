# 文件用途：多模型统一客户端
# 定义抽象基类 LLMClient，并实现 OpenAIClient / AnthropicClient / DashScopeClient 三个子类，
# 对外暴露统一的 chat() 接口。同时支持「模型路由」：根据任务类型自动选择合适的模型。
# 这样上层业务代码只依赖统一接口，切换模型只需改配置，符合 AISearch 项目 clients/ 的封装思想。
# 依赖：pip install openai anthropic python-dotenv

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
except ImportError:
    raise RuntimeError("缺少依赖 python-dotenv，请执行: pip install python-dotenv")

try:
    from openai import OpenAI
except ImportError:
    raise RuntimeError("缺少依赖 openai，请执行: pip install openai")

load_dotenv()


# ============================================================
# 统一数据结构
# ============================================================
@dataclass
class Message:
    """统一的对话消息结构。"""
    role: str  # system / user / assistant
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResult:
    """统一的调用返回结构。"""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    raw: object = None  # 原始响应对象，便于调试


# ============================================================
# 抽象基类 LLMClient
# ============================================================
class LLMClient(ABC):
    """所有 LLM 客户端的抽象基类，定义统一接口。"""

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def chat(self, messages: list[Message], temperature: float = 0.7,
             max_tokens: int | None = None) -> ChatResult:
        """统一的对话接口，子类必须实现。"""
        ...

    def chat_simple(self, prompt: str, system: str | None = None,
                    temperature: float = 0.7) -> str:
        """便捷方法：单轮提问直接返回文本。"""
        msgs = []
        if system:
            msgs.append(Message("system", system))
        msgs.append(Message("user", prompt))
        return self.chat(msgs, temperature=temperature).content


# ============================================================
# OpenAI 客户端
# ============================================================
class OpenAIClient(LLMClient):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None,
                 base_url: str | None = None):
        super().__init__(model)
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("未配置 OPENAI_API_KEY")
        self.client = OpenAI(api_key=key, base_url=base_url or os.getenv("OPENAI_BASE_URL"))

    def chat(self, messages: list[Message], temperature: float = 0.7,
             max_tokens: int | None = None) -> ChatResult:
        kwargs = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        resp = self.client.chat.completions.create(**kwargs)
        return ChatResult(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            raw=resp,
        )


# ============================================================
# Anthropic Claude 客户端
# ============================================================
class AnthropicClient(LLMClient):
    def __init__(self, model: str = "claude-3-5-sonnet-20241022",
                 api_key: str | None = None):
        super().__init__(model)
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("缺少依赖 anthropic，请执行: pip install anthropic")
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("未配置 ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=key)

    def chat(self, messages: list[Message], temperature: float = 0.7,
             max_tokens: int | None = None) -> ChatResult:
        # Claude：system 提取为顶级参数，max_tokens 必填
        system_text = ""
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_text += m.content + "\n"
            else:
                chat_msgs.append(m.to_dict())
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 1024,  # Claude 必填
            system=system_text.strip() or "You are a helpful assistant.",
            messages=chat_msgs,
            temperature=temperature,
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return ChatResult(
            content=text,
            model=self.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            raw=resp,
        )


# ============================================================
# 通义千问 DashScope 客户端（兼容 OpenAI 格式）
# ============================================================
class DashScopeClient(LLMClient):
    def __init__(self, model: str = "qwen-plus", api_key: str | None = None):
        super().__init__(model)
        key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not key:
            raise RuntimeError("未配置 DASHSCOPE_API_KEY")
        self.client = OpenAI(
            api_key=key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def chat(self, messages: list[Message], temperature: float = 0.7,
             max_tokens: int | None = None) -> ChatResult:
        kwargs = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        resp = self.client.chat.completions.create(**kwargs)
        return ChatResult(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            raw=resp,
        )


# ============================================================
# 模型路由器：根据任务类型选择模型
# ============================================================
@dataclass
class ModelRouter:
    """
    根据任务类型路由到不同模型，实现「按需选模型」。
    - 简单/高频任务 -> 用便宜快速的模型
    - 复杂推理任务 -> 用旗舰模型
    - 中文任务     -> 用中文强的模型
    """
    clients: dict[str, LLMClient] = field(default_factory=dict)

    def register(self, task_type: str, client: LLMClient) -> None:
        self.clients[task_type] = client

    def chat(self, task_type: str, messages: list[Message], **kwargs) -> ChatResult:
        client = self.clients.get(task_type)
        if not client:
            raise ValueError(f"未注册任务类型: {task_type}，已注册: {list(self.clients)}")
        return client.chat(messages, **kwargs)


def demo() -> None:
    print("=" * 60)
    print("多模型统一客户端演示")
    print("=" * 60)

    # 注意：以下客户端在缺少对应 Key 时会抛错，
    # 实际使用时按需启用你已配置 Key 的客户端。
    available: list[LLMClient] = []

    if os.getenv("OPENAI_API_KEY"):
        available.append(OpenAIClient(model="gpt-4o-mini"))
    if os.getenv("ANTHROPIC_API_KEY"):
        available.append(AnthropicClient())
    if os.getenv("DASHSCOPE_API_KEY"):
        available.append(DashScopeClient())

    if not available:
        print("⚠️ 未检测到任何 API Key，请先在 .env 配置至少一个模型的 Key。")
        print("   示例：")
        print("   OPENAI_API_KEY=sk-xxx")
        print("   ANTHROPIC_API_KEY=sk-ant-xxx")
        print("   DASHSCOPE_API_KEY=sk-xxx")
        return

    prompt = "用一句话解释什么是 Embedding。"
    for client in available:
        print(f"\n--- {client.__class__.__name__} (model={client.model}) ---")
        try:
            result = client.chat_simple(prompt, system="你是简洁的技术助手。")
            print(f"回复: {result}")
        except Exception as e:  # noqa: BLE001
            print(f"调用失败: {e}")

    # 演示模型路由
    print("\n" + "=" * 60)
    print("模型路由演示")
    print("=" * 60)
    router = ModelRouter()
    # 简单任务用便宜模型，复杂任务用旗舰模型
    for c in available:
        name = c.__class__.__name__
        if "OpenAI" in name and c.model == "gpt-4o-mini":
            router.register("simple", c)         # 简单任务
        elif "Anthropic" in name:
            router.register("complex", c)        # 复杂推理
        elif "DashScope" in name:
            router.register("chinese", c)        # 中文任务

    for task in ["simple", "complex", "chinese"]:
        if task in router.clients:
            print(f"\n任务类型 [{task}] -> 路由到 {router.clients[task].__class__.__name__}")
            try:
                r = router.chat(task, [Message("user", prompt)])
                print(f"回复: {r.content}")
            except Exception as e:  # noqa: BLE001
                print(f"调用失败: {e}")


if __name__ == "__main__":
    demo()
