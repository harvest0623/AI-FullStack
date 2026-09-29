# 文件用途：自动化评估管道
# EvalPipeline 类：加载测试集 → 批量调用被评估模型 → LLM-as-Judge 评分 → 生成评估报告
# 支持定时执行 / 结果历史追踪 / 趋势分析
# 含可视化数据生成
# Python 3.10+ 可运行
# 依赖：pip install openai

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

from dataclasses import dataclass, field

# 复用同目录的 LLMJudge
from llm_judge import LLMJudge, JudgeResult  # type: ignore[import-not-found]


@dataclass
class PipelineConfig:
    """评估管道配置。"""

    target_base_url: str = "http://localhost:11434/v1"
    target_api_key: str = "ollama"
    target_model: str = "qwen2.5:7b"
    judge_model: str = "gpt-4o-mini"
    output_dir: str = "eval_results"
    max_tokens: int = 512


@dataclass
class EvalRun:
    """单次评估运行记录。"""

    run_id: str
    timestamp: str
    model: str
    total: int
    success: int
    avg_scores: dict[str, float] = field(default_factory=dict)
    latency_avg: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "model": self.model,
            "total": self.total,
            "success": self.success,
            "avg_scores": self.avg_scores,
            "latency_avg": round(self.latency_avg, 3),
        }


