# -*- coding: utf-8 -*-
"""
文件用途：SemanticSplitterNodeParser 语义切分
-----------------------------------------------
语义切分不像句子切分那样"按固定长度"切分，而是**依据句子间的语义相似度**，
在主题发生明显变化的位置切分，让每个 Node 内部语义更连贯。

本示例用 SemanticSplitterDemo 类演示：
1. 用 SemanticSplitterNodeParser 按语义边界切分
2. 对比语义切分与句子切分的差异
3. 展示语义分组的输出
4. 需 embedding 模型（OpenAIEmbedding）；无 Key 时降级为规则演示

运行：
    python 02_semantic_splitter.py
"""
import os

from dotenv import load_dotenv

load_dotenv()


class SemanticSplitterDemo:
    """演示语义切分器。"""

    # ---------- 构造一段包含多个主题语块的文本 ----------
    @staticmethod
    def make_text() -> str:
        return (
            # 主题一：系统介绍
            "DataIQ 是一套企业知识库问答系统。它使用 LlamaIndex 构建。"
            "该系统帮助员工快速检索文档。数据库存储所有知识文档。"
            # 主题二：安装部署
            "安装 DataIQ 需要 Python 3.10 环境。使用 pip 安装依赖。"
            "运行后可打开本地 8000 端口进入控制台。Docker 也是推荐的部署方式。"
            # 主题三：使用与权限
            "员工登录后即可提问。权限按部门隔离。财务与研发数据互不可见。"
            "管理员负责文档录入与权限分配。"
        )

    # ---------- 1. 语义切分（需 Key，联网） ----------
    @staticmethod
    def semantic_split() -> None:
        from llama_index.core import Settings
        from llama_index.core.node_parser import SemanticSplitterNodeParser
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.core.schema import Document

        print("[1] 语义切分（基于 OpenAI Embedding 计算语义边界）")
        # 配置 embedding（需联网）
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        splitter = SemanticSplitterNodeParser(
            buffer_size=1, breakpoint_percentile_threshold=95, embed_model=Settings.embed_model
        )
        doc = Document(text=SemanticSplitterDemo.make_text())
        nodes = splitter.get_nodes_from_documents([doc])
        print(f"  语义切分得到 {len(nodes)} 个 Node：")
        for i, node in enumerate(nodes):
            print(f"    ─ Node[{i}] 长度={len(node.get_text()):<4} | "
                  f"{node.get_text()[:50]}...")
        print()

    # ---------- 2. 无 Key 时的规则降级演示 ----------
    @staticmethod
    def fallback_demo() -> None:
        import re

        print("[2] 降级演示：无 Key 时，采用『按空行/主题块』的启发式分组模拟语义切分")
        text = SemanticSplitterDemo.make_text()
        # 用句号切句后，按"主题标志词"简单分组，模拟语义分组思路
        sentences = [s for s in re.split(r"。", text) if s.strip()]
        print(f"  共 {len(sentences)} 个句子，可按主题关键词人工分组（此处仅演示思路）：")
        groups = ["系统介绍", "安装部署", "使用与权限"]
        print("  示例分组：")
        for gi, g in enumerate(groups):
            print(f"    [{g}] 包含句子示例：{sentences[gi][:20]}...")
        print("  提示：配置 OPENAI_API_KEY 后运行本文件即可体验真实的语义切分。")
        print()


def main() -> None:
    print("=" * 60)
    print("SemanticSplitterNodeParser 语义切分演示")
    print("=" * 60)
    if os.getenv("OPENAI_API_KEY"):
        try:
            SemanticSplitterDemo.semantic_split()
        except Exception as e:  # noqa: BLE001
            print(f"  [警告] 在线语义切分失败（{e}），进入降级演示。\n")
            SemanticSplitterDemo.fallback_demo()
    else:
        print("  [提示] 未检测到 OPENAI_API_KEY，转规则降级演示。\n")
        SemanticSplitterDemo.fallback_demo()
    print("=" * 60)


if __name__ == "__main__":
    main()