# 文件用途：微调效果评估
# FinetuneEvaluator 类：加载微调前后模型 → 在测试集上对比 → 生成评估报告
# 评估维度：任务准确率 / 格式合规率 / 通用能力检测（MMLU子集）/ 灾难性遗忘检测
# 含报告生成
# Python 3.10+ 可运行
# 依赖：pip install openai（需可连接的本地或 API 模型服务）

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


@dataclass
class ModelSpec:
    """被评估模型规格。"""

    name: str
    base_url: str
    api_key: str
    model: str


@dataclass
class EvalResult:
    """单个问题的评估结果。"""

    question: str
    expected: str
    answer: str
    is_correct: bool
    format_ok: bool
    latency: float
    status: str = "success"


@dataclass
class ModelEvalReport:
    """单个模型的评估报告。"""

    model_name: str
    task_accuracy: float = 0.0
    format_compliance: float = 0.0
    avg_latency: float = 0.0
    general_ability: float = 0.0  # 通用能力得分（0-1）
    details: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "task_accuracy": round(self.task_accuracy, 4),
            "format_compliance": round(self.format_compliance, 4),
            "avg_latency": round(self.avg_latency, 3),
            "general_ability": round(self.general_ability, 4),
            "details_count": len(self.details),
        }


class FinetuneEvaluator:
    """微调效果评估器，对比微调前后模型表现。"""

    def __init__(self, before: ModelSpec, after: ModelSpec) -> None:
        if OpenAI is None:
            raise ImportError("未安装 openai 包，请执行: pip install openai")
        self.before = before
        self.after = after
        self._clients = {
            "before": OpenAI(base_url=before.base_url, api_key=before.api_key),
            "after": OpenAI(base_url=after.base_url, api_key=after.api_key),
        }

    def _call_model(self, which: str, prompt: str, system: str = "") -> tuple[str, float]:
        """调用模型，返回 (回答, 延迟)。"""
        client = self._clients[which]
        spec = self.before if which == "before" else self.after
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.time()
        resp = client.chat.completions.create(
            model=spec.model,
            messages=messages,
            temperature=0.0,
            max_tokens=512,
        )
        elapsed = time.time() - start
        return resp.choices[0].message.content or "", elapsed

    @staticmethod
    def _check_correct(answer: str, expected: str) -> bool:
        """简单准确性检查：包含匹配（忽略大小写与首尾空白）。"""
        return expected.strip().lower() in answer.strip().lower()

    @staticmethod
    def _check_format(answer: str, pattern: str | None = None) -> bool:
        """格式合规检查。"""
        if not answer.strip():
            return False
        if pattern and not re.search(pattern, answer):
            return False
        return True

    def eval_task(
        self,
        test_set: list[dict[str, str]],
        format_pattern: str | None = None,
    ) -> tuple[ModelEvalReport, ModelEvalReport]:
        """在任务测试集上评估微调前后模型。"""
        reports = {
            "before": ModelEvalReport(model_name=self.before.name),
            "after": ModelEvalReport(model_name=self.after.name),
        }

        for which in ("before", "after"):
            results: list[EvalResult] = []
            for item in test_set:
                question = item.get("question", item.get("instruction", ""))
                expected = item.get("expected", item.get("output", ""))
                try:
                    answer, latency = self._call_model(
                        which, question, system=item.get("system", "")
                    )
                    is_correct = self._check_correct(answer, expected)
                    fmt_ok = self._check_format(answer, format_pattern)
                    results.append(
                        EvalResult(
                            question=question,
                            expected=expected,
                            answer=answer,
                            is_correct=is_correct,
                            format_ok=fmt_ok,
                            latency=latency,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    results.append(
                        EvalResult(
                            question=question,
                            expected=expected,
                            answer="",
                            is_correct=False,
                            format_ok=False,
                            latency=0.0,
                            status=f"error: {exc}",
                        )
                    )

            # 汇总
            success_results = [r for r in results if r.status == "success"]
            total = len(results)
            report = reports[which]
            report.task_accuracy = (
                sum(1 for r in success_results if r.is_correct) / total if total else 0
            )
            report.format_compliance = (
                sum(1 for r in success_results if r.format_ok) / total if total else 0
            )
            report.avg_latency = (
                sum(r.latency for r in success_results) / len(success_results)
                if success_results
                else 0
            )
            report.details = [
                {
                    "question": r.question,
                    "expected": r.expected,
                    "answer": r.answer[:200],
                    "is_correct": r.is_correct,
                    "format_ok": r.format_ok,
                    "latency": round(r.latency, 3),
                    "status": r.status,
                }
                for r in results
            ]

        return reports["before"], reports["after"]

    def eval_general_ability(
        self, general_set: list[dict[str, str]]
    ) -> tuple[ModelEvalReport, ModelEvalReport]:
        """通用能力检测（MMLU 子集风格），用于判断灾难性遗忘。"""
        return self.eval_task(general_set)

    @staticmethod
    def detect_forgetting(
        before: ModelEvalReport, after: ModelEvalReport, threshold: float = 0.05
    ) -> dict[str, Any]:
        """检测灾难性遗忘。"""
        drop = before.task_accuracy - after.task_accuracy
        has_forgetting = drop > threshold
        return {
            "before_accuracy": round(before.task_accuracy, 4),
            "after_accuracy": round(after.task_accuracy, 4),
            "accuracy_drop": round(drop, 4),
            "has_catastrophic_forgetting": has_forgetting,
            "threshold": threshold,
            "conclusion": (
                "⚠️ 检测到灾难性遗忘，通用能力下降超过阈值"
                if has_forgetting
                else "✅ 未检测到明显灾难性遗忘"
            ),
        }

    def generate_report(
        self,
        task_before: ModelEvalReport,
        task_after: ModelEvalReport,
        general_before: ModelEvalReport,
        general_after: ModelEvalReport,
    ) -> str:
        """生成完整评估报告。"""
        forgetting = self.detect_forgetting(general_before, general_after)
        improvement = task_after.task_accuracy - task_before.task_accuracy

        return f"""# 微调效果评估报告

## 任务能力对比

| 指标 | 微调前({task_before.model_name}) | 微调后({task_after.model_name}) | 变化 |
| --- | --- | --- | --- |
| 任务准确率 | {task_before.task_accuracy:.2%} | {task_after.task_accuracy:.2%} | {improvement:+.2%} |
| 格式合规率 | {task_before.format_compliance:.2%} | {task_after.format_compliance:.2%} | {task_after.format_compliance - task_before.format_compliance:+.2%} |
| 平均延迟 | {task_before.avg_latency:.3f}s | {task_after.avg_latency:.3f}s | {task_after.avg_latency - task_before.avg_latency:+.3f}s |

## 通用能力检测（灾难性遗忘）

| 指标 | 微调前 | 微调后 | 变化 |
| --- | --- | --- | --- |
| 通用准确率 | {general_before.task_accuracy:.2%} | {general_after.task_accuracy:.2%} | {general_after.task_accuracy - general_before.task_accuracy:+.2%} |

**遗忘检测结论：** {forgetting['conclusion']}
- 通用能力下降幅度：{forgetting['accuracy_drop']:.2%}
- 阈值：{forgetting['threshold']:.2%}

## 总结

- {'✅ 微调有效，任务准确率提升 ' + f'{improvement:.2%}' if improvement > 0 else '❌ 微调未带来任务提升，需检查数据或参数'}
- {forgetting['conclusion']}

## 建议

{self._generate_suggestions(improvement, forgetting['has_catastrophic_forgetting'])}
"""

    @staticmethod
    def _generate_suggestions(improvement: float, has_forgetting: bool) -> str:
        """生成优化建议。"""
        suggestions = []
        if improvement < 0:
            suggestions.append("- 任务准确率未提升，建议：检查数据质量、增加数据量、调整学习率")
        elif improvement < 0.1:
            suggestions.append("- 提升幅度较小，建议：增加训练数据多样性、提高 LoRA rank")
        else:
            suggestions.append("- ✅ 任务提升明显，可继续优化或部署上线")

        if has_forgetting:
            suggestions.append("- 存在灾难性遗忘，建议：减少 epochs、降低学习率、混入通用数据")
        else:
            suggestions.append("- ✅ 通用能力保持良好")

        return "\n".join(suggestions)

    def save_report(self, report: str, path: str | Path) -> None:
        """保存评估报告。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"[FinetuneEvaluator] 报告已保存到 {path}")


def build_default_specs() -> tuple[ModelSpec, ModelSpec]:
    """构建默认对比规格：微调前本地 vs 微调后本地。"""
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    before = ModelSpec(
        name="base",
        base_url=ollama_url,
        api_key="ollama",
        model="qwen2.5:7b",
    )
    after = ModelSpec(
        name="finetuned",
        base_url=ollama_url,
        api_key="ollama",
        model="qwen2.5:7b-aisearch",  # 微调后模型名
    )
    return before, after


def build_sample_testset() -> list[dict[str, str]]:
    """构建示例任务测试集。"""
    return [
        {
            "question": "AISearch 支持哪些文档格式？",
            "expected": "PDF",
            "system": "你是 AISearch 智能问答助手。",
        },
        {
            "question": "如何提高 RAG 检索准确率？",
            "expected": "切分",
            "system": "你是 AISearch 智能问答助手。",
        },
    ]


def build_sample_general_set() -> list[dict[str, str]]:
    """构建通用能力测试集（MMLU 子集风格）。"""
    return [
        {"question": "中国的首都是哪个城市？", "expected": "北京"},
        {"question": "1+1 等于几？", "expected": "2"},
        {"question": "水由哪两种元素组成？", "expected": "氢"},
        {"question": "地球绕着什么转？", "expected": "太阳"},
    ]


def demo_eval() -> None:
    """演示微调效果评估流程。"""
    before, after = build_default_specs()
    evaluator = FinetuneEvaluator(before, after)

    print("=== 任务能力评估 ===")
    task_before, task_after = evaluator.eval_task(build_sample_testset())
    print(f"微调前准确率: {task_before.task_accuracy:.2%}")
    print(f"微调后准确率: {task_after.task_accuracy:.2%}")

    print("\n=== 通用能力评估（灾难性遗忘检测）===")
    gen_before, gen_after = evaluator.eval_general_ability(build_sample_general_set())
    print(f"微调前通用准确率: {gen_before.task_accuracy:.2%}")
    print(f"微调后通用准确率: {gen_after.task_accuracy:.2%}")

    print("\n=== 评估报告 ===")
    report = evaluator.generate_report(task_before, task_after, gen_before, gen_after)
    print(report)
    evaluator.save_report(report, "eval_output/finetune_report.md")


if __name__ == "__main__":
    demo_eval()
