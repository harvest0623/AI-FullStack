# -*- coding: utf-8 -*-
"""
文件用途：自定义 Node Parser
-----------------------------
当内置切分器（句子/语义/层级等）不满足需求时，可继承 NodeParser
实现自定义切分逻辑。任何自定义 Parser 只要返回 List[Node]，
就能无缝接入索引或 IngestionPipeline。

本示例用 CustomParserDemo 类演示：
1. 继承 NodeParser，实现"按段落 + 标题"的自定义切分
2. 保留文档结构信息（把段落序号/标题写入 metadata）
3. 应用到 ingest / get_nodes_from_documents 管道

运行：
    python 04_custom_parser.py
"""
from typing import Any, List, Optional

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------
# 步骤 1：自定义 NodeParser —— 按段落 + 标题切分
# ---------------------------------------------------------------
try:
    from llama_index.core.schema import Document, NodeParser, TextNode
    LLAMA_INDEX_OK = True
except ModuleNotFoundError:  # pragma: no cover
    Document = None
    NodeParser = object  # 占位，避免 import 级崩溃
    TextNode = None
    LLAMA_INDEX_OK = False


class SectionNodeParser(NodeParser):
    """按 Markdown 风格的标题（##）与段落切分。

    每条以 '## ' 开头到下一个标题之间的内容，被切成一个独立 Node，
    并把标题写入 metadata['section_title']。
    """

    def _parse_nodes(
        self,
        nodes: List["Document"],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> List[TextNode]:
        generated: List[TextNode] = []
        for node in nodes:
            text = node.get_content(metadata_mode="none")
            generated.extend(self._split_to_sections(text, dict(node.metadata)))
        return generated

    @staticmethod
    def _split_to_sections(text: str, base_meta: dict) -> List[TextNode]:
        sections: List[TextNode] = []
        current_title = "(无标题)"
        current_lines: List[str] = []

        def flush() -> None:
            if current_lines:
                body = "".join(current_lines).strip()
                if body:
                    meta = dict(base_meta)
                    meta["section_title"] = current_title
                    sections.append(TextNode(text=body, metadata=meta))

        for line in text.splitlines():
            if line.startswith("## "):
                flush()  # 结束上一节
                current_title = line[3:].strip()
                current_lines = []
            else:
                current_lines.append(line)
        flush()  # 结束最后一节
        return sections


# ---------------------------------------------------------------
# 步骤 2：应用自定义 Parser
# ---------------------------------------------------------------
class CustomParserDemo:
    """演示如何使用自定义 Parser。"""

    @staticmethod
    def make_document() -> Document:
        content = (
            "## 系统概述\nDataIQ 是一套企业知识库问答系统，基于 LlamaIndex 构建。\n"
            "系统支持多格式文档导入。\n"
            "## 安装方式\n推荐使用 Docker 部署，端口 8000。\n"
            "也可直接使用 pip 安装依赖后运行。\n"
            "## 权限管理\n权限按部门隔离，管理员统一分配。\n"
        )
        return Document(text=content, metadata={"file_name": "guide.md"})

    @staticmethod
    def run() -> None:
        print("[1] 直接使用自定义 Parser 切分")
        parser = SectionNodeParser()
        nodes = parser.get_nodes_from_documents([CustomParserDemo.make_document()])
        print(f"  切分得到 {len(nodes)} 个 Node：")
        for i, n in enumerate(nodes):
            print(f"    Node[{i}] section_title={n.metadata.get('section_title')!r} | "
                  f"{n.get_text()[:30]}...")

        print("\n[2] 接入 IngestionPipeline（与切分串联）")
        from llama_index.core.ingestion import IngestionPipeline

        def stamp(nodes_: List[TextNode]) -> List[TextNode]:
            for n in nodes_:
                n.metadata["ingested_by"] = "custom-pipeline"
            return nodes_

        pipeline = IngestionPipeline(transformations=[parser, stamp])
        result = pipeline.run(documents=[CustomParserDemo.make_document()])
        print(f"  pipeline 产出 {len(result)} 个 Node：")
        for n in result:
            print(f"    - [{n.metadata.get('section_title')}] "
                  f"ingested_by={n.metadata.get('ingested_by')} | "
                  f"{n.get_text()[:24]}...")


def main() -> None:
    print("=" * 60)
    print("自定义 Node Parser 演示（按段落 + 标题切分）")
    print("=" * 60)
    if not LLAMA_INDEX_OK:  # pragma: no cover
        print("[提示] 未安装 llama_index，需先执行：pip install llama-index")
    else:
        CustomParserDemo.run()
    print("=" * 60)


if __name__ == "__main__":
    main()