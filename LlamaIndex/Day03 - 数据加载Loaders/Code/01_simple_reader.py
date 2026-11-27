# -*- coding: utf-8 -*-
"""
文件用途：SimpleDirectoryReader 通用目录加载
--------------------------------------------
SimpleDirectoryReader 是 LlamaIndex 最常用的加载器，能自动识别目录下多种文件类型。

本示例用 SimpleReaderDemo 类演示：
1. 加载目录中的多种格式文件（.txt / .md）
2. recursive=True 递归加载子目录
3. required_exts 按扩展名过滤
4. 批量加载并打印每个 Document 的文本片段 + metadata
5. 若目录无数据，则自动生成示例 .txt / .md 文档

运行：
    python 01_simple_reader.py
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 示例数据根目录
DATA_DIR = Path(__file__).parent / "data"
SUB_DIR = DATA_DIR / "docs_nested"     # 用于演示递归
OUT_DIR = DATA_DIR / "docs_md"         # 用于演示扩展名过滤


def ensure_sample_files() -> None:
    """若目录为空，生成 .txt 与 .md 示例文档。"""
    for d in (DATA_DIR, SUB_DIR, OUT_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # 根目录 .txt
    if not (DATA_DIR / "readme.txt").exists():
        (DATA_DIR / "readme.txt").write_text(
            "DataIQ 读取器示例：SimpleDirectoryReader 支持多种格式。\n"
            "本文件为纯文本说明。",
            encoding="utf-8",
        )
    # 子目录 .md（递归演示）
    if not (SUB_DIR / "nested.md").exists():
        (SUB_DIR / "nested.md").write_text(
            "# 递归加载示例\n这是子目录中的一个 Markdown 文档，用于演示 recursive 功能。",
            encoding="utf-8",
        )
    # 独立 .md 目录（扩展名过滤演示）
    if not (OUT_DIR / "note.md").exists():
        (OUT_DIR / "note.md").write_text(
            "# 扩展名过滤\n这是 docs_md 目录下的 markdown 文件。",
            encoding="utf-8",
        )


class SimpleReaderDemo:
    """封装 SimpleDirectoryReader 的几种用法。"""

    # ---------- 1. 基础加载：整个目录 ----------
    @staticmethod
    def load_all(dir_path: Path) -> None:
        from llama_index.core import SimpleDirectoryReader

        print(f"\n[1] 基础加载：{dir_path}")
        reader = SimpleDirectoryReader(input_dir=str(dir_path), filename_as_id=True)
        documents = reader.load_data()
        print(f"  共加载 {len(documents)} 个 Document：")
        for i, doc in enumerate(documents):
            print(f"    - {doc.metadata.get('file_name', '?')} "
                  f"| text: {doc.text[:40].strip()}...")

    # ---------- 2. 递归加载 ----------
    @staticmethod
    def load_recursive(dir_path: Path) -> None:
        from llama_index.core import SimpleDirectoryReader

        print(f"\n[2] 递归加载（recursive=True）：{dir_path}")
        reader = SimpleDirectoryReader(
            input_dir=str(dir_path), recursive=True, filename_as_id=True)
        documents = reader.load_data()
        print(f"  递归后可加载 {len(documents)} 个 Document（含子目录）：")
        for doc in documents:
            print(f"    - {doc.metadata.get('file_path', '?')}")

    # ---------- 3. 按扩展名过滤 ----------
    @staticmethod
    def load_with_ext(dir_path: Path, exts: list) -> None:
        from llama_index.core import SimpleDirectoryReader

        print(f"\n[3] 扩展名过滤（required_exts={exts}）：{dir_path}")
        reader = SimpleDirectoryReader(
            input_dir=str(dir_path),
            recursive=True if dir_path == DATA_DIR else False,
            required_exts=exts,
            filename_as_id=True,
        )
        documents = reader.load_data()
        print(f"  过滤后保留 {len(documents)} 个 Document：")
        for doc in documents:
            print(f"    - {doc.metadata.get('file_name', '?')}"
                  f"({doc.metadata.get('file_extension', '?')})")

    # ---------- 4. 打印完整 metadata ----------
    @staticmethod
    def dump_meta(dir_path: Path) -> None:
        from llama_index.core import SimpleDirectoryReader

        print(f"\n[4] 打印 Document 的 metadata：{dir_path}")
        reader = SimpleDirectoryReader(input_dir=str(dir_path), filename_as_id=True)
        documents = reader.load_data()
        for i, doc in enumerate(documents, 1):
            print(f"  Document[{i}] metadata = {dict(doc.metadata)}")


def main() -> None:
    ensure_sample_files()
    print("=" * 60)
    print("SimpleDirectoryReader 通用目录加载演示")
    print("=" * 60)

    SimpleReaderDemo.load_all(DATA_DIR)
    SimpleReaderDemo.load_recursive(DATA_DIR)

    # 分别展示两种过滤目标更清晰：
    #   - OUT_DIR 全为 .md，过滤 .txt 应为 0 个
    #   - DATA_DIR 递归，过滤出所有 .md
    SimpleReaderDemo.load_with_ext(OUT_DIR, [".txt"])   # 期望为空
    SimpleReaderDemo.load_with_ext(DATA_DIR, [".md"])   # 期望只剩 markdown

    SimpleReaderDemo.dump_meta(DATA_DIR)
    print("\n" + "=" * 60)
    print("提示：SimpleDirectoryReader 自动识别的扩展名包括 "
          "md/txt/pdf/docx/pptx/csv/ipynb/html 等。")
    print("=" * 60)


if __name__ == "__main__":
    main()