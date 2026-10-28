# -*- coding: utf-8 -*-
"""
Day09 - 03 LlamaIndex 集成

模板：用 LlamaIndex 的 Ollama LLM + OllamaEmbedding 建索引做文档问答。
需要 `pip install llama-index llama-index-llms-ollama llama-index-embeddings-ollama`。
未安装/无环境时打印结构说明。
"""


def template() -> str:
    return r'''
# ---- 真实接入模板 ----
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# 1) 设置底座
Settings.llm = Ollama(model="llama3.1")
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# 2) 文档 -> 索引
doc = Document(text="退货政策：签收7天内可无理由退货，退款3-5个工作日原路退回。")
index = VectorStoreIndex.from_documents([doc])

# 3) 查询引擎
engine = index.as_query_engine()
print(engine.query("退款要多久？"))
'''


def main():
    print(">> LlamaIndex 集成（模板）\n")
    print("依赖：pip install llama-index llama-index-llms-ollama "
          "llama-index-embeddings-ollama")
    try:
        import llama_index  # noqa
        print("  已安装 llama-index 核心 ✓")
    except ImportError:
        print("  未安装 llama-index，当前打印结构说明。")
    print("\nLlamaIndex 用 Settings 统一配置底座，一行切云/本地：")
    print(template())
    print("→ Settings.llm / Settings.embed_model 换成本地 Ollama，实现数据不出本地。")


if __name__ == "__main__":
    main()