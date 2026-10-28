# -*- coding: utf-8 -*-
"""
Day09 - 04 框架对比与选择

不依赖任何框架，纯讲解：LangChain vs LlamaIndex vs 纯 Ollama 的选型，
以及"Ollama 当底座、换云端只换一行"的 provider 抽象。
"""

from ollama_util import is_ollama_available


def comparison():
    print("三个使用层级（从底层到框架）：")
    print("""
  纯 Ollama（Day01-08）     LangChain（09）        LlamaIndex（09）
  ┌──────────────┐       ┌──────────────┐      ┌──────────────┐
  │ /api/chat    │       │ ChatOllama   │      │ Settings.llm │
  │ /api/embed   │   →   │ OllamaEmbed- │  →   │ OllamaEmbed- │
  │ 手写循环     │       │ dings        │      │ ding         │
  │ 完全可控     │       │ 工作流/Agent │      │ 索引/查询    │
  └──────────────┘       └──────────────┘      └──────────────┘
  最灵活/代码多          通用编排/生态足      知识库/检索强
  """)


def when_to_use():
    print("选型建议：")
    print("  - 只调聊天/简单嵌入       → 纯 Ollama，够用且最轻")
    print("  - 复杂工作流/AAgent/多工具 → LangChain")
    print("  - 主要是文档知识库/检索问答 → LlamaIndex")
    print("  - 追求完全可控/教学实现    → 纯 Ollama 徒手")


def provider_switch():
    print("\nProvider 抽象：Ollama 与云端切换只改一段")
    print("""
  # Ollama（本地）
  llm = ChatOllama(model="llama3.1")
  # 云端（若要换，仅改这一行）
  # llm = ChatOpenAI(model="gpt-4o")
  """)


def main():
    print(">> LangChain vs LlamaIndex vs 纯 Ollama\n")
    print(f"当前机器 Ollama 可用：{'是' if is_ollama_available() else '否'}\n")
    comparison()
    when_to_use()
    provider_switch()
    print("\n→ Ollama 的价值是『本地底座』，框架是编排层，二者不冲突，" 
          "通常可以组合使用。")


if __name__ == "__main__":
    main()