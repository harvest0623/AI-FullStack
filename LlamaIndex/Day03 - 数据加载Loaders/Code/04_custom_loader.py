# -*- coding: utf-8 -*-
"""
文件用途：自定义 Loader（继承 BaseReader）
------------------------------------------
LlamaIndex 的 Loader 统一继承 BaseReader 并实现 load_data()，
返回 List[Document]。这样无论数据源多"特别"，都能无缝接入
后续的 Parse → Index → Query 管道。

本示例用 CustomLoaderDemo 演示：
1. 继承 BaseReader 的自定义 Loader
2. 自定义数据源：模拟"本地 JSON 目录 / 假 API"
3. 把自定义 Loader 产出的 Document 交给 SimpleDirectoryReader 风格或直接使用
4. 注册使用（作为任何 Reader 普通调用）

运行：
    python 04_custom_loader.py
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------
# 步骤 1：实现一个模拟 API / JSON 目录数据源（demo 用，非 LlamaIndex 代码）
# ---------------------------------------------------------------
class LocalDocSource:
    """模拟一个"内部文档目录/API"，返回原始 dict 列表。"""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def ensure_seed(self) -> None:
        seed_file = self.base_dir / "knowledge.json"
        if not seed_file.exists():
            seed = [
                {"title": "DataIQ 部署手册", "department": "技术部",
                 "body": "推荐使用 Docker 部署 DataIQ，端口映射 8000。"},
                {"title": "员工报销须知", "department": "财务部",
                 "body": "报销需附发票照片，5 个工作日内审批。"},
            ]
            seed_file.write_text(
                json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")

    def fetch_docs(self) -> List[Dict[str, Any]]:
        """假装从远程 API 拉取，实质读取本地 JSON 文件。"""
        self.ensure_seed()
        return json.loads((self.base_dir / "knowledge.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------
# 步骤 2：自定义 Loader —— 继承 BaseReader（若未安装 llama_index 则降级提示）
# ---------------------------------------------------------------
try:
    from llama_index.core.readers.base import BaseReader
    from llama_index.core.schema import Document
    LLAMA_INDEX_OK = True
except ModuleNotFoundError:  # pragma: no cover
    BaseReader = object  # 占位，避免 import 级崩溃
    Document = None
    LLAMA_INDEX_OK = False


class CompanyDocReader(BaseReader):
    """从内部数据源加载企业文档的自定义 Reader。

    关键点：实现 load_data(*args, **kwargs) -> List[Document]。
    """

    def __init__(self, source: LocalDocSource, title_prefix: str = "DataIQ") -> None:
        self.source = source
        self.title_prefix = title_prefix
        super().__init__()

    def load_data(self, *args: Any, **kwargs: Any) -> List[Document]:
        items = self.source.fetch_docs()  # 拿原始数据
        docs: List[Document] = []
        for it in items:
            text = f"【{it['title']}】\n{it['body']}"
            metadata = {
                "source": "custom-company-api",
                "title": it["title"],
                "department": it["department"],
                "is_custom": True,
            }
            docs.append(Document(text=text, metadata=metadata))
        return docs


# ---------------------------------------------------------------
# 步骤 3：自定义 Loader 的使用与注册
# ---------------------------------------------------------------
class CustomLoaderDemo:
    """演示自定义 Loader 的接入方式。"""

    @staticmethod
    def run() -> None:
        data_dir = Path(__file__).parent / "data"
        source = LocalDocSource(data_dir)
        reader = CompanyDocReader(source)

        print("[1] 直接调用自定义 Loader 的 load_data()：")
        docs = reader.load_data()
        for d in docs:
            print(f"    - {d.metadata.get('title')} "
                  f"[部门={d.metadata.get('department')}]")
            print(f"      text: {d.text[:40]}...")

        print("\n[2] 自定义 Loader 作为普通 Reader 使用（接入后续管道）：")

        # 无需联网也能演示：仅构造成"可直接喂给 index"的 Document 集合
        print(f"    共产生 {len(docs)} 个 Document，"
              f"包含 metadata={list(docs[0].metadata.keys())}")
        print("    说明：这些 Document 之后可继续传给 Node Parser / Index。")

        # 注册使用：可在后续从 nodes 直接构建，这里演示思路
        print("\n[3] 扩展性说明：")
        print("     - 继承 BaseReader + 实现 load_data() 即可接入 LlamaIndex")
        print("     - 同一 Reader 可用于不同数据源，返回统一 Document 结构")
        print("     - 也常配合 IngestionPipeline/Index 直接使用")


if __name__ == "__main__":
    print("=" * 60)
    print("自定义 Loader 演示（继承 BaseReader）")
    print("=" * 60)
    if not LLAMA_INDEX_OK:  # pragma: no cover
        print("[提示] 未安装 llama_index，需先执行：pip install llama-index")
    else:
        CustomLoaderDemo.run()
    print("=" * 60)