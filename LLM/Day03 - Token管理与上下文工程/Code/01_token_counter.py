# 文件用途：Token 计数工具
# 用 tiktoken 实现通用 Token 计数器 TokenCounter：
#   - 支持多模型 encoding（GPT-4o / GPT-3.5 / GPT-4 等不同编码器）
#   - 统计文本 / 对话消息列表的 Token 数
#   - 中文 / 英文 / 代码 Token 效率对比
#   - Token 消耗可视化（柱状图数据）
# 依赖：pip install tiktoken
# 本地分词，不需要 API Key。

import sys

try:
    import tiktoken
except ImportError:
    print("缺少依赖 tiktoken，请执行: pip install tiktoken")
    sys.exit(1)


class TokenCounter:
    """通用 Token 计数器，支持多模型编码器。"""

    # 模型 -> 编码器名称 映射
    MODEL_ENCODINGS = {
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
    }

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        encoding_name = self.MODEL_ENCODINGS.get(model, "cl100k_base")
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding(encoding_name)

    # ---- 文本 Token 计数 ----
    def count(self, text: str) -> int:
        """统计一段文本的 Token 数。"""
        return len(self.encoding.encode(text))

    def count_batch(self, texts: list[str]) -> list[int]:
        """批量统计多段文本。"""
        return [len(ids) for ids in self.encoding.encode_batch(texts)]

    def encode(self, text: str) -> list[int]:
        return self.encoding.encode(text)

    def decode(self, token_ids: list[int]) -> str:
        return self.encoding.decode(token_ids)

    # ---- 对话消息 Token 计数 ----
    def count_messages(self, messages: list[dict], model: str | None = None) -> int:
        """
        统计对话消息列表的 Token 数（近似估算，参考 OpenAI 官方算法）。
        每条消息大致消耗：role 标记 + content + 固定开销。
        注意：这是近似值，实际计费以 API 返回 usage 为准。
        """
        if model is None:
            model = self.model
        # 不同编码器每条消息的固定开销不同
        tokens_per_message = 3 if "gpt-4" in model or "gpt-3.5" in model else 3
        tokens_per_name = 1  # 带 name 字段时额外开销

        total = 0
        for msg in messages:
            total += tokens_per_message
            for key, value in msg.items():
                total += self.count(str(value))
                if key == "name":
                    total += tokens_per_name
        total += 3  # 每轮对话末尾的 assistant 引导开销
        return total


def demo_text_count(counter: TokenCounter) -> None:
    print("=" * 60)
    print("1. 文本 Token 计数")
    print("=" * 60)
    samples = [
        "Hello, how are you today?",
        "你好，今天过得怎么样？",
        "def hello():\n    print('hi')\n    return 0",
    ]
    for text in samples:
        n = counter.count(text)
        print(f"  [{len(text)}字符] {text[:30]!r}  -> {n} tokens")


def demo_message_count(counter: TokenCounter) -> None:
    print("\n" + "=" * 60)
    print("2. 对话消息 Token 计数")
    print("=" * 60)
    messages = [
        {"role": "system", "content": "你是一个有用的助手。"},
        {"role": "user", "content": "什么是大语言模型？"},
        {"role": "assistant", "content": "大语言模型是基于 Transformer 的大规模神经网络。"},
        {"role": "user", "content": "它和传统 NLP 有什么区别？"},
    ]
    total = counter.count_messages(messages)
    print(f"  4 条消息对话，近似总 Token 数: {total}")
    print("  （实际计费以 API 返回 usage 为准）")


def demo_efficiency(counter: TokenCounter) -> None:
    print("\n" + "=" * 60)
    print("3. 中文/英文/代码 Token 效率对比")
    print("=" * 60)
    datasets = {
        "英文": ("The quick brown fox jumps over the lazy dog. "
                "Natural language processing is a fascinating field."),
        "中文": "敏捷的棕色狐狸跳过了懒狗。自然语言处理是一个非常有趣的领域，"
                "也是大语言模型的重要基础。",
        "代码": "def fibonacci(n):\n    if n < 2:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    }
    print(f"  {'类型':<6}{'字符数':<8}{'Token数':<10}{'字符/Token':<12}{'Token/百字'}")
    print("  " + "-" * 50)
    for lang, text in datasets.items():
        chars = len(text)
        toks = counter.count(text)
        print(f"  {lang:<6}{chars:<8}{toks:<10}{chars/toks:<12.2f}{toks/chars*100:.1f}")
    print("\n  结论：中文相同语义消耗的 Token 明显多于英文，成本更高。")


def demo_visualization(counter: TokenCounter) -> None:
    print("\n" + "=" * 60)
    print("4. Token 消耗可视化（可复制到图表工具）")
    print("=" * 60)
    # 模拟一段对话从 1 轮增长到 10 轮的 Token 消耗
    base_turn = "用户：请解释一下向量数据库的原理。\n助手：向量数据库存储高维向量并支持近似最近邻搜索。"
    print("  对话轮数 -> Token 数（柱状图，每个 █ ≈ 50 tokens）")
    for turns in range(1, 11):
        text = base_turn * turns
        n = counter.count(text)
        bar = "█" * (n // 50)
        print(f"  {turns:>2} 轮: {n:>5} {bar}")
    print("\n  可见对话越长，每次请求重复发送的 Token 线性增长，成本也随之上升。")


def main() -> None:
    counter = TokenCounter(model="gpt-4o")
    print(f"使用编码器: {counter.encoding.name} (对应模型: {counter.model})\n")
    demo_text_count(counter)
    demo_message_count(counter)
    demo_efficiency(counter)
    demo_visualization(counter)


if __name__ == "__main__":
    main()
