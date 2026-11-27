# -*- coding: utf-8 -*-
"""
文件用途：第一个 LlamaIndex 程序
---------------------------------
完整演示 LlamaIndex 核心数据管道的三步走：
    Load（加载） → Index（建索引） → Query（查询回答）

流程：
1. 若目录无数据，则自动生成示例 .txt 企业知识文档
2. 用 SimpleDirectoryReader 加载示例数据（Load）
3. 用 VectorStoreIndex.from_documents() 构建向量索引（Index）
4. 用 as_query_engine().query() 查询，打印回答与来源节点（Query）

环境：
- 需在项目根目录配置 .env，写入 OPENAI_API_KEY
- 若无 API Key，程序会进行降级提示，不会直接崩溃

运行：
    python 01_hello_llama.py
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载根目录或同级目录下的 .env 配置（API Key）
load_dotenv()

# 示例数据目录（相对本文件）
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "company_intro.txt"


def ensure_sample_data() -> None:
    """若示例数据目录为空，则自动生成一份企业知识文档（DataIQ 场景）。"""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        sample = (
            "## DataIQ 企业知识库系统介绍\n\n"
            "DataIQ 是一套基于 LlamaIndex 构建的企业内部知识库问答系统，"
            "旨在帮助企业员工快速检索海量文档，并以自然语言的形式获取答案。\n\n"
            "## 核心功能\n\n"
            "1. 统一知识接入：支持 PDF、Word、Markdown、CSV 等多种格式文档的批量导入；\n"
            "2. 智能语义检索：基于向量索引，理解问题意图并返回最相关内容；\n"
            "3. 多轮对话问答：支持追问与上下文理解，提升回答的连续性；\n"
            "4. 权限隔离：不同部门员工仅能检索本部门授权文档。\n\n"
            "## 技术架构\n\n"
            "系统采用 Load（加载数据）、Parse（解析节点）、Index（构建索引）、"
            "Query（查询回答）四段式数据管道，使用 LlamaIndex 框架实现数据模型、"
            "加载器与节点解析等核心能力。\n\n"
            "## 使用说明\n\n"
            "员工登录系统后，在搜索框输入问题，例如：'DataIQ 支持哪些文档格式？'，"
            "系统将在数秒内返回经过引用的专业回答。\n"
        )
        DATA_FILE.write_text(sample, encoding="utf-8")
        print(f"[Info] 已自动生成示例文档：{DATA_FILE}")


def main() -> None:
    # 1. 准备数据
    ensure_sample_data()
    print("=" * 60)
    print("LlamaIndex 第一个程序：Load → Index → Query")
    print("=" * 60)

    # 2. 动态导入 llama_index（便于在真正需要时才暴露缺失依赖）
    try:
        from llama_index.core import VectorStoreIndex
        from llama_index.core import SimpleDirectoryReader
        from llama_index.core import Settings
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.llms.openai import OpenAI
        from llama_index.embeddings.openai import OpenAIEmbedding
    except ImportError as e:
        print(f"[错误] 缺少必要依赖：{e}")
        print("请先执行：pip install llama-index llama-index-readers-file python-dotenv")
        return

    # 2.1 检查 API Key：无 Key 时降级提示，避免直接报错
    if not os.getenv("OPENAI_API_KEY"):
        print("[警告] 未检测到 OPENAI_API_KEY，将仅演示数据加载与索引构建（不联网）。")
        print("       若要体验完整问答，请在 .env 中配置：OPENAI_API_KEY=sk-xxxx")
        print("-" * 60)

    # 2.2 全局 Settings 配置（可选，未配置则使用默认值）
    if os.getenv("OPENAI_API_KEY"):
        try:
            Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
            Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
            Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        except Exception as e:  # noqa: BLE001
            print(f"[警告] Settings 配置失败（{e}），使用默认配置。")

    # 3. Load 阶段：用 SimpleDirectoryReader 加载目录下的所有文档
    reader = SimpleDirectoryReader(input_dir=str(DATA_DIR), filename_as_id=True)
    documents = reader.load_data()
    print(f"\n[Load] 成功加载 {len(documents)} 个 Document：")
    for i, doc in enumerate(documents):
        excerpt = doc.text[:60].replace("\n", " ")
        print(f"  - Document[{i}] text(前60字): {excerpt}...")
        print(f"      metadata: {doc.metadata}")

    # 4. Index 阶段：从 Document 构建向量索引
    #    （内部会自动调用 Settings.node_parser 完成切分与向量化 embed）
    print("\n[Index] 正在构建向量索引……（若配置了 Key 会调用 Embedding 模型）")
    index = VectorStoreIndex.from_documents(documents)
    print("[Index] 索引构建完成。")

    # 5. Query 阶段：查询并打印回答与来源节点
    print("\n[Query] 向知识库提问……\n")
    query_engine = index.as_query_engine(similarity_top_k=2)
    try:
        response = query_engine.query("DataIQ 支持哪些文档格式？")
        print("→ 回答：", str(response))
        print("\n→ 来源节点：")
        for i, node in enumerate(response.source_nodes, 1):
            print(f"  [{i}] score={node.score:.4f} | {node.node.get_text()[:80]}...")
    except Exception as e:  # noqa: BLE001
        print(f"[说明] 由于未配置 API Key 或网络问题，无法完成在线问答（{e}）。")
        print("       Index 构建与数据管道流程已完整演示；配置 Key 后即可获得回答。")

    print("\n" + "=" * 60)
    print("程序结束：Load → Index → Query 三步数据管道演示完成。")
    print("=" * 60)


if __name__ == "__main__":
    main()