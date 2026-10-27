# Code 说明

本目录为「Day07 - 嵌入模型与向量检索」的可执行代码。

- 01_embedding_intro.py  嵌入与余弦相似度
- 02_semantic_search.py  本地语义搜索（top-k）
- 03_doc_chunk.py        文档切块与入库
- 04_rag_embed.py        嵌入驱动的完整检索链路
- ollama_util.py         双模式共用（含 embed_wrapper）

运行方式：

```bash
python 01_embedding_intro.py
python 02_semantic_search.py
python 03_doc_chunk.py
python 04_rag_embed.py
```

> 有真实嵌入模型时走真实向量；无环境用伪向量兜底，语义检索逻辑保持不变。