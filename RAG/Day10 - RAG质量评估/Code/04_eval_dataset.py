# -*- coding: utf-8 -*-
"""
文件用途：Day10 - 04 构建评估数据集
演示如何构造一份"小而覆盖难例"的 RAG 评估集 JSON，
含 question / reference / retrieved_contexts / 备注。

运行：python 04_eval_dataset.py（无需联网，输出 eval_dataset.json）
"""

import json


def build_eval_set():
    return [
        {"question": "住宿报销每天上限多少？",
         "ground_truth": "每日500元",
         "retrieved_contexts": ["住宿每日上限500元，超出部分自理"],
         "note": "事实型基础题"},
        {"question": "伙计，出差回来咋报销啊？",
         "ground_truth": "5个工作日内提交申请附发票",
         "retrieved_contexts": ["报销需在出差结束后5个工作日内提交，附发票"],
         "note": "口语化/需查询改写"},
        {"question": "DATA-PRO2024 支持云闪付吗？",
         "ground_truth": "支持",
         "retrieved_contexts": ["DATA-PRO-2024 支持支付宝与云闪付支付"],
         "note": "专有名词，考验混合检索"},
        {"question": "年假能结转么，又和病假冲突么？",
         "ground_truth": "年假不跨年结转；病假不计入年假，不冲突",
         "retrieved_contexts": ["年假每年15天，不允许跨年结转", "病假需医院证明，不计入年假"],
         "note": "复合问题，考验查询分解"},
        {"question": "财务部的报销审核流程是什么？",
         "ground_truth": "需附发票在5个工作日内提交",
         "retrieved_contexts": ["报销需在出差结束后5个工作日内提交，附发票"],
         "note": "元数据/部门过滤验证"},
    ]


def main() -> None:
    evals = build_eval_set()
    with open("eval_dataset.json", "w", encoding="utf-8") as f:
        json.dump(evals, f, ensure_ascii=False, indent=2)
    print(f"已生成 {len(evals)} 条评估数据 → eval_dataset.json")
    print("覆盖难点分类：")
    for e in evals:
        print(f"  - {e['note']}: {e['question']}")


if __name__ == "__main__":
    main()