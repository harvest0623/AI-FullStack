# -*- coding: utf-8 -*-
"""
Day09 - 01 LangChain 接入 Ollama（ChatOllama）

讲解版：离线可运行。展示 ChatOllama 的接入骨架，无需安装也能看的懂。
若已 `pip install langchain-ollama` 且本机有 Ollama，放开 `[真实]` 段即可跑通。
"""

from ollama_util import is_ollama_available


def area_01_what_it_looks_like():
    print("接入骨架（伪码视角，写给你理解）：")
    print("""
  from langchain_ollama import ChatOllama

  llm = ChatOllama(model="llama3.1", temperature=0.7)

  # 简单对话
  llm.invoke("给我讲个笑话")

  # prompt 模板 + 链式调用
  from langchain_core.prompts import ChatPromptTemplate
  prompt = ChatPromptTemplate.from_messages([
      ("system", "你是友好的助手"),
      ("user", "{question}"),
  ])
  chain = prompt | llm
  chain.invoke({"question": "什么是RAG？"})
  """)


def check_env():
    if is_ollama_available("llama3.1"):
        print("  检测到真实 Ollama + llama3.1 ✓（可放开【真实】段跑通）")
        return True
    print("  未检测到 Ollama 环境 → 以讲解形式展示。")
    return False


def real_llm_demo():
    # 若本机安装了 langchain-ollama 且服务存活，下面解开即可真实运行
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        print("  未安装 langchain-ollama，跳过真实运行。")
        return
    llm = ChatOllama(model="llama3.1")
    print("  真实调用：", llm.invoke("用一句话介绍自己").content)


def main():
    print(">> LangChain 接入 Ollama（ChatOllama）\n")
    area_01_what_it_looks_like()
    print("环境检查：")
    if check_env():
        real_llm_demo()
    print("\n→ ChatOllama 把 Ollama 包装成标准 LLM 对象，即可用于 chains / agents。")


if __name__ == "__main__":
    main()