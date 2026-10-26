# -*- coding: utf-8 -*-
"""
Day06 - 04 历史裁剪与摘要

当整体上下文超过 num_ctx 时：
1. 裁剪：丢弃最早的历史回合，只保留最近 N 轮（滑动窗口）
2. 摘要：用一句简短摘要压缩被丢弃的旧内容，兼顾"记忆"与"长度"
3. 综合的"窗口感知对话器"

结构贴近真实设计，无环境也能完整观察逻辑。
"""

from ollama_util import chat_wrapper

APPROX_TOKEN_PER_CHAR = 1.0


def est_tokens(text: str) -> int:
    return max(1, int(len(text) * APPROX_TOKEN_PER_CHAR))


def trim_history(messages: list[dict], keep_rounds: int = 3) -> list[dict]:
    """
    滑动窗口裁剪：保留 system + 最近 keep_rounds 轮（含 user/assistant 对）。
    """
    if keep_rounds <= 0:
        return messages[:1]  # 只留 system
    sys_msg = messages[:1]
    rounds = messages[1:]
    # 每轮是 user+assistant 两条；取最后 keep_rounds*2 条
    tail = rounds[-(keep_rounds * 2):] if len(rounds) > keep_rounds * 2 else rounds
    return sys_msg + tail


def summarize(dropped: list[dict]) -> str:
    """把被丢弃的历史压成一句摘要（这里用规则拼接，教育演示）"""
    user_items = [m["content"] for m in dropped if m.get("role") == "user"]
    if not user_items:
        return ""
    short = "；".join(u[:12] + ("…" if len(u) > 12 else "") for u in user_items)
    return f"（历史摘要：用户曾和小O讨论过：{short}）"


# ---- 构造 6 轮对话，模拟长对话 ----
def build_long_history() -> list[dict]:
    msgs = [{"role": "system", "content": "你是客服小O。"}]
    for i in range(6):
        msgs.append({"role": "user", "content": f"第{i+1}个问题：我的订单状态是什么？"})
        msgs.append({"role": "assistant", "content": f"第{i+1}次回答：在处理中，请稍候~"})
    return msgs


def used_tokens(msgs: list[dict]) -> int:
    return sum(est_tokens(m["content"]) for m in msgs)


def main():
    print(">> 历史裁剪与摘要\n")
    full = build_long_history()
    print(f"完整历史：{len(full)} 条，占 {used_tokens(full)} token")

    # 演示 1：裁剪
    print("\n一、滑动窗口裁剪（保留最近 3 轮）")
    trimmed = trim_history(full, keep_rounds=3)
    print(f"裁剪后：{len(trimmed)} 条，占 {used_tokens(trimmed)} token")
    for m in trimmed:
        print(f"  [{m['role']:<9}] {m['content']}")

    # 演示 2：摘要压缩被裁部分
    print("\n二、用摘要代替被裁的旧历史")
    dropped = full[1:-6] if len(full) > 6 else []
    summary = summarize(dropped)
    compact = [trimmed[0],
               {"role": "system", "content": summary},
               *trimmed[1:]]
    total = used_tokens(compact)
    print(f"  摘要内容：{summary}")
    print(f"  摘要+滑动窗口后：{len(compact)} 条，占 {total} token")
    print(f"  相比完整历史已省 {used_tokens(full) - total} token")

    # 演示 3：真实会话（带裁剪后 send）
    print("\n三、把裁剪后的历史真正发给模型（有环境时）")
    reply = chat_wrapper("llama3.1", compact, verbose=True)
    print(f"  模型以裁剪后的历史作答：{reply}")

    print("\n  tips: 重要信息会因裁剪丢失 → 用「摘要」或单独记忆来兜底")


if __name__ == "__main__":
    main()