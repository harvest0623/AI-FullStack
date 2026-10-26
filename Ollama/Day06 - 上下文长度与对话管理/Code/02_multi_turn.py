# -*- coding: utf-8 -*-
"""
Day06 - 02 多轮对话历史构建

演示 messages 如何按顺序累加，让模型"记住"前面说过的话：
1. system 定位角色
2. 连续 user/assistant 回合
3. 每次新提问都带上全部历史

双模式：有 Ollama -> 真实模型记住上下文；无 -> 模拟展示消息结构。
"""

from ollama_util import chat_wrapper


def demo_messages():
    """构建一次完整的多轮 messages，观察结构"""
    messages = [
        {"role": "system", "content": "你是客服小O，回答简短、友好。"},
        {"role": "user", "content": "我叫小张。"},
        {"role": "assistant", "content": "你好小张！有什么可以帮你？"},
        {"role": "user", "content": "我刚买的水杯不保温。我要怎么办？"},
    ]
    print("当前 messages（共 %d 条）：" % len(messages))
    for m in messages:
        print(f"  [{m['role']:<9}] {m['content']}")
    return messages


def append_round(messages, role: str, content: str):
    messages.append({"role": role, "content": content})


def main():
    print(">> 多轮对话历史构建\n")
    messages = demo_messages()

    print("\n下一轮问答：")
    append_round(messages, "assistant", "抱歉！请提供商品订单号，我来帮你排查。")
    mixed = input("（模拟用户继续：）") if False else "订单号是 2026-0901-007，谢谢。"
    append_round(messages, "user", mixed)

    print("\n最新 messages：")
    for m in messages:
        print(f"  [{m['role']:<9}] {m['content']}")

    print("\n真实模型验证（有环境时）：")
    answer = chat_wrapper("llama3.1", messages, verbose=True)
    print(f"  模型回答：{answer}")

    print("\n  tips: 上下文就在这些消息里；不带历史 = 每次都「失忆」。")


if __name__ == "__main__":
    main()