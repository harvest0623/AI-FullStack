# -*- coding: utf-8 -*-
"""
文件用途：SentenceSplitter 句子切分
-----------------------------------
SentenceSplitter 是 LlamaIndex 自带的最常用切分器，默认按句子边界切分，
可通过 chunk_size / chunk_overlap 控制切块大小与重叠区，从而在
"检索精度"与"Token 成本"之间取得平衡。

本示例用 SentenceSplitterDemo 类演示：
1. 基础切分：把 Document 切为多个 Node
2. chunk_size 与 chunk_overlap 的参数作用
3. 对比不同 chunk_size 的切分效果（Node 数量 / 长度 / 文本片段）
4. 打印每个 Node 的文本与长度

场景：DataIQ 长文档切分。

运行：
    python 01_sentence_splitter.py
"""
from dotenv import load_dotenv

load_dotenv()


class SentenceSplitterDemo:
    """演示句子切分器 SentenceSplitter。"""

    # ---------- 构造一段较长的 DataIQ 文档 ----------
    @staticmethod
    def make_document():
        from llama_index.core.schema import Document

        text = (
            "DataIQ 是一套企业知识库问答系统。它基于 LlamaIndex 框架构建。"
            "系统支持多格式文档的批量导入。检索采用向量索引实现语义匹配。"
            "系统提供多轮对话问答能力。权限按照部门进行隔离。"
            "管理员可以在后台统一管理知识文档。员工通过搜索框快速获取答案。"
            + "这是用于补充长度的附加说明句子。要确保文本足够长以触发多次切分。"
        )
        return Document(text=text, metadata={"file_name": "long_doc.txt"})

    # ---------- 1. 基础切分（默认参数） ----------
    @staticmethod
    def basic_split() -> None:
        from llama_index.core.node_parser import SentenceSplitter

        print("[1] 基础切分（默认 chunk_size / chunk_overlap）")
        doc = SentenceSplitterDemo.make_document()
        splitter = SentenceSplitter(chunk_size=60, chunk_overlap=10)
        nodes = splitter.get_nodes_from_documents([doc])
        print(f"  切分得到 {len(nodes)} 个 Node：")
        for i, node in enumerate(nodes):
            print(f"    Node[{i}] 长度={len(node.get_text())} | {node.get_text()[:40]}...")
        print()

    # ---------- 2. 展示 chunk_overlap 的作用 ----------
    @staticmethod
    def overlap_demo() -> None:
        from llama_index.core.node_parser import SentenceSplitter

        print("[2] chunk_overlap 的作用（重叠区保持上下文连续）")
        doc = SentenceSplitterDemo.make_document()
        splitter = SentenceSplitter(chunk_size=50, chunk_overlap=15)
        nodes = splitter.get_nodes_from_documents([doc])
        for i, node in enumerate(nodes[:3]):
            print(f"    Node[{i}] 长度={len(node.get_text())} | {node.get_text()}")
        print()

    # ---------- 3. 对比不同 chunk_size 的切分效果 ----------
    @staticmethod
    def compare_sizes() -> None:
        from llama_index.core.node_parser import SentenceSplitter

        print("[3] 对比不同 chunk_size 的切分效果")
        doc = SentenceSplitterDemo.make_document()
        for size in (40, 80, 160):
            splitter = SentenceSplitter(chunk_size=size, chunk_overlap=10)
            nodes = splitter.get_nodes_from_documents([doc])
            lens = [len(n.get_text()) for n in nodes]
            print(f"    chunk_size={size:<4} → Node 数={len(nodes)} "
                  f"| 各块长度={lens}")
        print()


def main() -> None:
    print("=" * 60)
    print("SentenceSplitter 句子切分演示（DataIQ 场景）")
    print("=" * 60)
    SentenceSplitterDemo.basic_split()
    SentenceSplitterDemo.overlap_demo()
    SentenceSplitterDemo.compare_sizes()
    print("=" * 60)


if __name__ == "__main__":
    main()