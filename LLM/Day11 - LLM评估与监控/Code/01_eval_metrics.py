# 文件用途：评估指标计算
# EvalMetrics 类：计算准确性 / 相关性 / 格式合规率
# 支持精确匹配 / 包含匹配 / 正则匹配 / JSON Schema 验证
# 含 BLEU / ROUGE 分数计算，多维度评估报告生成
# Python 3.10+ 可运行（BLEU/ROUGE 用纯标准库实现简化版）

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricResult:
    """单项指标结果。"""

    name: str
    value: float
    detail: dict[str, Any] = field(default_factory=dict)


class EvalMetrics:
    """LLM 评估指标计算器。"""

    # ---------- 准确性 ----------
    @staticmethod
    def exact_match(prediction: str, reference: str) -> bool:
        """精确匹配（忽略首尾空白与大小写）。"""
        return prediction.strip().lower() == reference.strip().lower()

    @staticmethod
    def contains_match(prediction: str, reference: str) -> bool:
        """包含匹配：参考答案是否出现在预测中。"""
        return reference.strip().lower() in prediction.strip().lower()

    @staticmethod
    def regex_match(prediction: str, pattern: str) -> bool:
        """正则匹配。"""
        return re.search(pattern, prediction) is not None

    @staticmethod
    def accuracy(
        predictions: list[str],
        references: list[str],
        match_type: str = "contains",
    ) -> MetricResult:
        """计算准确率。

        match_type: exact / contains
        """
        if len(predictions) != len(references):
            raise ValueError("predictions 与 references 长度不一致")
        if not predictions:
            return MetricResult("accuracy", 0.0)

        match_fn = {
            "exact": EvalMetrics.exact_match,
            "contains": EvalMetrics.contains_match,
        }.get(match_type, EvalMetrics.contains_match)

        correct = sum(
            1 for p, r in zip(predictions, references) if match_fn(p, r)
        )
        value = correct / len(predictions)
        return MetricResult(
            "accuracy",
            value,
            {"correct": correct, "total": len(predictions), "match_type": match_type},
        )

    # ---------- 格式合规 ----------
    @staticmethod
    def format_compliance(
        predictions: list[str],
        pattern: str | None = None,
        require_json: bool = False,
    ) -> MetricResult:
        """格式合规率。"""
        if not predictions:
            return MetricResult("format_compliance", 0.0)

        compliant = 0
        for pred in predictions:
            ok = bool(pred.strip())
            if pattern and not re.search(pattern, pred):
                ok = False
            if require_json:
                try:
                    json.loads(pred)
                except (json.JSONDecodeError, TypeError):
                    ok = False
            if ok:
                compliant += 1

        value = compliant / len(predictions)
        return MetricResult(
            "format_compliance",
            value,
            {"compliant": compliant, "total": len(predictions)},
        )

    @staticmethod
    def json_schema_check(
        prediction: str, required_keys: list[str]
    ) -> bool:
        """检查 JSON 输出是否包含必需字段。"""
        try:
            data = json.loads(prediction)
        except (json.JSONDecodeError, TypeError):
            return False
        return all(k in data for k in required_keys)

    # ---------- BLEU ----------
    @staticmethod
    def _ngrams(tokens: list[str], n: int) -> Counter:
        """计算 n-gram 频次。"""
        return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))

    @staticmethod
    def bleu_score(
        prediction: str, reference: str, max_n: int = 4
    ) -> float:
        """简化版 BLEU 分数（几何平均 + brevity penalty）。"""
        pred_tokens = prediction.lower().split()
        ref_tokens = reference.lower().split()

        if not pred_tokens:
            return 0.0

        # brevity penalty
        bp = 1.0 if len(pred_tokens) >= len(ref_tokens) else (
            1.0 if len(ref_tokens) == 0 else
            min(1.0, len(pred_tokens) / max(1, len(ref_tokens)))
        )

        precisions: list[float] = []
        for n in range(1, max_n + 1):
            pred_ngrams = EvalMetrics._ngrams(pred_tokens, n)
            ref_ngrams = EvalMetrics._ngrams(ref_tokens, n)
            if not pred_ngrams:
                precisions.append(0.0)
                continue
            overlap = sum((pred_ngrams & ref_ngrams).values())
            total = sum(pred_ngrams.values())
            precisions.append(overlap / total if total > 0 else 0.0)

        # 几何平均
        if any(p == 0 for p in precisions):
            return 0.0
        geo_mean = 1.0
        for p in precisions:
            geo_mean *= p
        geo_mean = geo_mean ** (1.0 / max_n)
        return bp * geo_mean

    @staticmethod
    def corpus_bleu(
        predictions: list[str], references: list[str], max_n: int = 4
    ) -> MetricResult:
        """语料级 BLEU。"""
        if len(predictions) != len(references):
            raise ValueError("长度不一致")
        scores = [
            EvalMetrics.bleu_score(p, r, max_n)
            for p, r in zip(predictions, references)
        ]
        avg = sum(scores) / len(scores) if scores else 0.0
        return MetricResult("bleu", avg, {"max_n": max_n, "samples": len(scores)})

    # ---------- ROUGE ----------
    @staticmethod
    def rouge_n(
        prediction: str, reference: str, n: int = 1
    ) -> float:
        """简化版 ROUGE-N 召回率。"""
        pred_tokens = prediction.lower().split()
        ref_tokens = reference.lower().split()
        pred_ngrams = EvalMetrics._ngrams(pred_tokens, n)
        ref_ngrams = EvalMetrics._ngrams(ref_tokens, n)

        if not ref_ngrams:
            return 0.0
        overlap = sum((pred_ngrams & ref_ngrams).values())
        total = sum(ref_ngrams.values())
        return overlap / total if total > 0 else 0.0

    @staticmethod
    def rouge_l(prediction: str, reference: str) -> float:
        """简化版 ROUGE-L（最长公共子序列）。"""
        pred_tokens = prediction.lower().split()
        ref_tokens = reference.lower().split()
        if not pred_tokens or not ref_tokens:
            return 0.0

        m, n = len(pred_tokens), len(ref_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if pred_tokens[i - 1] == ref_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        lcs = dp[m][n]
        recall = lcs / n
        precision = lcs / m
        if recall + precision == 0:
            return 0.0
        return 2 * recall * precision / (recall + precision)

    @staticmethod
    def corpus_rouge(
        predictions: list[str], references: list[str]
    ) -> MetricResult:
        """语料级 ROUGE（ROUGE-1/ROUGE-2/ROUGE-L 平均）。"""
        if len(predictions) != len(references):
            raise ValueError("长度不一致")
        r1, r2, rl = [], [], []
        for p, r in zip(predictions, references):
            r1.append(EvalMetrics.rouge_n(p, r, 1))
            r2.append(EvalMetrics.rouge_n(p, r, 2))
            rl.append(EvalMetrics.rouge_l(p, r))
        detail = {
            "rouge_1": sum(r1) / len(r1) if r1 else 0,
            "rouge_2": sum(r2) / len(r2) if r2 else 0,
            "rouge_l": sum(rl) / len(rl) if rl else 0,
        }
        avg = sum(detail.values()) / 3
        return MetricResult("rouge", avg, detail)

    # ---------- 综合报告 ----------
    @staticmethod
    def evaluate(
        predictions: list[str],
        references: list[str],
        match_type: str = "contains",
        format_pattern: str | None = None,
    ) -> dict[str, Any]:
        """生成多维度评估报告。"""
        results: list[MetricResult] = [
            EvalMetrics.accuracy(predictions, references, match_type),
            EvalMetrics.format_compliance(predictions, format_pattern),
            EvalMetrics.corpus_bleu(predictions, references),
            EvalMetrics.corpus_rouge(predictions, references),
        ]
        return {
            "samples": len(predictions),
            "metrics": {r.name: round(r.value, 4) for r in results},
            "details": {r.name: r.detail for r in results},
        }

    @staticmethod
    def print_report(report: dict[str, Any]) -> None:
        """打印评估报告。"""
        print("\n" + "=" * 50)
        print("评估指标报告")
        print("=" * 50)
        print(f"样本数: {report['samples']}")
        print("-" * 50)
        for name, value in report["metrics"].items():
            print(f"  {name:<20} {value:.4f}")
        print("-" * 50)
        for name, detail in report["details"].items():
            print(f"  [{name}] {detail}")


def demo_metrics() -> None:
    """演示评估指标计算。"""
    predictions = [
        "AISearch 支持 PDF、Word、Markdown 等格式。",
        "RAG 通过检索增强生成，提高准确性。",
        "向量数据库用于存储和检索 embedding。",
    ]
    references = [
        "PDF",
        "检索增强生成",
        "embedding",
    ]

    # 准确性
    acc = EvalMetrics.accuracy(predictions, references, match_type="contains")
    print(f"准确率（包含匹配）: {acc.value:.2%}")

    # 格式合规
    fmt = EvalMetrics.format_compliance(predictions)
    print(f"格式合规率: {fmt.value:.2%}")

    # BLEU
    for p, r in zip(predictions, references):
        bleu = EvalMetrics.bleu_score(p, r)
        print(f"BLEU: {bleu:.4f}  (pred: {p[:30]}...)")

    # ROUGE
    for p, r in zip(predictions, references):
        rouge = EvalMetrics.rouge_l(p, r)
        print(f"ROUGE-L: {rouge:.4f}")

    # 综合报告
    report = EvalMetrics.evaluate(predictions, references)
    EvalMetrics.print_report(report)

    # JSON 格式检查
    json_preds = ['{"answer": "是", "score": 5}', "不是 JSON", '{"answer": "否"}']
    json_ok = EvalMetrics.format_compliance(json_preds, require_json=True)
    print(f"\nJSON 合规率: {json_ok.value:.2%}")

    schema_ok = EvalMetrics.json_schema_check(
        '{"answer": "是", "score": 5}', required_keys=["answer", "score"]
    )
    print(f"Schema 检查: {schema_ok}")


if __name__ == "__main__":
    demo_metrics()
