# Day03 - 文本切块 Chunking 策略 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_fixed_splitter.py` | 固定大小切块及语义断裂演示 | 否 |
| `02_recursive_splitter.py` | 递归字符切块（多分隔符） | 否 |
| `03_semantic_splitter.py` | 语义切块（嵌入版 + 降级） | 是（可降级） |
| `04_chunking_tune.py` | chunk_size / overlap 参数量化对比 | 否 |

## 运行

```bash
python 01_fixed_splitter.py
python 02_recursive_splitter.py
python 03_semantic_splitter.py
python 04_chunking_tune.py
```

> `03` 配置 `OPENAI_API_KEY` 时走语义嵌入切块，否则降级为启发式。

## 依赖

```bash
pip install langchain-text-splitters   # 01/02/04 必需
pip install langchain-experimental langchain-openai   # 03 语义切块（可选）
```