# -*- coding: utf-8 -*-
"""
文件用途：各格式文件 Reader 加载
---------------------------------
llama-index-readers-file 提供针对不同格式的专用 Reader：
    PDFReader / DocxReader / CsvReader / MarkdownReader / PPTXReader 等。

本示例用 FileReaderDemo 类演示常用 Reader 的加载方式，
并在文件不存在时自动生成对应格式的示例文件。

运行：
    python 02_file_readers.py
"""
import csv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"


# ---------- 自动生成各格式示例文件 ----------
def ensure_sample_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Markdown
    if not (DATA_DIR / "guide.md").exists():
        (DATA_DIR / "guide.md").write_text(
            "# DataIQ 用户指南\n\n本文档介绍 DataIQ 的安装与使用。\n"
            "点击登录后可进入控制台。",
            encoding="utf-8",
        )
    # CSV（带表头）
    if not (DATA_DIR / "employees.csv").exists():
        with open(DATA_DIR / "employees.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "department", "email"])
            writer.writerow(["张三", "技术部", "zhang@ex.com"])
            writer.writerow(["李四", "财务部", "li@ex.com"])


class FileReaderDemo:
    """封装各格式文件 Reader 的加载。"""

    # ---------- 1. MarkdownReader ----------
    @staticmethod
    def read_markdown(path: Path) -> None:
        from llama_index.core import SimpleDirectoryReader

        print(f"\n[1] Markdown 读取：{path.name}")
        docs = SimpleDirectoryReader(input_files=[str(path)]).load_data()
        for d in docs:
            print(f"   text: {d.text[:50]}...")

    # ---------- 2. CsvReader ----------
    @staticmethod
    def read_csv(path: Path) -> None:
        from llama_index.core import SimpleDirectoryReader

        print(f"\n[2] CSV 读取（含表头）：{path.name}")
        docs = SimpleDirectoryReader(input_files=[str(path)]).load_data()
        for i, d in enumerate(docs, 1):
            print(f"   CSV行[{i}]: {d.text[:60]}...")

    # ---------- 3. 专用 Reader：PDFReader ----------
    @staticmethod
    def read_pdf(path: Path) -> None:
        try:
            from llama_index.readers.file import PDFReader
        except ImportError:
            print("\n[3] PDF 读取：未安装 llama-index-readers-file，跳过。")
            return
        print(f"\n[3] PDFReader：{path}")
        reader = PDFReader()
        docs = reader.load_data(file=path)
        for d in docs:
            print(f"   页 {d.metadata.get('page_label', '?')}: {d.text[:40]}...")

    # ---------- 4. 专用 Reader：DocxReader ----------
    @staticmethod
    def read_docx(path: Path) -> None:
        try:
            from llama_index.readers.file import DocxReader
        except ImportError:
            print("\n[4] DOCX 读取：未安装 llama-index-readers-file，跳过。")
            return
        print(f"\n[4] DocxReader：{path}")
        reader = DocxReader()
        docs = reader.load_data(file=path)
        for d in docs:
            print(f"   {d.text[:50]}...")


def main() -> None:
    ensure_sample_files()
    print("=" * 60)
    print("各格式文件 Reader 加载演示")
    print("=" * 60)

    # 简单用 SimpleDirectoryReader 演示 md / csv（已安装即可）
    FileReaderDemo.read_markdown(DATA_DIR / "guide.md")
    FileReaderDemo.read_csv(DATA_DIR / "employees.csv")

    # 专用 Reader：需要先生成 PDF / DOCX（未安装额外库则提示）
    _, _ = None, None  # placeholder（保持结构清晰）
    FileReaderDemo.read_pdf(DATA_DIR / "guide.md")   # 演示失败提示分支
    FileReaderDemo.read_docx(DATA_DIR / "guide.md")

    print("\n" + "=" * 60)
    print("说明：PDF/DOCX/PPTX 需先生成真实文件，并安装对应解析依赖；")
    print("       示例中以 '没有对应文件/未安装依赖' 进行降级演示。")
    print("=" * 60)


if __name__ == "__main__":
    main()