# 文件用途：上下文窗口管理器
# ContextManager 类：管理对话历史的 Token 消耗，
#   - 自动截断超出窗口的旧消息
#   - 支持三种策略：截断(truncate) / 摘要(summary) / 滑动窗口(sliding)
#   - 含 Token 预算管理：设定 max_tokens 预算，超出时自动压缩
# 摘要策略需要调用 LLM API（可选，未配置 Key 时回退为截断）。
# 依赖：pip install tiktoken python-dotenv openai
# 体现 AISearch 项目 core/ 中「上下文管理」的封装思想。

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


@dataclass
class ContextManager:
    """
    上下文窗口管理器。
    策略：
      - truncate: 直接丢弃最早的旧消息
      - sliding:  只保留最近 K 轮对话
      - summary:  将旧消息压缩为一条摘要消息
    """
    max_tokens: int = 4000               # 上下文 Token 预算
    strategy: str = "truncate"           # truncate / sliding / summary
    keep_recent_turns: int = 4           # sliding 策略保留的最近轮数
    encoding_model: str = "gpt-4o"       # 用于 Token 计数的编码器
    messages: list[dict] = field(default_factory=list)
    _encoding: object = field(default=None, repr=False)

    def __post_init__(self):
        try:
            self._encoding = tiktoken.encoding_for_model(self.encoding_model)
        except KeyError:
            self._encoding = tiktoken.get_encoding("cl100k_base")

    # ---------- Token 计数 ----------
    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    def count_message_tokens(self, msg: dict) -> int:
        # 近似：3（开销） + content token
        return 3 + self.count_tokens(str(msg.get("content", "")))

    def total_tokens(self) -> int:
        return sum(self.count_message_tokens(m) for m in self.messages)

    # ---------- 消息管理 ----------
    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self._maybe_compress()

    def add_user(self, content: str) -> None:
        self.add_message("user", content)

    def add_assistant(self, content: str) -> None:
        self.add_message("assistant", content)

    def get_messages(self) -> list[dict]:
        """返回当前可用于 API 调用的消息列表。"""
        return list(self.messages)

    # ---------- 压缩策略 ----------
    def _maybe_compress(self) -> None:
        if self.total_tokens() <= self.max_tokens:
            return
        if self.strategy == "truncate":
            self._truncate()
        elif self.strategy == "sliding":
            self._sliding()
        elif self.strategy == "summary":
            self._summary()

    def _truncate(self) -> None:
        """从最早的消息开始丢弃，直到满足预算。"""
        while self.messages and self.total_tokens() > self.max_tokens:
            removed = self.messages.pop(0)
            print(f"  [truncate] 丢弃旧消息: {removed['content'][:20]}...")

    def _sliding(self) -> None:
        """只保留最近 keep_recent_turns 轮（每轮=user+assistant=2条）。"""
        keep = self.keep_recent_turns * 2
        if len(self.messages) > keep:
            removed = len(self.messages) - keep
            self.messages = self.messages[-keep:]
            print(f"  [sliding] 滑动窗口，丢弃 {removed} 条旧消息")
        # 若仍超预算，继续截断
        while self.messages and self.total_tokens() > self.max_tokens:
            self.messages.pop(0)

    def _summary(self) -> None:
        """将旧消息压缩为一条 system 摘要。保留最近的若干条原文。"""
        if len(self.messages) <= 2:
            return
        # 保留最近 2 条，其余压缩
        to_summarize = self.messages[:-2]
        recent = self.messages[-2:]
        summary_text = self._summarize_with_llm(to_summarize)
        summary_msg = {
            "role": "system",
            "content": f"[历史对话摘要] {summary_text}",
        }
        self.messages = [summary_msg] + recent
        print(f"  [summary] 将 {len(to_summarize)} 条旧消息压缩为 1 条摘要")

    def _summarize_with_llm(self, msgs: list[dict]) -> str:
        """
        用 LLM 对旧对话生成摘要。若未配置 Key，回退为简单拼接截断。
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # 回退：取每条消息前 30 字拼接
            joined = " | ".join(m["content"][:30] for m in msgs)
            return joined[:500] + "...(无LLM回退摘要)"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            dialog = "\n".join(f"{m['role']}: {m['content']}" for m in msgs)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "请把以下对话压缩为一段不超过 150 字的摘要，保留关键信息。"},
                    {"role": "user", "content": dialog},
                ],
                max_tokens=256,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            return f"(摘要失败回退: {e})"


def demo() -> None:
    print("=" * 60)
    print("上下文窗口管理器演示")
    print("=" * 60)

    # 模拟一个会不断超预算的对话
    fake_turns = [
        ("user", "我想了解机器学习的基础概念，能从监督学习开始讲吗？"),
        ("assistant", "监督学习是用带标签的数据训练模型，让它学会从输入预测输出。"),
        ("user", "那无监督学习呢？它和监督学习最大的区别是什么？"),
        ("assistant", "无监督学习用无标签数据，目标是发现数据内在结构，如聚类。"),
        ("user", "强化学习又是怎么回事？它适合解决什么问题？"),
        ("assistant", "强化学习通过试错与奖励信号学习策略，适合决策与控制类问题。"),
        ("user", "深度学习和它们是什么关系？是用神经网络吗？"),
        ("assistant", "深度学习是用多层神经网络做表示学习，可结合监督/无监督/强化。"),
    ]

    for strategy in ["truncate", "sliding", "summary"]:
        print(f"\n--- 策略: {strategy} ---")
        cm = ContextManager(max_tokens=300, strategy=strategy, keep_recent_turns=2)
        for role, content in fake_turns:
            cm.add_message(role, content)
        print(f"  最终消息数: {len(cm.messages)}，总 Token: {cm.total_tokens()}")
        print(f"  最后一条: {cm.messages[-1]['content'][:40]}...")


if __name__ == "__main__":
    demo()
