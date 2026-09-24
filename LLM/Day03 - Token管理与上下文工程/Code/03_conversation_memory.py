# 文件用途：对话历史管理
# ConversationMemory 类：实现三种对话历史管理策略并对比
#   - full:    全量保留（简单但 Token 线性增长）
#   - summary: 摘要压缩（每 N 轮摘要一次旧对话）
#   - sliding: 滑动窗口（只保留最近 K 轮）
# 摘要策略用 LLM API 自动摘要旧对话（未配置 Key 时回退为截断）。
# 含性能对比：Token 消耗 / 信息保留率。
# 依赖：pip install tiktoken python-dotenv openai
# 体现 AISearch 项目 core/ 中「对话管理」的封装思想。

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
except ImportError:
    raise RuntimeError("缺少依赖 python-dotenv，请执行: pip install python-dotenv")

try:
    import tiktoken
except ImportError:
    raise RuntimeError("缺少依赖 tiktoken，请执行: pip install tiktoken")

load_dotenv()


def _get_encoding(model: str = "gpt-4o"):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _llm_summarize(dialog: str) -> str:
    """用 LLM 摘要旧对话；未配置 Key 时回退为简单截断。"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return f"(回退摘要) {dialog[:120]}..."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "把以下对话压缩成不超过 120 字的摘要，保留关键事实。"},
                {"role": "user", "content": dialog},
            ],
            max_tokens=256,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:  # noqa: BLE001
        return f"(摘要失败) {dialog[:80]}... 原因: {e}"


@dataclass
class ConversationMemory:
    """
    对话历史管理器，支持三种策略。

    strategy:
      - full:    全量保留
      - summary: 每 summary_every 轮把旧对话压缩为一条摘要
      - sliding: 只保留最近 keep_turns 轮
    """
    strategy: str = "full"
    keep_turns: int = 3           # sliding 保留轮数
    summary_every: int = 4        # summary 每 N 轮触发一次
    encoding: object = field(default_factory=lambda: _get_encoding(), repr=False)

    messages: list[dict] = field(default_factory=list)
    _turn_count: int = 0

    def add_turn(self, user: str, assistant: str) -> None:
        """添加一轮对话（user + assistant）。"""
        self.messages.append({"role": "user", "content": user})
        self.messages.append({"role": "assistant", "content": assistant})
        self._turn_count += 1
        if self.strategy == "sliding":
            self._apply_sliding()
        elif self.strategy == "summary":
            if self._turn_count % self.summary_every == 0:
                self._apply_summary()

    def _apply_sliding(self) -> None:
        keep = self.keep_turns * 2
        if len(self.messages) > keep:
            self.messages = self.messages[-keep:]

    def _apply_summary(self) -> None:
        # 保留最近 2 条，其余压缩
        if len(self.messages) <= 2:
            return
        old = self.messages[:-2]
        recent = self.messages[-2:]
        dialog = "\n".join(f"{m['role']}: {m['content']}" for m in old)
        summary = _llm_summarize(dialog)
        self.messages = [
            {"role": "system", "content": f"[历史摘要] {summary}"}
        ] + recent

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def total_tokens(self) -> int:
        total = 0
        for m in self.messages:
            total += 3 + len(self.encoding.encode(str(m["content"])))
        return total

    def info(self) -> dict:
        return {
            "strategy": self.strategy,
            "turns": self._turn_count,
            "messages": len(self.messages),
            "tokens": self.total_tokens(),
        }


def run_demo(strategy: str, turns: list[tuple[str, str]]) -> dict:
    print(f"\n--- 策略: {strategy} ---")
    mem = ConversationMemory(strategy=strategy, keep_turns=2, summary_every=3)
    for i, (u, a) in enumerate(turns, 1):
        mem.add_turn(u, a)
        info = mem.info()
        print(f"  第{i}轮后: 消息数={info['messages']}, tokens={info['tokens']}")
    return mem.info()


def compare_strategies() -> None:
    """对比三种策略的 Token 消耗与信息保留。"""
    print("\n" + "=" * 60)
    print("三种策略性能对比")
    print("=" * 60)
    # 模拟 6 轮对话
    turns = [
        ("我叫张三，是一名后端工程师。", "你好张三，很高兴认识你。"),
        ("我主要用 Python 和 Go。", "Python 适合快速开发，Go 适合高并发服务。"),
        ("我想学 LLM 应用开发。", "建议从 API 调用、Prompt 工程开始。"),
        ("Token 是什么意思？", "Token 是 LLM 处理文本的最小单位。"),
        ("如何控制成本？", "管理上下文窗口、复用缓存、选合适模型。"),
        ("RAG 是什么？", "RAG 是检索增强生成，结合检索与大模型。"),
    ]

    results = {}
    for strategy in ["full", "sliding", "summary"]:
        results[strategy] = run_demo(strategy, turns)

    print("\n" + "-" * 50)
    print(f"{'策略':<10}{'消息数':<8}{'Token数':<10}{'信息保留'}")
    print("-" * 50)
    info_keep = {"full": "100%", "sliding": "仅近期", "summary": "摘要+近期"}
    for s, r in results.items():
        print(f"{s:<10}{r['messages']:<8}{r['tokens']:<10}{info_keep[s]}")

    print("\n结论：")
    print("- full:     Token 线性增长，适合短对话，长对话成本高")
    print("- sliding:  Token 恒定，但丢失早期信息，适合无状态问答")
    print("- summary:  Token 受控且保留关键信息，适合长对话助手（推荐）")


def main() -> None:
    print("=" * 60)
    print("对话历史管理 ConversationMemory 演示")
    print("=" * 60)
    print("说明：summary 策略默认调用 LLM 摘要；未配置 OPENAI_API_KEY 时自动回退为截断。")
    compare_strategies()


if __name__ == "__main__":
    main()
