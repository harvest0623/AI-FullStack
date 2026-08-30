# 文件用途：多种格式文档加载演示
# 演示 TextLoader 加载 txt、CSVLoader 加载 CSV、JSONLoader 加载 JSON、
# PyPDFLoader 加载 PDF，展示每种 Loader 的输出 Document 结构。
# DocumentLoader 统一封装类。场景：ChainQA 多格式文档接入

import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    JSONLoader,
    PyPDFLoader,
)

load_dotenv()

# 示例数据目录
DATA_DIR = Path(__file__).parent / "sample_data"


def prepare_sample_data() -> None:
    """准备示例数据文件，供后续 Loader 加载。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. txt 文件
    txt_path = DATA_DIR / "intro.txt"
    txt_path.write_text(
        "LangChain 是一个用于开发 LLM 应用的框架。\n"
        "它提供了模型接口、Prompt 管理、链式调用、记忆管理等核心组件。\n"
        "LCEL 是其核心表达式语言，用管道符组合组件。",
        encoding="utf-8",
    )

    # 2. CSV 文件
    csv_path = DATA_DIR / "users.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "age", "city"])
        writer.writerow(["张三", "20", "北京"])
        writer.writerow(["李四", "25", "上海"])
        writer.writerow(["王五", "30", "广州"])

    # 3. JSON 文件
    json_path = DATA_DIR / "messages.json"
    json_path.write_text(
        json.dumps({
            "messages": [
                {"role": "user", "content": "什么是 LangChain？"},
                {"role": "assistant", "content": "LangChain 是 LLM 应用框架。"},
                {"role": "user", "content": "它有哪些组件？"},
                {"role": "assistant", "content": "包括 Chains、Memory、Retrievers 等。"},
            ]
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class DocumentLoader:
    """统一文档加载器，封装多种格式 Loader。

    根据文件扩展名自动选择合适的 Loader。
    """

    @staticmethod
    def load(file_path: str | Path) -> list[Document]:
        """根据文件类型加载文档，返回 Document 列表。"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{path}")

        suffix = path.suffix.lower()

        if suffix == ".txt":
            loader = TextLoader(str(path), encoding="utf-8")
        elif suffix == ".csv":
            loader = CSVLoader(str(path), encoding="utf-8")
        elif suffix == ".json":
            loader = JSONLoader(
                file_path=str(path),
                jq_schema=".messages[].content",  # 提取每条消息的 content
                text_content=False,
            )
        elif suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        else:
            raise ValueError(f"不支持的文件格式：{suffix}")

        return loader.load()

    @staticmethod
    def load_text(file_path: str | Path) -> list[Document]:
        return TextLoader(str(file_path), encoding="utf-8").load()

    @staticmethod
    def load_csv(file_path: str | Path) -> list[Document]:
        return CSVLoader(str(file_path), encoding="utf-8").load()

    @staticmethod
    def load_json(file_path: str | Path, jq_schema: str = ".messages[].content") -> list[Document]:
        return JSONLoader(
            file_path=str(file_path),
            jq_schema=jq_schema,
            text_content=False,
        ).load()


def demo_text_loader() -> None:
    """TextLoader：加载 txt 文件。"""
    print("=" * 60)
    print("【TextLoader 加载 txt】\n")

    txt_path = DATA_DIR / "intro.txt"
    docs = DocumentLoader.load_text(txt_path)

    print(f"文件：{txt_path.name}")
    print(f"Document 数量：{len(docs)}")
    for i, doc in enumerate(docs):
        print(f"  [{i}] page_content（前 60 字）：{doc.page_content[:60]}...")
        print(f"      metadata：{doc.metadata}")
    print()


def demo_csv_loader() -> None:
    """CSVLoader：每行一个 Document。"""
    print("=" * 60)
    print("【CSVLoader 加载 CSV（每行一个 Document）】\n")

    csv_path = DATA_DIR / "users.csv"
    docs = DocumentLoader.load_csv(csv_path)

    print(f"文件：{csv_path.name}")
    print(f"Document 数量：{len(docs)}（CSV 3 行数据 = 3 个 Document）")
    for i, doc in enumerate(docs):
        print(f"  [{i}] page_content：{doc.page_content}")
        print(f"      metadata：{doc.metadata}")
    print()


def demo_json_loader() -> None:
    """JSONLoader：用 jq 语法提取字段。"""
    print("=" * 60)
    print("【JSONLoader 加载 JSON（jq_schema 提取字段）】\n")

    json_path = DATA_DIR / "messages.json"
    docs = DocumentLoader.load_json(json_path, jq_schema=".messages[].content")

    print(f"文件：{json_path.name}")
    print(f"Document 数量：{len(docs)}（4 条消息 = 4 个 Document）")
    for i, doc in enumerate(docs):
        print(f"  [{i}] page_content：{doc.page_content}")
        print(f"      metadata：{doc.metadata}")
    print()


def demo_pdf_loader() -> None:
    """PyPDFLoader：加载 PDF，每页一个 Document（需准备 PDF 文件）。"""
    print("=" * 60)
    print("【PyPDFLoader 加载 PDF（每页一个 Document）】\n")

    pdf_path = DATA_DIR / "sample.pdf"
    if not pdf_path.exists():
        print(f"未找到 {pdf_path.name}，跳过 PDF 演示")
        print("说明：PyPDFLoader 每页生成一个 Document，metadata 含 page 编号")
        print("用法：PyPDFLoader('doc.pdf').load()  # 需 pip install pypdf\n")
        return

    docs = PyPDFLoader(str(pdf_path)).load()
    print(f"文件：{pdf_path.name}")
    print(f"Document 数量：{len(docs)}（PDF 页数 = Document 数）")
    for i, doc in enumerate(docs[:3]):  # 只展示前 3 页
        print(f"  [{i}] page_content（前 60 字）：{doc.page_content[:60]}...")
        print(f"      metadata：{doc.metadata}")
    print()


def demo_unified_loader() -> None:
    """DocumentLoader 统一封装：根据扩展名自动选择 Loader。"""
    print("=" * 60)
    print("【DocumentLoader 统一封装（自动识别格式）】\n")

    files = ["intro.txt", "users.csv", "messages.json"]
    for fname in files:
        path = DATA_DIR / fname
        docs = DocumentLoader.load(path)
        print(f"加载 {fname}：{len(docs)} 个 Document，格式={Path(fname).suffix}")

    print("\n说明：DocumentLoader 根据扩展名自动分派，统一接口\n")


def main() -> None:
    prepare_sample_data()
    demo_text_loader()
    demo_csv_loader()
    demo_json_loader()
    demo_pdf_loader()
    demo_unified_loader()
    print("=" * 60)
    print("多种格式文档加载演示完成。")


if __name__ == "__main__":
    main()
