# -*- coding: utf-8 -*-
"""
Day01 - 03 快速对话：第一句"本地模型回答"

演示统一的双模式骨架：
  有 Ollama + 模型 -> 真实 API
  无环境          -> SimOllama 模拟

首次跑通 Agent 的一次完整交互。
"""

from ollama_util import is_ollama_available, real_chat, SimOllama, chat_wrapper


def first_chat():
    print("=" * 62)
    print("01 你的第一段本地对话（双模式）")
    print("=" * 62)

    model = "llama3.1"  # 可换成 qwen2.5 / tinyllama 等
    print(f"  目标模型：{model}\n")

    if is_ollama_available(model):
        print("  [真实模式] 正在调用 Ollama ...")
        reply = real_chat(model, [
            {"role": "system", "content": "你是简洁的助手。"},
            {"role": "user", "content": "你好，请用一句话介绍你自己。"},
        ])
        print(f"  模型回答：{reply}")
    else:
        print("  [模拟模式] 使用 SimOllama ...")
        reply = SimOllama.chat(model, [
            {"role": "system", "content": "你是简洁的助手。"},
            {"role": "user", "content": "你好，请用一句话介绍你自己。"},
        ])
        print(f"  模拟回答：{reply}")

    print("\n>>> 提示：安装 Ollama 并 `ollama pull llama3.1` 后，此处将显示真实输出")


def wrapper_demo():
    print("=" * 62)
    print("02 用封装 chat_wrapper（verbose 显示当前模式）")
    print("=" * 62)
    reply = chat_wrapper(
        "llama3.1",
        [{"role": "user", "content": "什么是机器学习？"}],
        options={"temperature": 0.3},
        verbose=True,
    )
    print(f"  回答：{reply}")


def main():
    first_chat()
    print()
    wrapper_demo()


if __name__ == "__main__":
    main()