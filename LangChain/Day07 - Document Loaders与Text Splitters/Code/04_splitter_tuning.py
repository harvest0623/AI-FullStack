# 文件用途：分割参数调优演示
# 演示 chunk_size 对比实验（300/500/1000/2000）、
# chunk_overlap 对比实验（0/50/100/200），
# 生成调优报告：块数/平均长度/语义完整性评估。
# SplitterConfig 类管理分割参数。含最佳实践建议。

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# 用于调优的长文本（约 1200 字）
LONG_TEXT = """LangChain 是一个用于开发由大语言模型（LLM）驱动的应用程序的开源框架。它由 Harrison Chase 于 2022 年创建，目前是 GitHub 上最受欢迎的 LLM 应用框架之一。

LangChain 的设计理念是"组合性"（Composability），即将各种能力封装为可组合的模块化组件，开发者可以像搭积木一样构建复杂的 LLM 应用。这种设计让框架既灵活又强大。

LangChain 的核心组件包括以下几个方面。Model I/O 层提供了与各种 LLM 的统一接口，支持 OpenAI、Anthropic、Cohere 等多家供应商。Prompt 管理组件负责模板化和管理提示词，支持变量插值和多角色消息。Chains 链式调用组件是框架的核心，LCEL 表达式语言用管道符将多个组件串联，形成强大的处理流水线。

Memory 记忆管理组件让 LLM 记住对话历史，实现真正的多轮对话。它提供五种策略：BufferMemory 全量保留、BufferWindowMemory 滑动窗口、SummaryMemory 自动摘要、SummaryBufferMemory 摘要加缓冲、TokenBufferMemory 按 Token 管理。每种策略各有取舍，适用于不同场景。

Retrievers 检索器组件根据查询返回相关文档，是构建问答系统的基础。它基于向量存储和 Embedding 模型实现语义检索，支持相似度搜索、MMR 搜索等多种策略。Document Loaders 和 Text Splitters 负责加载和分割文档，为检索做准备。

Tools 工具组件让 LLM 能够调用外部函数和 API，实现 Tool Calling。Agent 智能体则结合 LLM 和 Tools，实现自主决策和任务执行。Callbacks 回调组件支持流式输出和执行过程监控。

LangChain 0.3 版本是当前的稳定版本，相比 0.1 和 0.2 有重大改进。它全面采用 LCEL 作为链式调用的标准方式，废弃了旧的 LLMChain 等类。所有组件都实现 Runnable 接口，支持 invoke、batch、stream 三种调用方式。

LangChain 生态系统还包括 LangServe（部署为 API）、LangSmith（追踪与评估）、LangGraph（状态图编排）等工具，覆盖了从开发到部署的完整生命周期。"""


class SplitterConfig:
    """分割参数配置类，管理 chunk_size 和 chunk_overlap。"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def create_splitter(self) -> RecursiveCharacterTextSplitter:
        """根据配置创建分割器。"""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", " ", ""],
        )

    def __repr__(self) -> str:
        return f"SplitterConfig(chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap})"


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """用指定参数分割文本，返回块列表。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", " ", ""],
    )
    return splitter.split_text(text)


def evaluate_semantic_completeness(chunks: list[str]) -> str:
    """评估语义完整性（启发式：检查是否在句号处结尾）。"""
    if not chunks:
        return "无"
    complete_count = sum(1 for c in chunks if c.rstrip().endswith(("。", ".", "！", "？", "\n")))
    ratio = complete_count / len(chunks)
    if ratio >= 0.8:
        return "好"
    elif ratio >= 0.5:
        return "中"
    else:
        return "差"


