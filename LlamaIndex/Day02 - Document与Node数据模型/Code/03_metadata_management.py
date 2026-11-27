# -*- coding: utf-8 -*-
"""
文件用途：元数据（metadata）管理
---------------------------------
metadata 描述 Document/Node 的来源与属性，在检索中作用重大：
1. 可展示（来源引用）
2. 可过滤（按部门/文档类型筛选）
3. 可注入 Prompt（把元数据带进回答上下文）

本示例用 MetadataManager 类演示：
1. 添加 / 修改 / 删除 metadata
2. 构造带 metadata 的节点集合，模拟按部门过滤
3. 把 metadata 注入 Prompt 模板（展示用法与思路）

场景：DataIQ 用 department / doc_type 等 metadata 标记节点，实现部门级检索权限。

运行：
    python 03_metadata_management.py
"""
from dotenv import load_dotenv

load_dotenv()


class MetadataManager:
    """封装 metadata 的增删改查、过滤与 Prompt 注入。"""

    # ---------- 1. metadata 的添加 / 修改 / 删除 ----------
    @staticmethod
    def crud_demo() -> "Document":
        from llama_index.core.schema import Document

        doc = Document(text="DataIQ 支持对检索结果进行来源引用。")
        print("[1] metadata 增删改")
        # 添加
        doc.metadata["department"] = "研发部"
        doc.metadata["doc_type"] = "产品说明"
        print(f"  添加后: {dict(doc.metadata)}")
        # 修改
        doc.metadata["doc_type"] = "用户手册"
        print(f"  修改后: {dict(doc.metadata)}")
        # 删除
        removed = doc.metadata.pop("doc_type", None)
        print(f"  删除 doc_type={removed!r} 后: {dict(doc.metadata)}")
        print()
        return doc

    # ---------- 2. 用 metadata 过滤节点集合 ----------
    @staticmethod
    def filter_demo() -> None:
        from llama_index.core.schema import Document

        docs = [
            Document(text="财务报销流程说明。", metadata={"department": "财务部"}),
            Document(text="研发环境搭建指南。", metadata={"department": "研发部"}),
            Document(text="差旅申请规则。", metadata={"department": "财务部"}),
            Document(text="前端编码规范。", metadata={"department": "研发部"}),
        ]
        print("[2] 按 metadata 过滤（模拟部门权限）")
        target = "财务部"
        matched = [d for d in docs if d.metadata.get("department") == target]
        print(f"  '{target}' 部门可见文档：")
        for d in matched:
            print(f"    - {d.text}")
        print()

    # ---------- 3. 把 metadata 注入 Prompt 模板 ----------
    @staticmethod
    def prompt_inject_demo() -> None:
        from llama_index.core.schema import TextNode

        print("[3] 将 metadata 注入 Prompt（思路演示）")
        node = TextNode(
            text="DataIQ 已接入统一身份认证系统，支持单点登录。",
            metadata={"file_name": "sso.md", "department": "IT 部", "doc_type": "架构文档"},
        )

        # 用户自定义 Prompt 模板：可在模板里引用 metadata
        template = (
            "你是一名企业助手。以下是来自 {department} 的文档《{file_name}》"
            "（类型：{doc_type}）相关内容：\n{context}\n请根据内容回答。"
        )
        prompt = template.format(
            department=node.metadata.get("department", "未知部门"),
            file_name=node.metadata.get("file_name", "未知文件"),
            doc_type=node.metadata.get("doc_type", "未知类型"),
            context=node.get_text(),
        )
        print(f"  生成的 Prompt：\n{prompt}")
        print()


def main() -> None:
    print("=" * 60)
    print("metadata 管理演示（DataIQ 场景）")
    print("=" * 60)
    mgr = MetadataManager()
    mgr.crud_demo()
    mgr.filter_demo()
    mgr.prompt_inject_demo()
    print("=" * 60)
    print("关键点：metadata 在检索中的作用 = 可展示 + 可过滤 + 可注入 Prompt")
    print("=" * 60)


if __name__ == "__main__":
    main()