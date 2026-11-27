# -*- coding: utf-8 -*-
"""
文件用途：网页与字符串 / JSON 加载
-----------------------------------
除本地文件外，LlamaIndex 还能从网页与字符串直接加载数据：
1. WebPageReader  —— 加载网页正文
2. StringReader   —— 把字符串直接转为 Document
3. JSONReader     —— 读取 JSON 数据（来自 llama-index-readers-json）

用 WebAndStringReader 类封装示例。网页加载需联网，失败时降级演示。

运行：
    python 03_web_reader.py
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class WebAndStringReader:
    """从网页、字符串、JSON 三种来源加载数据。"""

    # ---------- 1. StringReader：字符串 → Document ----------
    @staticmethod
    def from_string() -> None:
        from llama_index.core import Document

        print("[1] StringReader（字符串直接加载，无需联网）")
        text = "这是 DataIQ 的一条内部通知：系统将于本周日凌晨进行维护升级。"
        # LlamaIndex 中直接把字符串包成 Document 即为最简"StringReader"
        doc = Document(text=text, metadata={"source": "string", "type": "notice"})
        print(f"   → 生成 1 个 Document，text: {doc.text}")
        print(f"   → metadata: {doc.metadata}\n")

    # ---------- 2. JSONReader：JSON 文件 → Document ----------
    @staticmethod
    def from_json() -> None:
        import json
        from pathlib import Path

        print("[2] JSONReader（JSON 数据加载）")
        path = Path(__file__).parent / "data" / "sample.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                json.dumps({
                    "title": "DataIQ FAQ",
                    "items": [
                        {"q": "支持哪些文档？", "a": "PDF/Word/MD/CSV"},
                        {"q": "如何授权？", "a": "管理员后台配置"},
                    ],
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        try:
            from llama_index.readers.file import JSONReader
            reader = JSONReader()
            docs = reader.load_data(input_file=str(path))
            print(f"   → JSONReader 产生 {len(docs)} 个 Document")
            for d in docs:
                print(f"     - {d.text[:50].replace(chr(10), ' ')}...")
        except Exception as e:  # noqa: BLE001
            print(f"   → 读取失败（可pip install llama-index-readers-json）：{e}")
        print()

    # ---------- 3. WebPageReader：网页加载 ----------
    @staticmethod
    def from_web(url: str) -> None:
        print(f"[3] WebPageReader（网页加载）：{url}")
        try:
            from llama_index.readers.web import WebPageReader
            reader = WebPageReader(html_to_text=True)
            docs = reader.load_data(urls=[url])
            print(f"   → 获取 {len(docs)} 个 Document")
            for d in docs:
                print(f"     标题/片段: {d.text[:60].strip()[:60]}...")
                print(f"     metadata: {d.metadata}")
        except Exception as e:  # noqa: BLE001
            print(f"   → 网页加载需要联网，当前降级：{type(e).__name__}：{e}")


def main() -> None:
    print("=" * 60)
    print("网页 / 字符串 / JSON 加载演示")
    print("=" * 60)

    WebAndStringReader.from_string()
    WebAndStringReader.from_json()
    WebAndStringReader.from_web("https://example.com")

    print("=" * 60)
    print("小结：Loader 的来源 = 文件 + 网页 + 字符串/内存数据 + API/数据库")
    print("=" * 60)


if __name__ == "__main__":
    main()