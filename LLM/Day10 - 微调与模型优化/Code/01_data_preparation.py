# 文件用途：微调数据准备与格式化
# DataPreparator 类：加载原始数据 / 清洗去重 / 格式转换（指令格式+对话格式）
# 数据质量检查 / 统计分析。支持 JSON/JSONL/CSV 输入，生成训练集和验证集
# 含数据质量报告生成
# Python 3.10+ 可运行（纯标准库）

from __future__ import annotations

import csv
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DataQualityReport:
    """数据质量报告。"""

    total: int = 0
    after_dedup: int = 0
    after_clean: int = 0
    train_size: int = 0
    val_size: int = 0
    avg_input_length: float = 0.0
    avg_output_length: float = 0.0
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "after_dedup": self.after_dedup,
            "after_clean": self.after_clean,
            "train_size": self.train_size,
            "val_size": self.val_size,
            "avg_input_length": round(self.avg_input_length, 1),
            "avg_output_length": round(self.avg_output_length, 1),
            "issues": self.issues,
        }


class DataPreparator:
    """微调数据准备工具，支持加载、清洗、格式转换与质量检查。"""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.records: list[dict[str, str]] = []
        self.report = DataQualityReport()

    # ---------- 加载 ----------
    def load_json(self, path: str | Path) -> list[dict[str, str]]:
        """加载 JSON 文件（列表结构）。"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.records = data if isinstance(data, list) else [data]
        self.report.total = len(self.records)
        return self.records

    def load_jsonl(self, path: str | Path) -> list[dict[str, str]]:
        """加载 JSONL 文件。"""
        records: list[dict[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        self.records = records
        self.report.total = len(records)
        return records

    def load_csv(self, path: str | Path) -> list[dict[str, str]]:
        """加载 CSV 文件，要求含 instruction/input/output 列。"""
        records: list[dict[str, str]] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(
                    {
                        "instruction": row.get("instruction", ""),
                        "input": row.get("input", ""),
                        "output": row.get("output", ""),
                    }
                )
        self.records = records
        self.report.total = len(records)
        return records

    # ---------- 清洗 ----------
    def deduplicate(self) -> list[dict[str, str]]:
        """去重：基于 instruction+output 完全匹配。"""
        seen: set[str] = set()
        unique: list[dict[str, str]] = []
        for r in self.records:
            key = (r.get("instruction", "") + r.get("output", "")).strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(r)
        removed = len(self.records) - len(unique)
        if removed > 0:
            self.report.issues.append(f"去重移除 {removed} 条重复数据")
        self.records = unique
        self.report.after_dedup = len(unique)
        return unique

    def clean(self, min_input_len: int = 2, min_output_len: int = 2) -> list[dict[str, str]]:
        """清洗：过滤空值、过短、含乱码的数据。"""
        cleaned: list[dict[str, str]] = []
        for r in self.records:
            instruction = r.get("instruction", "").strip()
            output = r.get("output", "").strip()
            if len(instruction) < min_input_len or len(output) < min_output_len:
                continue
            # 过滤控制字符
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", instruction + output):
                continue
            cleaned.append(
                {
                    "instruction": instruction,
                    "input": r.get("input", "").strip(),
                    "output": output,
                }
            )
        removed = len(self.records) - len(cleaned)
        if removed > 0:
            self.report.issues.append(f"清洗移除 {removed} 条无效数据")
        self.records = cleaned
        self.report.after_clean = len(cleaned)
        return cleaned

    # ---------- 格式转换 ----------
    def to_instruction_format(self) -> list[dict[str, Any]]:
        """转换为指令格式（Alpaca 风格）。"""
        return [
            {
                "instruction": r["instruction"],
                "input": r.get("input", ""),
                "output": r["output"],
            }
            for r in self.records
        ]

    def to_conversation_format(
        self, system: str = "你是一个专业的智能问答助手。"
    ) -> list[dict[str, Any]]:
        """转换为对话格式（ShareGPT 风格）。"""
        result: list[dict[str, Any]] = []
        for r in self.records:
            user_content = r["instruction"]
            if r.get("input"):
                user_content += "\n" + r["input"]
            result.append(
                {
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": r["output"]},
                    ]
                }
            )
        return result

    # ---------- 划分 ----------
    def split(
        self, val_ratio: float = 0.2
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """划分训练集与验证集。"""
        random.seed(self.seed)
        shuffled = self.records.copy()
        random.shuffle(shuffled)
        val_size = max(1, int(len(shuffled) * val_ratio))
        val_set = shuffled[:val_size]
        train_set = shuffled[val_size:]
        self.report.train_size = len(train_set)
        self.report.val_size = val_size
        return train_set, val_set

    # ---------- 质量统计 ----------
    def analyze(self) -> DataQualityReport:
        """统计分析并生成质量报告。"""
        if self.records:
            input_lens = [len(r.get("instruction", "")) for r in self.records]
            output_lens = [len(r.get("output", "")) for r in self.records]
            self.report.avg_input_length = sum(input_lens) / len(input_lens)
            self.report.avg_output_length = sum(output_lens) / len(output_lens)

        if self.report.total > 0:
            if self.report.after_dedup / self.report.total < 0.9:
                self.report.issues.append("重复率较高（>10%），建议检查数据来源")
            if self.report.avg_output_length < 20:
                self.report.issues.append("输出平均长度过短，可能影响学习效果")
            if self.report.total < 500:
                self.report.issues.append("数据量偏少（<500），建议扩充至 1000+ 条")

        return self.report

    # ---------- 保存 ----------
    def save_jsonl(self, data: list[dict[str, Any]], path: str | Path) -> None:
        """保存为 JSONL 文件。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[DataPreparator] 已保存 {len(data)} 条到 {path}")

    def save_report(self, path: str | Path) -> None:
        """保存质量报告。"""
        report = self.analyze().to_dict()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[DataPreparator] 质量报告已保存到 {path}")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def create_sample_data(path: str | Path, n: int = 50) -> None:
    """生成示例数据用于演示。"""
    samples = [
        {
            "instruction": "AISearch 支持哪些文档格式？",
            "input": "",
            "output": "AISearch 支持 PDF、Word、Markdown、TXT、HTML 等主流文档格式，并支持自动解析与向量化。",
        },
        {
            "instruction": "如何提高 RAG 检索准确率？",
            "input": "",
            "output": "可通过以下方式提高：1) 优化文档切分策略；2) 使用更优的 embedding 模型；3) 引入重排序；4) 增加查询改写。",
        },
    ]
    data = [samples[i % len(samples)] for i in range(n)]
    # 故意加几条重复与空值用于演示清洗
    data.append({"instruction": "", "input": "", "output": "空数据"})
    data.append(samples[0])  # 重复

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"已生成 {len(data)} 条示例数据到 {path}")


def demo_data_preparation() -> None:
    """演示数据准备流程。"""
    sample_path = "sample_finetune_data.jsonl"
    output_dir = "finetune_data"

    # 1. 生成示例数据
    create_sample_data(sample_path, n=50)

    # 2. 准备数据
    prep = DataPreparator()
    prep.load_jsonl(sample_path)
    prep.deduplicate()
    prep.clean(min_input_len=2, min_output_len=5)

    # 3. 格式转换
    instruction_data = prep.to_instruction_format()
    conversation_data = prep.to_conversation_format()

    # 4. 划分数据集
    train_set, val_set = prep.split(val_ratio=0.2)

    # 5. 保存
    prep.save_jsonl(instruction_data, f"{output_dir}/train_instructions.jsonl")
    prep.save_jsonl(conversation_data, f"{output_dir}/train_conversations.jsonl")
    prep.save_jsonl(train_set, f"{output_dir}/train.jsonl")
    prep.save_jsonl(val_set, f"{output_dir}/val.jsonl")

    # 6. 质量报告
    prep.save_report(f"{output_dir}/quality_report.json")


if __name__ == "__main__":
    demo_data_preparation()