class EvalPipeline:
    """自动化评估管道。"""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        if OpenAI is None:
            raise ImportError("未安装 openai 包，请执行: pip install openai")
        self.config = config or PipelineConfig()
        self.target_client = OpenAI(
            base_url=self.config.target_base_url,
            api_key=self.config.target_api_key,
        )
        self.judge = LLMJudge(model=self.config.judge_model)
        self.history: list[EvalRun] = []
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_testset(self, path: str | Path) -> list[dict[str, str]]:
        """加载测试集（JSONL 格式）。"""
        path = Path(path)
        items: list[dict[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        print(f"[EvalPipeline] 已加载 {len(items)} 条测试数据")
        return items

    def call_target(self, question: str, system: str = "") -> tuple[str, float]:
        """调用被评估模型。"""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": question})

        start = time.time()
        resp = self.target_client.chat.completions.create(
            model=self.config.target_model,
            messages=messages,
            temperature=0.0,
            max_tokens=self.config.max_tokens,
        )
        elapsed = time.time() - start
        return resp.choices[0].message.content or "", elapsed

    def run(
        self,
        testset: list[dict[str, str]],
        run_id: str | None = None,
    ) -> EvalRun:
        """执行一次完整评估。"""
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now().isoformat()
        print(f"\n[EvalPipeline] 开始评估运行 {run_id}")
        print(f"[EvalPipeline] 被评估模型: {self.config.target_model}")

        # 1. 批量调用被评估模型
        answers: list[dict[str, Any]] = []
        latencies: list[float] = []
        for i, item in enumerate(testset):
            question = item.get("question", item.get("instruction", ""))
            system = item.get("system", "")
            try:
                answer, latency = self.call_target(question, system)
                answers.append(
                    {
                        "question": question,
                        "answer": answer,
                        "reference": item.get("expected", item.get("output", "")),
                        "latency": latency,
                        "status": "success",
                    }
                )
                latencies.append(latency)
            except Exception as exc:  # noqa: BLE001
                answers.append(
                    {
                        "question": question,
                        "answer": "",
                        "reference": item.get("expected", ""),
                        "latency": 0,
                        "status": f"error: {exc}",
                    }
                )
            if (i + 1) % 10 == 0:
                print(f"[EvalPipeline] 已生成回答 {i + 1}/{len(testset)}")

        # 2. LLM-as-Judge 评分
        success_answers = [a for a in answers if a["status"] == "success"]
        judge_items = [
            {
                "question": a["question"],
                "answer": a["answer"],
                "reference": a["reference"],
            }
            for a in success_answers
        ]
        print(f"[EvalPipeline] 开始 LLM-as-Judge 评分（{len(judge_items)} 条）...")
        judge_results: list[JudgeResult] = self.judge.judge_batch(judge_items)

        # 3. 聚合
        agg = LLMJudge.aggregate(judge_results)

        # 4. 记录运行
        run = EvalRun(
            run_id=run_id,
            timestamp=timestamp,
            model=self.config.target_model,
            total=len(testset),
            success=len(success_answers),
            avg_scores=agg.get("avg_scores", {}),
            latency_avg=sum(latencies) / len(latencies) if latencies else 0,
        )
        self.history.append(run)

        # 5. 保存结果
        self._save_run(run, answers, judge_results, agg)

        return run

    def _save_run(
        self,
        run: EvalRun,
        answers: list[dict[str, Any]],
        judge_results: list[JudgeResult],
        agg: dict[str, Any],
    ) -> None:
        """保存单次运行结果。"""
        run_dir = self.output_dir / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 运行摘要
        (run_dir / "summary.json").write_text(
            json.dumps(run.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 详细回答
        (run_dir / "answers.jsonl").write_text(
            "\n".join(json.dumps(a, ensure_ascii=False) for a in answers),
            encoding="utf-8",
        )

        # 评分详情
        (run_dir / "judge_results.jsonl").write_text(
            "\n".join(
                json.dumps(r.to_dict(), ensure_ascii=False) for r in judge_results
            ),
            encoding="utf-8",
        )

        # 评估报告
        report = LLMJudge.generate_report(agg, model_name=run.model)
        (run_dir / "report.md").write_text(report, encoding="utf-8")

        print(f"[EvalPipeline] 结果已保存到 {run_dir}")

    def trend_analysis(self) -> dict[str, Any]:
        """趋势分析：对比多次运行的得分变化。"""
        if len(self.history) < 2:
            return {"info": "至少需要 2 次运行才能进行趋势分析"}

        runs = sorted(self.history, key=lambda r: r.timestamp)
        first = runs[0]
        latest = runs[-1]

        dims = ["accuracy", "relevance", "fluency", "safety", "overall"]
        changes: dict[str, float] = {}
        for dim in dims:
            old = first.avg_scores.get(dim, 0)
            new = latest.avg_scores.get(dim, 0)
            changes[dim] = round(new - old, 2)

        return {
            "runs_count": len(runs),
            "first_run": first.to_dict(),
            "latest_run": latest.to_dict(),
            "score_changes": changes,
            "trend": (
                "改善" if changes.get("overall", 0) > 0
                else "下降" if changes.get("overall", 0) < 0
                else "持平"
            ),
        }

    def generate_visualization_data(self) -> str:
        """生成可视化数据（JSON，可用于绘制趋势图）。"""
        runs = sorted(self.history, key=lambda r: r.timestamp)
        data = {
            "labels": [r.run_id for r in runs],
            "datasets": {},
        }
        for dim in ["accuracy", "relevance", "fluency", "safety", "overall"]:
            data["datasets"][dim] = [r.avg_scores.get(dim, 0) for r in runs]

        path = self.output_dir / "trend_data.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"可视化数据已保存到 {path}"


def build_sample_testset() -> list[dict[str, str]]:
    """构建示例测试集。"""
    return [
        {
            "question": "什么是 RAG？",
            "expected": "检索增强生成",
            "system": "你是 AISearch 智能问答助手。",
        },
        {
            "question": "AISearch 支持哪些文档格式？",
            "expected": "PDF",
            "system": "你是 AISearch 智能问答助手。",
        },
        {
            "question": "如何提高检索准确率？",
            "expected": "切分",
            "system": "你是 AISearch 智能问答助手。",
        },
    ]


def demo_pipeline() -> None:
    """演示评估管道。"""
    config = PipelineConfig(
        target_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        target_model="qwen2.5:7b",
        judge_model="gpt-4o-mini",
    )
    pipeline = EvalPipeline(config)

    testset = build_sample_testset()

    # 运行评估
    run = pipeline.run(testset)
    print(f"\n运行结果: {run.to_dict()}")

    # 趋势分析
    trend = pipeline.trend_analysis()
    print(f"\n趋势分析: {trend}")

    # 可视化数据
    print(pipeline.generate_visualization_data())


if __name__ == "__main__":
    demo_pipeline()
