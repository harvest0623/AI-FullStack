# Day07 - 查询优化与查询路由 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_query_rewrite.py` | 查询改写 + 前后命中对比 | 是（可降级） |
| `02_multi_query.py` | 多查询展开 + 合并去重 | 是（可降级） |
| `03_query_decompose.py` | 复合问题分解子检索 | 是（可降级） |
| `04_query_router.py` | LLM / 关键词查询路由 | 路由支持两种 |

## 运行

```bash
python 01_query_rewrite.py
python 02_multi_query.py
python 03_query_decompose.py
python 04_query_router.py
```

> 01/02/03 配置 `OPENAI_API_KEY` 走 LLM 改写/多查/分解，否则降级为规则；04 有 Key 走 LLM 路由，无 Key 走关键词路由（完全离线可用）。

## 依赖

```bash
pip install openai python-dotenv
```