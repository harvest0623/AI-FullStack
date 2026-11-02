# Day11 - 生产级 RAG 系统架构 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_arch_design.py` | 索引/检索解耦骨架 | 否 |
| `02_cache_layer.py` | 检索/生成缓存 | 否 |
| `03_observability.py` | 可观测埋点骨架 | 否 |
| `04_fastapi_rag.py` | FastAPI 生产 RAG 服务 | 是（可降级） |

## 运行

```bash
python 01_arch_design.py
python 02_cache_layer.py
python 03_observability.py

# FastAPI 服务
python 04_fastapi_rag.py
# 或
uvicorn 04_fastapi_rag:app --reload --port 8000
```

> `04` 启动后可通过 `POST /query {"question":"..."}` 测试；配置 `OPENAI_API_KEY` 走真实嵌入，否则降级为哈希向量（服务仍可用）。

## 依赖

```bash
pip install fastapi uvicorn pydantic langchain-community faiss-cpu langchain-openai python-dotenv
```