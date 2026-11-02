# Day10 - RAG 质量评估 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_retrieval_metrics.py` | Recall / Precision / MRR / nDCG | 否 |
| `02_generation_metrics.py` | 忠实性 / 相关性判定逻辑 | 否 |
| `03_ragas_eval.py` | 用 RAGAS 端到端评估 | 是（需 LLM） |
| `04_eval_dataset.py` | 构建评估数据集 JSON | 否 |

## 运行

```bash
python 01_retrieval_metrics.py
python 02_generation_metrics.py
python 04_eval_dataset.py        # 生成 eval_dataset.json
python 03_ragas_eval.py          # 配置 OPENAI_API_KEY 后
```

## 依赖

```bash
# RAGAS（03 专用）
pip install ragas datasets
# 其余仅需 Python 标准库（或 langchain-openai）
```