# 文件用途：多种分割器对比演示
# 演示 RecursiveCharacterTextSplitter 递归分割、CharacterTextSplitter 字符分割、
# TokenTextSplitter Token 分割、MarkdownHeaderTextSplitter 标题分割、
# 代码分割器 from_language。同一段文本用不同分割器对比输出。
# SplitterComparator 类对比不同分割器效果。

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
    Language,
)

load_dotenv()

# 测试文本（中文，含段落和句子结构）
SAMPLE_TEXT = """LangChain 是一个用于开发 LLM 应用的开源框架。它由 LangChain 公司维护。

LangChain 的核心组件包括 Model I/O、Prompt 管理、Chains 链式调用、Memory 记忆管理和 Retrievers 检索器。其中 LCEL 是 0.3 版本的核心表达式语言，用管道符组合组件。

Memory 组件让 LLM 记住对话历史，实现多轮对话。它提供五种策略：Buffer、Window、Summary、SummaryBuffer、TokenBuffer。

Retrievers 检索器根据查询返回相关文档，是构建问答系统的基础。它基于向量存储和 Embedding 模型实现语义检索。"""

# 测试 Markdown
SAMPLE_MARKDOWN = """# LangChain 概述

LangChain 是 LLM 应用开发框架。

## 核心组件

### Model I/O
模型接口层。

### Chains
链式调用，LCEL 是核心。

## Memory
记忆管理。

# 总结
本节介绍了 LangChain。"""

# 测试代码
SAMPLE_CODE = """def fibonacci(n):
    result = []
    a, b = 0, 1
    for i in range(n):
        result.append(a)
        a, b = b, a + b
    return result

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class Calculator:
    def add(self, a, b):
        return a + b
    def multiply(self, a, b):
        return a * b
"""


def demo_recursive_splitter() -> None:
    """RecursiveCharacterTextSplitter：递归字符分割，通用首选。"""
    print("=" * 60)
    print("【RecursiveCharacterTextSplitter 递归分割】\n")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=80,
        chunk_overlap=20,
        separators=["\n\n", "\n", "。", " ", ""],
    )
    chunks = splitter.split_text(SAMPLE_TEXT)

    print(f"chunk_size=80, chunk_overlap=20")
    print(f"分割为 {len(chunks)} 块：\n")
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}（{len(chunk)} 字）：{chunk[:50]}...")
    print()


def demo_character_splitter() -> None:
    """CharacterTextSplitter：按固定分隔符分割。"""
    print("=" * 60)
    print("【CharacterTextSplitter 固定分隔符分割】\n")

    splitter = CharacterTextSplitter(
        separator="\n\n",     # 只按段落分
        chunk_size=80,
        chunk_overlap=20,
    )
    chunks = splitter.split_text(SAMPLE_TEXT)

    print(f"separator='\\n\\n', chunk_size=80")
    print(f"分割为 {len(chunks)} 块：\n")
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}（{len(chunk)} 字）：{chunk[:50]}...")
    print()


def demo_token_splitter() -> None:
    """TokenTextSplitter：按 Token 数分割。"""
    print("=" * 60)
    print("【TokenTextSplitter 按 Token 分割】\n")

    splitter = TokenTextSplitter(
        chunk_size=50,      # 每块 50 Token
        chunk_overlap=10,
    )
    chunks = splitter.split_text(SAMPLE_TEXT)

    print(f"chunk_size=50 tokens, chunk_overlap=10")
    print(f"分割为 {len(chunks)} 块：\n")
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}（{len(chunk)} 字）：{chunk[:50]}...")
    print()


def demo_markdown_splitter() -> None:
    """MarkdownHeaderTextSplitter：按 Markdown 标题层级分割。"""
    print("=" * 60)
    print("【MarkdownHeaderTextSplitter 按标题分割】\n")

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
    )
    docs = splitter.split_text(SAMPLE_MARKDOWN)

    print(f"按标题分割为 {len(docs)} 个 Document：\n")
    for i, doc in enumerate(docs):
        print(f"  Document {i}：")
        print(f"    metadata（标题层级）：{doc.metadata}")
        print(f"    page_content：{doc.page_content.strip()[:40]}...")
    print()


def demo_code_splitter() -> None:
    """代码分割器：按代码语法分割，避免在语句中间断开。"""
    print("=" * 60)
    print("【代码分割器 from_language】\n")

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=80,
        chunk_overlap=10,
    )
    chunks = splitter.split_text(SAMPLE_CODE)

    print(f"language=Python, chunk_size=80")
    print(f"分割为 {len(chunks)} 块：\n")
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}：")
        print(f"    {chunk.strip()[:60]}...")
    print()


class SplitterComparator:
    """分割器对比器：同一段文本用不同分割器对比输出。"""

    def __init__(self, text: str) -> None:
        self.text = text

    def compare(self, chunk_size: int = 80, chunk_overlap: int = 20) -> None:
        """对比多种分割器的效果。"""
        print("=" * 60)
        print("【SplitterComparator 分割器对比】\n")
        print(f"参数：chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        print(f"原文长度：{len(self.text)} 字\n")

        splitters = {
            "RecursiveCharacter": RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", "。", " ", ""],
            ),
            "Character": CharacterTextSplitter(
                separator="\n\n", chunk_size=chunk_size, chunk_overlap=chunk_overlap,
            ),
            "Token": TokenTextSplitter(
                chunk_size=max(chunk_size // 3, 20), chunk_overlap=max(chunk_overlap // 3, 5),
            ),
        }

        print(f"{'分割器':<22}{'块数':<8}{'平均块长度':<12}{'最短块':<10}{'最长块'}")
        print("-" * 60)

        for name, splitter in splitters.items():
            chunks = splitter.split_text(self.text)
            if chunks:
                lengths = [len(c) for c in chunks]
                avg = sum(lengths) // len(lengths)
                print(f"{name:<22}{len(chunks):<8}{avg:<12}{min(lengths):<10}{max(lengths)}")
            else:
                print(f"{name:<22}{0:<8}{'N/A'}")

        print("\n结论：")
        print("  - RecursiveCharacter：递归切分，语义保持最好（推荐）")
        print("  - Character：只按单一分隔符，块大小不均")
        print("  - Token：按 Token 精确控制，但可能在字符层面切分\n")


def main() -> None:
    demo_recursive_splitter()
    demo_character_splitter()
    demo_token_splitter()
    demo_markdown_splitter()
    demo_code_splitter()

    # 对比器
    comparator = SplitterComparator(SAMPLE_TEXT)
    comparator.compare(chunk_size=80, chunk_overlap=20)

    print("=" * 60)
    print("多种分割器对比演示完成。")


if __name__ == "__main__":
    main()
