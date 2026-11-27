# -*- coding: utf-8 -*-
"""
文件用途：LlamaIndex Settings 全局配置
---------------------------------------
Settings 是 LlamaIndex 的全局配置对象，集中管理所有组件的默认实例，
是"一处配置、全局生效"的关键。

本示例用 SettingsConfig 类封装三类典型配置：
1. Settings.llm          → 配置全局 LLM（ChatOpenAI）
2. Settings.embed_model  → 配置全局 Embedding 模型（OpenAIEmbedding）
3. Settings.node_parser  → 配置默认切分器（SentenceSplitter）
4. Settings.show_progress → 是否显示进度条

同时演示：配置前 vs 配置后的差异，以及未配置时的默认行为。

运行：
    python 03_settings.py
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class SettingsConfig:
    """封装 LlamaIndex 全局 Settings 的配置操作。"""

    def __init__(self, llm_model: str = "gpt-4o-mini",
                 embedding_model: str = "text-embedding-3-small",
                 chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        from llama_index.core import Settings

        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.settings = Settings  # 保存 Settings 单例引用

    # ---------- 1. 检查当前是否已有 Key ----------
    @staticmethod
    def has_credentials() -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    # ---------- 2. 展示未配置时的默认行为 ----------
    @staticmethod
    def print_defaults() -> None:
        from llama_index.core import Settings

        def _safe(model_attr: str) -> str:
            # 新版 Settings 在“未显式配置”时访问 .llm/.embed_model 会触发默认解析，
            # 可能因缺少依赖/Key 抛异常，故加降级保护。
            try:
                return type(getattr(Settings, model_attr)).__name__
            except Exception:  # noqa: BLE001
                return "(未配置，使用默认)"

        print("[配置前：默认行为]")
        print(f"  - Settings.llm 默认类型: {_safe('llm')}")
        print(f"  - Settings.embed_model 默认类型: {_safe('embed_model')}")
        print(f"  - Settings.show_progress 默认: {Settings.show_progress}")
        print("  说明：未配置时 LlamaIndex 会使用框架默认('openai' llm 等)，"
              "通常依赖 OPENAI_API_KEY；无 Key/依赖时访问可能报错，已自动降级。\n")

    # ---------- 3. 应用全局配置 ----------
    def configure(self) -> None:
        from llama_index.core import Settings
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.llms.openai import OpenAI
        from llama_index.embeddings.openai import OpenAIEmbedding

        print("[配置中：统一设置全局组件]")
        # 3.1 配置 LLM
        Settings.llm = OpenAI(model=self.llm_model, temperature=0.1)
        print(f"  - Settings.llm          = OpenAI(model={self.llm_model})")
        # 3.2 配置 Embedding
        Settings.embed_model = OpenAIEmbedding(model=self.embedding_model)
        print(f"  - Settings.embed_model   = OpenAIEmbedding(model={self.embedding_model})")
        # 3.3 配置默认切分器
        Settings.node_parser = SentenceSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        print(f"  - Settings.node_parser   = SentenceSplitter(chunk_size={self.chunk_size}, "
              f"chunk_overlap={self.chunk_overlap})")
        # 3.4 进度条
        Settings.show_progress = True
        print(f"  - Settings.show_progress = True")
        print()

    # ---------- 4. 展示配置后生效的默认实例 ----------
    def print_after(self) -> None:
        print("[配置后：默认实例已更新]")
        # 从配置里取 llm 的 model，无需联网
        llm = self.settings.llm
        embed = self.settings.embed_model
        parser = self.settings.node_parser
        print(f"  - Settings.llm 实例类   : {type(llm).__name__} "
              f"(model={getattr(llm, 'model', '?')})")
        print(f"  - Settings.embed_model   : {type(embed).__name__} "
              f"(embed_batch_size={getattr(embed, 'embed_batch_size', '?')})")
        print(f"  - Settings.node_parser   : {type(parser).__name__} "
              f"(chunk_size={getattr(parser, 'chunk_size', '?')})")
        print("  - 此后所有 index/query 默认使用这些配置。\n")

    # ---------- 5. 用配置后的 node_parser 做一次真实切分演示 ----------
    def demo_split(self) -> None:
        from llama_index.core.schema import Document

        long_text = (
            "LlamaIndex 是一个连接 LLM 与私有数据的框架。"
            "它通过加载数据、解析节点、构建索引来支持检索问答。"
            "Settings 提供了全局性的默认配置，让组件复用以减少重复代码。"
            * 10  # 重复多段，让文本足够长以便切分
        )
        doc = Document(text=long_text)
        nodes = self.settings.node_parser.get_nodes_from_documents([doc])
        print(f"[切分演示] 一段 {len(long_text)} 字符的文档，"
              f"被切分为 {len(nodes)} 个 Node：")
        for i, node in enumerate(nodes):
            print(f"  - Node[{i}] 长度 {len(node.get_text())} 字符 | "
                  f"{node.get_text()[:30]}...")


def main() -> None:
    cfg = SettingsConfig()

    # 1) 配置前行为
    SettingsConfig.print_defaults()

    # 2) 若无 Key，给出降级说明但仍演示切分（node_parser 无需联网）
    if not SettingsConfig.has_credentials():
        print("[提示] 未配置 OPENAI_API_KEY，LLM / Embedding 在线能力受限；")
        print("       切分(node_parser)与配置展示不受影响，可离线运行。\n")

    # 3) 应用配置（若未安装 openai 集成包也会触发 ImportError，统一降级）
    try:
        cfg.configure()
        cfg.print_after()
    except Exception as e:  # noqa: BLE001
        print(f"\n[提示] 在线模型配置不可用（{e}），跳过 LLM/Embedding 配置。")
        print("        仍可直接运行 demo_split 验证默认 node_parser 切分。\n")
        try:
            cfg.demo_split()
        except Exception as e2:  # noqa: BLE001
            print(f"        切分演示亦不可用：{e2}")
        return

    # 4) 用配置后的默认 node_parser 做切分演示
    cfg.demo_split()


if __name__ == "__main__":
    main()