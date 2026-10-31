# Day04 - 嵌入 Embedding 与向量化 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_embedding_basics.py` | 嵌入调用 + 余弦相似度 + query/doc 区分 | 是（可降级） |
| `02_model_compare.py` | 不同嵌入模型维度与相关性对比 | 是（可降级） |
| `03_batch_cache.py` | 批量嵌入 + 内存缓存命中演示 | 是（可降级） |
| `04_embedding_quality.py` | 相似/不相关对的嵌入质量检验 | 是（可降级） |

## 运行

```bash
python 01_embedding_basics.py
python 02_model_compare.py
python 03_batch_cache.py
python 04_embedding_quality.py
```

> 全部脚本在配置 `OPENAI_API_KEY` 时走真实嵌入；否则降级为本地哈希向量（仅演示流程，无真实语义）。
> `02` 额外支持本地 `BAAI/bge-small-zh-v1.5`（需 `pip install sentence-transformers`）。

## 依赖

```bash
pip install langchain-openai python-dotenv
# 本地模型（可选）
pip install sentence-transformers
```