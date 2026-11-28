# -*- coding: utf-8 -*-
"""
文件用途：元数据提取 Metadata Extractor 与 IngestionPipeline
-------------------------------------------------------------
切分的同时，可以为 Node 提取结构化 metadata（关键词、标题、实体、摘要），
这能显著提升后续检索的精度与可解释性。

本示例用 MetadataExtractorDemo 类演示：
1. MetadataExtractor 组合 Extractors（KV自建/内置）
2. IngestionPipeline 串联 Splitter + Extractor，一键把 Document 转成带元数据的 Node
3. 展示提取结果：为节点增加关键词 / 标题等元数据
4. 无 Key 时降级为"规则化"元数据注入演示

运行：
    python 03_metadata_extractor.py
"""
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


class MetadataExtractorDemo:
    """演示元数据提取 + IngestionPipeline。"""

    @staticmethod
    def make_documents():
        from llama_index.core.schema import Document

        return [
            Document(text="DataIQ 支持 PDF、Word、Markdown 与 CSV 格式的文档导入，"
                          "并支持按部门配置查看权限。",
                     metadata={"source": "intro.txt"}),
            Document(text="Docker 是推荐的 DataIQ 部署方式，端口映射为 8000，"
                          "需配置企业统一身份认证。",
                     metadata={"source": "deploy.txt"}),
        ]

    # ---------- 1. 内置 Extractor（需 LLM，联网） ----------
    @staticmethod
    def offline_extract(docs) -> List[Any]:
        from llama_index.core.ingestion import IngestionPipeline
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.core.schema import Document, TextNode

        # 由于内置 Title/Keyword 需要 LLM，这里用一套"规则"变换替代演示，
        # 说明 ingestion 管道如何为每个 Node 补元数据（不联网）。
        print("[趋势] 用 IngestionPipeline 串接 Splitter + 元数据规则变换")
        splitter = SentenceSplitter(chunk_size=64, chunk_overlap=8)
        # 建立一个"纯规则"的元数据变换：根据文本包含的关键词打标签
        def add_kw_transform(nodes: List[TextNode]) -> List[TextNode]:
            kw_map = {"PDF": "格式", "Docker": "部署", "权限": "权限"}
            for n in nodes:
                tags = [v for k, v in kw_map.items() if k in n.get_text()]
                if tags:
                    n.metadata["auto_tags"] = tags
            return nodes

        pipeline = IngestionPipeline(
            transformations=[splitter, add_kw_transform],  # 串接"切分 + 元数据变换"
        )
        result = pipeline.run(documents=docs)
        return result

    # ---------- 2. 联网时尝试内置 Extractor ----------
    @staticmethod
    def online_extract(docs) -> None:
        try:
            from llama_index.core.extractors import (
                MetadataExtractor, TitleExtractor, KeywordExtractor, SummaryExtractor,
            )
            from llama_index.core.ingestion import IngestionPipeline
            from llama_index.core.node_parser import SentenceSplitter

            extractor = MetadataExtractor(
                extractors=[
                    TitleExtractor(nodes=1),     # 提取标题
                    KeywordExtractor(keywords=3),# 提取关键词
                    SummaryExtractor(summaries=["self"]),  # 提取摘要
                ],
            )
            pipeline = IngestionPipeline(
                transformations=[SentenceSplitter(chunk_size=64), extractor],
            )
            nodes = pipeline.run(documents=docs)
            print(f"  提取得到 {len(nodes)} 个 Node，每个带元数据：")
            for i, n in enumerate(nodes):
                print(f"    Node[{i}] metadata keys = {list(n.metadata.keys())}")
                for k in ("document_title", "excerpt_keywords", "section_summary"):
                    if k in n.metadata:
                        val = str(n.metadata[k])[:40]
                        print(f"      - {k}: {val}...")
        except Exception as e:  # noqa: BLE001
            print(f"  [提示] 内置元数据提取需要额外依赖/LM，此机器降级（{e}）。")
            print("  （Keyword/Summary 提取依赖 LLM，无 Key 或未装相关库时不可用）")


def main() -> None:
    print("=" * 60)
    print("元数据提取 / IngestionPipeline 演示")
    print("=" * 60)
    demo = MetadataExtractorDemo()
    docs = demo.make_documents()

    # 先演示"纯规则管道"（离线必可运行）
    nodes = demo.offline_extract(docs)
    print(f"\n[结果] 离线管道产出 {len(nodes)} 个 Node：")
    for i, n in enumerate(nodes):
        print(f"    Node[{i}] auto_tags={n.metadata.get('auto_tags')} | "
              f"source={n.metadata.get('source')}")

    # 有 Key 时尝试真实内置 Extractor
    print()
    if os.getenv("OPENAI_API_KEY"):
        print("[在线] 检测到 API Key，尝试内置 Title/Keyword/Summary 元数据提取：")
        demo.online_extract(docs)
    else:
        print("[提示] 未检测到 OPENAI_API_KEY，内置 LLM 元数据提取跳过；"
              "以上规则管道演示了 IngestionPipeline 的用法。")
    print("=" * 60)


if __name__ == "__main__":
    main()