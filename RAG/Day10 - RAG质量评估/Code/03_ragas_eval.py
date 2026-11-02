# -*- coding: utf-8 -*-
"""
文件用途：Day10 - 03 用 RAGAS 评估端到端
RAGAS 用 LLM judge 自动计算 context_precision / context_recall /
faithfulness / answer_relevancy 等指标。

运行：python 03_ragas_eval.py
依赖：ragas langchain-openai langchain-community faiss-cpu
      （需 OPENAI_API_KEY；无 Key 时演示数据构造并提示跳过）
"""

import os
from dotenv import load_dotenv

load_dotenv()


def build_dataset():
    from datasets import Dataset
    return Dataset.from_list([
        {
            "user_input": "住宿报销上限是多少？",
            "response": "住宿每日上限500元。",
            "retrieved_contexts": ["住宿每日上限500元，超出部分自理"],
            "reference": "每日500元",
        },
        {
            "user_input": "年假有几天？",
            "response": "年假每年15天，需提前3天在HR系统提交。",
            "retrieved_contexts": ["年假每年15天，需提前3天在HR系统提交"],
            "reference": "每年15天",
        },
    ])


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("未配置 OPENAI_API_KEY，本文件需真实 LLM 打分，跳过实际评估。")
        print("安装依赖后配置 Key 重跑即可。")
        return
    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness, answer_relevancy, context_precision, context_recall,
        )
    except ImportError as e:
        print(f"缺少依赖：{e}。请安装 ragas、datasets 后再试。")
        return

    dataset = build_dataset()
    print("评估数据集条目数：", len(dataset))
    results = evaluate(dataset, metrics=[
        faithfulness, answer_relevancy, context_precision, context_recall,
    ])
    for name, val in results.items():
        print(f"  {name}: {val:.3f}")


if __name__ == "__main__":
    main()