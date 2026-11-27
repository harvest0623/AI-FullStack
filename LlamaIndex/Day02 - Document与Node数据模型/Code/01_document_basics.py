# -*- coding: utf-8 -*-
"""
文件用途：Document 创建与元数据管理
------------------------------------
Document 是 LlamaIndex 处理数据的最小单元（text + metadata）。

本示例用 DocumentCreator 类展示多种创建方式：
1. 直接创建：Document(text=..., metadata={...})
2. 动态添加 / 遍历 metadata
3. 从 dict 反向创建（Document.from_dict()）
4. 打印 Document 结构（text 片段 + 全部 metadata）

场景：DataIQ 企业知识文库的 Document 建模，
      用文件类型 / 部门 / 上传时间等元数据标记来源。

运行：
    python 01_document_basics.py
"""
import datetime

from dotenv import load_dotenv

load_dotenv()


class DocumentCreator:
    """封装 Document 的多种创建方式与元数据展示。"""

    # ---------- 方式 1：直接创建 ----------
    @staticmethod
    def create_directly() -> "Document":
        from llama_index.core.schema import Document

        doc = Document(
            text="DataIQ 系统支持 PDF、Word、Markdown 与 CSV 四种主要文档格式的导入。",
            metadata={
                "file_name": "intro.txt",
                "department": "技术部",
                "doc_type": "产品说明",
                "create_time": "2026-01-15",
            },
        )
        return doc

    # ---------- 方式 2：创建后追加/修改 metadata ----------
    @staticmethod
    def create_then_update() -> "Document":
        from llama_index.core.schema import Document

        doc = Document(text="员工使用 DataIQ 时可按部门配置检索权限。")
        # 动态追加元数据（两种写法等价）
        doc.metadata["file_name"] = "security.md"
        doc.metadata["author"] = "Admin"
        doc.metadata["security_level"] = "内部"
        return doc

    # ---------- 方式 3：从 dict 反向创建（常用） ----------
    @staticmethod
    def create_from_dict() -> "Document":
        from llama_index.core.schema import Document

        data = {
            "text": "DataIQ 的检索会返回带相似度评分与来源引用的回答。",
            "metadata": {
                "doc_id": "D-1024",
                "source": "faq.csv",
                "department": "客服部",
            },
        }
        return Document.from_dict(data)

    # ---------- 工具：遍历元数据 ----------
    @staticmethod
    def print_metadata(doc, title: str = "") -> None:
        print(f"--- {title or '元数据'} ---")
        print(f"  text 片段: {doc.text[:50]}...")
        print(f"  text 长度: {len(doc.text)} 字符")
        print(f"  metadata 类型: {type(doc.metadata).__name__}")
        for key, value in doc.metadata.items():
            print(f"    {key!r:>16} : {value!r}")
        print()


def main() -> None:
    print("=" * 60)
    print("Document 创建与元数据演示（DataIQ 场景）")
    print("=" * 60)

    # 使用当前时间生成一个元数据示例
    today = datetime.date.today().strftime("%Y-%m-%d")

    # 1) 方式一：直接创建
    doc1 = DocumentCreator.create_directly()
    DocumentCreator.print_metadata(doc1, "方式一：直接创建传递 metadata")

    # 2) 方式二：创建后追加
    doc2 = DocumentCreator.create_then_update()
    doc2.metadata["upload_time"] = today  # 再补一个时间字段
    DocumentCreator.print_metadata(doc2, "方式二：先创建后追加元数据")

    # 3) 方式三：从 dict 创建
    doc3 = DocumentCreator.create_from_dict()
    DocumentCreator.print_metadata(doc3, "方式三：从 dict（Document.from_dict）创建")

    # 4) 汇总：说明 metadata 的作用
    print("=" * 60)
    print("小结：Document.metadata 常用字段（DataIQ 数据建模）：")
    print("  - file_name      : 来源文件名")
    print("  - department     : 所属部门（可用于权限/过滤）")
    print("  - doc_type       : 文档类型")
    print("  - create_time    : 创建/上传时间")
    print("  - author         : 作者")
    print("  - security_level : 密级")
    print("=" * 60)


if __name__ == "__main__":
    main()