def experiment_chunk_size() -> None:
    """chunk_size 对比实验：300 / 500 / 1000 / 2000。"""
    print("=" * 60)
    print("【chunk_size 对比实验】\n")
    print(f"原文长度：{len(LONG_TEXT)} 字\n")

    sizes = [300, 500, 1000, 2000]
    print(f"{'chunk_size':<14}{'块数':<8}{'平均长度':<12}{'最短':<8}{'最长':<8}{'语义完整性'}")
    print("-" * 58)

    for size in sizes:
        chunks = split_text(LONG_TEXT, chunk_size=size, chunk_overlap=size // 10)
        lengths = [len(c) for c in chunks]
        avg = sum(lengths) // len(lengths) if lengths else 0
        completeness = evaluate_semantic_completeness(chunks)
        print(f"{size:<14}{len(chunks):<8}{avg:<12}{min(lengths) if lengths else 0:<8}"
              f"{max(lengths) if lengths else 0:<8}{completeness}")

    print("\n分析：")
    print("  - chunk_size=300：块多，每块信息少，检索精确但可能语义不全")
    print("  - chunk_size=500：平衡，推荐起点")
    print("  - chunk_size=1000：块少，每块信息丰富，语义完整但检索不够精确")
    print("  - chunk_size=2000：块很少，可能超出部分模型上下文\n")


def experiment_chunk_overlap() -> None:
    """chunk_overlap 对比实验：0 / 50 / 100 / 200。"""
    print("=" * 60)
    print("【chunk_overlap 对比实验】\n")
    print(f"原文长度：{len(LONG_TEXT)} 字，固定 chunk_size=500\n")

    overlaps = [0, 50, 100, 200]
    print(f"{'overlap':<12}{'块数':<8}{'平均长度':<12}{'总字符':<12}{'冗余率'}")
    print("-" * 52)

    for overlap in overlaps:
        chunks = split_text(LONG_TEXT, chunk_size=500, chunk_overlap=overlap)
        lengths = [len(c) for c in chunks]
        total = sum(lengths)
        avg = total // len(lengths) if lengths else 0
        # 冗余率 = 总字符 - 原文字符 / 原文字符
        redundancy = (total - len(LONG_TEXT)) / len(LONG_TEXT) * 100
        print(f"{overlap:<12}{len(chunks):<8}{avg:<12}{total:<12}{redundancy:.1f}%")

    print("\n分析：")
    print("  - overlap=0：无冗余，但跨块信息可能断裂")
    print("  - overlap=50：适度冗余（约 10%），推荐")
    print("  - overlap=100：冗余较多（约 20%），信息连续性好")
    print("  - overlap=200：冗余过大（约 40%），存储浪费\n")


def generate_tuning_report() -> None:
    """生成完整的参数调优报告。"""
    print("=" * 60)
    print("【分割参数调优报告】\n")

    # 用 SplitterConfig 管理推荐配置
    recommended = SplitterConfig(chunk_size=500, chunk_overlap=50)
    print(f"推荐配置：{recommended}")

    splitter = recommended.create_splitter()
    chunks = splitter.split_text(LONG_TEXT)

    print(f"\n原文长度：{len(LONG_TEXT)} 字")
    print(f"分割块数：{len(chunks)}")
    lengths = [len(c) for c in chunks]
    print(f"块长度范围：{min(lengths)} - {max(lengths)} 字")
    print(f"平均块长度：{sum(lengths) // len(lengths)} 字")
    print(f"语义完整性：{evaluate_semantic_completeness(chunks)}")

    print("\n各块预览：")
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}（{len(chunk)} 字）：{chunk[:40]}...{chunk[-20:]}")
    print()


def best_practices() -> None:
    """分割参数最佳实践建议。"""
    print("=" * 60)
    print("【分割参数最佳实践】\n")

    print("1. chunk_size 选择：")
    print("   - 问答型检索：300-500 字符（精确匹配）")
    print("   - 通用场景：500 字符（推荐起点）")
    print("   - 摘要型任务：800-1000 字符（信息丰富）")
    print("   - 长上下文分析：1000-2000 字符\n")

    print("2. chunk_overlap 选择：")
    print("   - 推荐：chunk_size 的 10-20%")
    print("   - chunk_size=500 → overlap=50-100")
    print("   - 避免过大，否则冗余严重\n")

    print("3. separators 选择（中文）：")
    print("   - ['\\n\\n', '\\n', '。', '！', '？', ' ', '']")
    print("   - 优先段落，再句子，最后字符\n")

    print("4. 调优流程：")
    print("   - 从 chunk_size=500, overlap=50 开始")
    print("   - 用真实查询测试检索效果")
    print("   - 根据效果调整，迭代优化\n")


def main() -> None:
    experiment_chunk_size()
    experiment_chunk_overlap()
    generate_tuning_report()
    best_practices()
    print("=" * 60)
    print("分割参数调优演示完成。")


if __name__ == "__main__":
    main()
