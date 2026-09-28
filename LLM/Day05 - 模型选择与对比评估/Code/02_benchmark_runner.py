# 文件用途：基准测试运行器
# 定义多任务测试用例集（分类/推理/代码/创作各若干题），批量调用模型，
# 自动判分并生成 Markdown 报告。支持自定义测试集与多种判分策略。
# 运行前：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# 测试用例与判分
# ---------------------------------------------------------------------------
class TaskType(str, Enum):
    CLASSIFY = "分类"
    REASONING = "推理"
    CODE = "代码"
    CREATION = "创作"


@dataclass
class TestCase:
    """单个测试用例。"""

    case_id: str
    task_type: TaskType
    prompt: str
    expected: str  # 期望关键词 / 期望答案 / 评分要点
    judge: str = "contains"  # contains / regex / exact / llm
    max_score: int = 1


@dataclass
class CaseResult:
    """单个用例的运行结果。"""

    case: TestCase
    output: str
    latency_sec: float
    score: float
    passed: bool
    note: str = ""


@dataclass
class BenchmarkReport:
    """整体报告。"""

    model: str
    results: list[CaseResult] = field(default_factory=list)

    def add(self, r: CaseResult) -> None:
        self.results.append(r)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def avg_latency(self) -> float:
        return sum(r.latency_sec for r in self.results) / max(self.total, 1)

    def by_type(self) -> dict[TaskType, tuple[int, int]]:
        """按任务类型统计 (通过数, 总数)。"""
        stat: dict[TaskType, tuple[int, int]] = {}
        for r in self.results:
            t = r.case.task_type
            passed, total = stat.get(t, (0, 0))
            stat[t] = (passed + (1 if r.passed else 0), total + 1)
        return stat

    def to_markdown(self) -> str:
        lines = [
            f"# 基准测试报告 - {self.model}",
            "",
            f"- 总用例数：{self.total}",
            f"- 通过数：{self.passed_count}",
            f"- 通过率：{self.passed_count / max(self.total, 1) * 100:.1f}%",
            f"- 平均延迟：{self.avg_latency:.2f}s",
            "",
            "## 分任务类型统计",
            "",
            "| 类型 | 通过 | 总数 | 通过率 |",
            "|------|------|------|--------|",
        ]
        for t, (p, total) in self.by_type().items():
            lines.append(f"| {t.value} | {p} | {total} | {p / max(total, 1) * 100:.1f}% |")

        lines.extend(["", "## 详细结果", "", "| 用例ID | 类型 | 延迟(s) | 得分 | 通过 | 备注 |", "|--------|------|---------|------|------|------|"])
        for r in self.results:
            lines.append(
                f"| {r.case.case_id} | {r.case.task_type.value} | {r.latency_sec:.2f} | "
                f"{r.score}/{r.case.max_score} | {'✓' if r.passed else '✗'} | {r.note} |"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 内置测试集（分类/推理/代码/创作 各 5 题）
# ---------------------------------------------------------------------------
def default_test_suite() -> list[TestCase]:
    return [
        # 分类 5 题
        TestCase("CLS-01", TaskType.CLASSIFY, "判断情感：'今天阳光真好，心情愉快'。只输出 正面 或 负面。", "正面"),
        TestCase("CLS-02", TaskType.CLASSIFY, "判断情感：'快递又丢了，客服态度还差'。只输出 正面 或 负面。", "负面"),
        TestCase("CLS-03", TaskType.CLASSIFY, "判断情感：'这部电影一般般，没什么亮点'。只输出 正面 或 负面。", "负面"),
        TestCase("CLS-04", TaskType.CLASSIFY, "判断情感：'终于下班啦！周末走起'。只输出 正面 或 负面。", "正面"),
        TestCase("CLS-05", TaskType.CLASSIFY, "判断情感：'作业写不完，deadline 明天'。只输出 正面 或 负面。", "负面"),
        # 推理 5 题
        TestCase("RSN-01", TaskType.REASONING, "小明有 5 个苹果，吃了 2 个又买了 3 个，现在有几个？只输出数字。", "6"),
        TestCase("RSN-02", TaskType.REASONING, "如果 A>B 且 B>C，那么 A 和 C 谁大？只输出 A 或 C。", "A"),
        TestCase("RSN-03", TaskType.REASONING, "一列火车 2 小时行驶 240 公里，平均时速多少？只输出数字。", "120"),
        TestCase("RSN-04", TaskType.REASONING, "三个连续整数和为 18，最大的是几？只输出数字。", "7"),
        TestCase("RSN-05", TaskType.REASONING, "今天是周三，5 天后是星期几？只输出 星期X。", "星期一"),
        # 代码 5 题
        TestCase("COD-01", TaskType.CODE, "用 Python 写一个返回两数之和的函数 add(a,b)。只输出代码。", "def add", "contains"),
        TestCase("COD-02", TaskType.CODE, "用 Python 写一个反转字符串的函数 reverse(s)。只输出代码。", "def reverse"),
        TestCase("COD-03", TaskType.CODE, "用 Python 写一个判断偶数的函数 is_even(n)。只输出代码。", "def is_even"),
        TestCase("COD-04", TaskType.CODE, "用 Python 写一个返回列表最大值的函数 my_max(lst)。只输出代码。", "def my_max"),
        TestCase("COD-05", TaskType.CODE, "用 Python 写一个判断回文字符串的函数 is_palindrome(s)。只输出代码。", "def is_palindrome"),
        # 创作 5 题
        TestCase("CRT-01", TaskType.CREATION, "用一句话为运动手环写广告语，包含 '健康' 关键词。", "健康"),
        TestCase("CRT-02", TaskType.CREATION, "用一句话为咖啡写广告语，包含 '活力' 关键词。", "活力"),
        TestCase("CRT-03", TaskType.CREATION, "用一句话为在线教育产品写广告语，包含 '成长' 关键词。", "成长"),
        TestCase("CRT-04", TaskType.CREATION, "用一句话为旅行 App 写广告语，包含 '世界' 关键词。", "世界"),
        TestCase("CRT-05", TaskType.CREATION, "用一句话为护肤品写广告语，包含 '自然' 关键词。", "自然"),
    ]


# ---------------------------------------------------------------------------
# 判分器
# ---------------------------------------------------------------------------
def judge_case(case: TestCase, output: str) -> tuple[float, str]:
    """根据 judge 策略返回 (得分, 备注)。"""
    out = output.strip()
    if case.judge == "exact":
        return (case.max_score, "完全匹配") if out == case.expected else (0.0, f"期望 {case.expected!r}")
    if case.judge == "contains":
        if case.expected in out:
            return (case.max_score, "包含期望关键词")
        # 大小写不敏感再判一次
        if case.expected.lower() in out.lower():
            return (case.max_score, "包含（忽略大小写）")
        return (0.0, f"未包含 {case.expected!r}")
    if case.judge == "regex":
        return (case.max_score, "正则匹配") if re.search(case.expected, out) else (0.0, "正则不匹配")
    # 默认 contains
    return (case.max_score, "") if case.expected in out else (0.0, "")


# ---------------------------------------------------------------------------
# 运行器
# ---------------------------------------------------------------------------
class BenchmarkRunner:
    """
    基准测试运行器。

    使用方式：
        runner = BenchmarkRunner(model="gpt-4o-mini")
        report = runner.run(default_test_suite())
        print(report.to_markdown())
    """

    def __init__(self, model: str = "gpt-4o-mini", base_url: str | None = None) -> None:
        self.model = model
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY，请在 .env 中设置")
            kwargs = {"api_key": api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _call(self, prompt: str) -> tuple[str, float]:
        start = time.perf_counter()
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=512,
        )
        output = resp.choices[0].message.content or ""
        return output, time.perf_counter() - start

    def run(
        self,
        cases: list[TestCase],
        judge_fn: Callable[[TestCase, str], tuple[float, str]] = judge_case,
        verbose: bool = True,
    ) -> BenchmarkReport:
        report = BenchmarkReport(model=self.model)
        for idx, case in enumerate(cases, 1):
            if verbose:
                print(f"  [{idx}/{len(cases)}] {case.case_id} ({case.task_type.value}) ...", end=" ", flush=True)
            try:
                output, latency = self._call(case.prompt)
            except Exception as exc:  # noqa: BLE001
                output, latency = "", 0.0
                note = f"调用失败: {type(exc).__name__}"
                report.add(CaseResult(case, output, latency, 0.0, False, note))
                if verbose:
                    print(f"FAIL ({note})")
                continue

            score, note = judge_fn(case, output)
            passed = score >= case.max_score
            report.add(CaseResult(case, output, latency, score, passed, note))
            if verbose:
                print(f"{'PASS' if passed else 'FAIL'} ({latency:.2f}s) {note}")
        return report


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY，请在 .env 中设置")
        return

    cases = default_test_suite()
    print(f"测试集大小：{len(cases)} 题\n")

    # 默认用 mini 跑（便宜快），可改为 gpt-4o 对比
    model = os.getenv("BENCHMARK_MODEL", "gpt-4o-mini")
    print(f"开始测试模型：{model}\n")

    runner = BenchmarkRunner(model=model)
    report = runner.run(cases)

    print("\n" + "=" * 60)
    print(report.to_markdown())


if __name__ == "__main__":
    demo()
