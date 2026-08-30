# 文件用途：网页与在线文档加载演示
# 演示 WebBaseLoader 加载网页内容、ArxivLoader 加载论文、
# DirectoryLoader 批量加载目录，展示 metadata 的差异。
# WebDocumentLoader 类封装。场景：ChainQA 在线知识接入

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    WebBaseLoader,
    ArxivLoader,
    DirectoryLoader,
    TextLoader,
)

load_dotenv()

DATA_DIR = Path(__file__).parent / "sample_data"


def prepare_sample_dir() -> None:
    """准备一个含多文件的目录，供 DirectoryLoader 批量加载。"""
    sub_dir = DATA_DIR / "articles"
    sub_dir.mkdir(parents=True, exist_ok=True)
    (sub_dir / "article1.txt").write_text("这是第一篇文章的内容，关于 LangChain 基础。", encoding="utf-8")
    (sub_dir / "article2.txt").write_text("这是第二篇文章的内容，关于 LCEL 链式调用。", encoding="utf-8")
    (sub_dir / "article3.txt").write_text("这是第三篇文章的内容，关于 Memory 记忆管理。", encoding="utf-8")


def demo_web_loader() -> None:
    """WebBaseLoader：加载网页内容（需 beautifulsoup4）。

    实际运行需网络访问。若无网络，会打印说明。
    """
    print("=" * 60)
    print("【WebBaseLoader 加载网页】\n")

    url = "https://python.langchain.com/docs/get_started/introduction"
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        print(f"URL：{url}")
        print(f"Document 数量：{len(docs)}")
        for doc in docs:
            print(f"  page_content（前 100 字）：{doc.page_content[:100]}...")
            print(f"  metadata：{doc.metadata}")
        print()
    except Exception as e:
        print(f"网页加载失败（{e.__class__.__name__}）：可能无网络或缺少 beautifulsoup4")
        print("用法：WebBaseLoader('https://...').load()")
        print("依赖：pip install beautifulsoup4\n")


def demo_arxiv_loader() -> None:
    """ArxivLoader：加载 arXiv 论文（需 arxiv 包）。

    实际运行需网络访问。
    """
    print("=" * 60)
    print("【ArxivLoader 加载论文】\n")

    try:
        # 加载一篇经典论文（Attention Is All You Need）
        docs = ArxivLoader(query="1706.03762", load_max_docs=1).load()
        print(f"论文 Document 数量：{len(docs)}")
        for doc in docs:
            print(f"  标题（metadata）：{doc.metadata.get('Title', 'N/A')}")
            print(f"  page_content（前 100 字）：{doc.page_content[:100]}...")
        print()
    except Exception as e:
        print(f"论文加载失败（{e.__class__.__name__}）：可能无网络或缺少 arxiv 包")
        print("用法：ArxivLoader(query='论文ID', load_max_docs=1).load()")
        print("依赖：pip install arxiv\n")


def demo_directory_loader() -> None:
    """DirectoryLoader：批量加载目录下所有文件。"""
    print("=" * 60)
    print("【DirectoryLoader 批量加载目录】\n")

    prepare_sample_dir()
    dir_path = DATA_DIR / "articles"

    loader = DirectoryLoader(
        str(dir_path),
        glob="**/*.txt",          # 匹配所有 txt
        loader_cls=TextLoader,    # 用 TextLoader 加载
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    print(f"目录：{dir_path}")
    print(f"加载 Document 数量：{len(docs)}（3 个 txt 文件 = 3 个 Document）")
    for i, doc in enumerate(docs):
        print(f"  [{i}] page_content：{doc.page_content}")
        print(f"      metadata（来源）：{doc.metadata.get('source', 'N/A')}")
    print()


class WebDocumentLoader:
    """网页文档加载器封装。"""

    @staticmethod
    def load_url(url: str) -> list[Document]:
        """加载单个网页。"""
        return WebBaseLoader(url).load()

    @staticmethod
    def load_urls(urls: list[str]) -> list[Document]:
        """批量加载多个网页。"""
        loader = WebBaseLoader(urls)
        return loader.load()

    @staticmethod
    def load_arxiv(query: str, max_docs: int = 1) -> list[Document]:
        """加载 arXiv 论文。"""
        return ArxivLoader(query=query, load_max_docs=max_docs).load()


def demo_web_loader_class() -> None:
    """演示 WebDocumentLoader 封装类的用法。"""
    print("=" * 60)
    print("【WebDocumentLoader 封装类】\n")

    print("WebDocumentLoader 提供：")
    print("  - load_url(url)：加载单个网页")
    print("  - load_urls(urls)：批量加载多个网页")
    print("  - load_arxiv(query)：加载 arXiv 论文")
    print("\n示例（需网络）：")
    print("  docs = WebDocumentLoader.load_url('https://...')")
    print("  docs = WebDocumentLoader.load_arxiv('1706.03762')\n")


def demo_metadata_comparison() -> None:
    """对比不同 Loader 的 metadata 差异。"""
    print("=" * 60)
    print("【不同 Loader 的 metadata 对比】\n")

    # TextLoader metadata
    txt_path = DATA_DIR / "intro.txt"
    txt_path.write_text("测试文本", encoding="utf-8")
    txt_docs = TextLoader(str(txt_path), encoding="utf-8").load()

    # DirectoryLoader metadata
    dir_path = DATA_DIR / "articles"
    dir_loader = DirectoryLoader(
        str(dir_path), glob="**/*.txt", loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    dir_docs = dir_loader.load()

    print(f"{'Loader':<22}{'metadata 字段':<30}{'说明'}")
    print("-" * 70)
    print(f"{'TextLoader':<22}{str(list(txt_docs[0].metadata.keys())):<30}{'来源文件路径'}")
    print(f"{'DirectoryLoader':<22}{str(list(dir_docs[0].metadata.keys())):<30}{'来源文件路径'}")
    print(f"{'CSVLoader':<22}{'[source, row]':<30}{'来源路径+行号'}")
    print(f"{'PyPDFLoader':<22}{'[source, page]':<30}{'来源路径+页码'}")
    print(f"{'WebBaseLoader':<22}{'[source]':<30}{'URL'}")
    print(f"{'ArxivLoader':<22}{'[source, Title, ...]':<30}{'论文元信息'}\n")


def main() -> None:
    demo_web_loader()
    demo_arxiv_loader()
    demo_directory_loader()
    demo_web_loader_class()
    demo_metadata_comparison()
    print("=" * 60)
    print("网页与在线文档加载演示完成。")


if __name__ == "__main__":
    main()
