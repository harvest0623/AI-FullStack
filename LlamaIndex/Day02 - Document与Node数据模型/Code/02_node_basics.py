# -*- coding: utf-8 -*-
"""
文件用途：Node 属性与创建
-------------------------
Node 是 Document 切分后的检索单元，是查询的基础粒度。

本示例用 NodeViewer 类展示：
1. TextNode 的直接创建（text / node_id / metadata / relationships）
2. 手动设置 node_id（自动生成 vs 自定义）
3. 从 Document 派生长 TextNode（不切分，保留整篇）
4. 展示 Node 结构（重点：relationships 父子关系）

场景：DataIQ 中一个 "企业安全规范" 文档被建模为多个节点，并挂载到源 Document。

运行：
    python 02_node_basics.py
"""
from dotenv import load_dotenv

load_dotenv()


class NodeViewer:
    """展示 TextNode 的创建与结构。"""

    # ---------- 1. 直接创建 TextNode ----------
    @staticmethod
    def create_textnode() -> "TextNode":
        from llama_index.core.schema import TextNode

        node = TextNode(
            text="DataIQ 节点是检索的最小粒度，携带文本与元数据。",
            metadata={"department": "技术部", "doc_type": "概念解释"},
            # 不指定 node_id 时，会由 LlamaIndex 自动生成（UUID）
        )
        return node

    # ---------- 2. 手动设置 node_id ----------
    @staticmethod
    def create_with_id() -> "TextNode":
        from llama_index.core.schema import TextNode

        node = TextNode(
            text="主数据管理（MDM）目录仅财务部门可见。",
            node_id="custom-node-0001",  # 自定义稳定 ID
            metadata={"department": "财务部"},
        )
        return node

    # ---------- 3. 从 Document 派生（单节点，不切分） ----------
    @staticmethod
    def from_document() -> tuple:
        from llama_index.core.schema import Document, TextNode

        doc = Document(
            text="请勿在公网传输机密文档，建议使用内网加密通道。",
            metadata={"file_name": "security.md", "department": "安全部"},
        )
        # 把 Document 转为 TextNode（doc_id 自动成为 source 关联）
        node = TextNode(text=doc.text, metadata=dict(doc.metadata))
        # 建立父子关系：node 是 source 的子节点
        node.relationships = {
            "source": doc.as_related_node_info(),  # 关联到源 Document
        }
        # 把 Document 原始 ID 记录到 metadata，便于追溯
        node.metadata["doc_id"] = doc.doc_id
        return doc, node

    # ---------- 工具：打印 Node 结构 ----------
    @staticmethod
    def print_node(node, title: str = "") -> None:
        print(f"--- {title or 'Node'} ---")
        print(f"  node_id     : {node.node_id}")
        print(f"  text 片段   : {node.get_text()[:40]}...")
        print(f"  metadata    : {node.metadata}")
        print(f"  relationships: {node.relationships}")
        print()


def main() -> None:
    print("=" * 60)
    print("TextNode 属性与创建演示（DataIQ 场景）")
    print("=" * 60)

    # 1) 直接创建（自动 node_id）
    n1 = NodeViewer.create_textnode()
    NodeViewer.print_node(n1, "方式一：直接创建（自动生成 node_id）")

    # 2) 手动指定 node_id
    n2 = NodeViewer.create_with_id()
    NodeViewer.print_node(n2, "方式二：手动指定 node_id")

    # 3) 从 Document 派生并建立父子关系
    doc, n3 = NodeViewer.from_document()
    print(f"--- Document → Node 关系 ---")
    print(f"  Document doc_id : {doc.doc_id}")
    print(f"  TextNode node_id: {n3.node_id}")
    print(f"  node.relationships['source'] = {n3.relationships.get('source')}")
    print(f"  说明：检索返回的是 Node，通过 relationships.source 可回溯源 Document。")
    print()

    # 4) 汇总
    print("=" * 60)
    print("Node 关键属性速查：")
    print("  - text          : 文本内容")
    print("  - node_id       : 节点唯一标识")
    print("  - metadata      : 元数据")
    print("  - relationships : 关系（source / parent-child / prev-next）")
    print("=" * 60)


if __name__ == "__main__":
    main()