# 文件用途：Prompt 测试框架
# PromptTestRunner 类：定义测试用例（输入/期望断言）→ 运行测试 → 生成报告。
# 断言类型：contains / not_contains / regex / json_schema / exact。
# 支持 mock LLM（无需真实 API）与真实 LLM 调用两种模式；含 pytest 集成示例。
# 运行前：pip install jinja2 jsonschema（真实调用还需 openai + .env）

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from dotenv import load_dotenv
from jinja2 import Environment, StrictUndefined

load_dotenv()


# ---------------------------------------------------------------------------
# 断言
# ---------------------------------------------------------------------------
@dataclass
class Assertion:
    """单条断言。"""

    kind: str  # contains / not_contains / regex / json_schema / exact
    expected: Any  # 关键词 / 正则 / schema / 期望字符串
    description: str = ""

    def check(self, output: str) -> tuple[bool, str]:
        out = output.strip()
        if self.kind == "contains":
            ok = isinstance(self.expected, str) and self.expected in out
            return ok, "包含关键词" if ok else f"未包含 {self.expected!r}"
        if self.kind == "not_contains":
            ok = isinstance(self.expected, str) and self.expected not in out
            return ok, "未包含禁用词" if ok else f"包含了禁用词 {self.expected!r}"
        if self.kind == "regex":
            ok = bool(re.search(self.expected, out))
            return ok, "正则匹配" if ok else "正则不匹配"
        if self.kind == "exact":
            ok = out == self.expected
            return ok, "完全匹配" if ok else f"期望 {self.expected!r}，实际 {out!r}"
        if self.kind == "json_schema":
            try:
                import json
                from jsonschema import validate

                data = json.loads(out)
                validate(instance=data, schema=self.expected)
                return True, "JSON Schema 校验通过"
            except Exception as exc:  # noqa: BLE001
                return False, f"JSON Schema 校验失败: {exc}"
        return False, f"未知断言类型 {self.kind}"


@dataclass
class TestCase:
    """测试用例。"""

    case_id: str
    template_name: str
    variables: dict        # 模板变量
    assertions: list[Assertion]
    description: str = ""
    # 可选：覆盖默认 mock 返回
    mock_output: str | None = None


@dataclass
class TestResult:
    case: TestCase
    output: str
    passed: bool
    details: list[tuple[bool, str]] = field(default_factory=list)
    error: str | None = None


@dataclass
class TestReport:
    results: list[TestResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    def to_markdown(self) -> str:
        lines = [
            "# Prompt 测试报告",
            "",
            f"- 总用例：{self.total}",
            f"- 通过：{self.passed}",
            f"- 失败：{self.total - self.passed}",
            f"- 通过率：{self.passed / max(self.total, 1) * 100:.1f}%",
            "",
            "| 用例ID | 模板 | 结果 | 详情 |",
            "|--------|------|------|------|",
        ]
        for r in self.results:
            ok = "✓" if r.passed else "✗"
            detail = "; ".join(f"{'✓' if p else '✗'}{d}" for p, d in r.details)
            if r.error:
                detail = f"ERROR: {r.error}"
            lines.append(f"| {r.case.case_id} | {r.case.template_name} | {ok} | {detail} |")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 运行器
# ---------------------------------------------------------------------------
class PromptTestRunner:
    """
    Prompt 测试框架。

    使用方式：
        runner = PromptTestRunner()
        runner.register_template("qa", "你是客服，回答：{{question}}")
        runner.add_case(TestCase(
            case_id="QA-01",
            template_name="qa",
            variables={"question": "怎么退款？"},
            assertions=[Assertion("contains", "退款")],
            mock_output="请在订单页申请退款。",
        ))
        report = runner.run(mock=True)
        print(report.to_markdown())
    """

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}
        self._cases: list[TestCase] = []
        self._env = Environment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)

    # ------------------------- 注册 -------------------------
    def register_template(self, name: str, template_str: str) -> None:
        self._templates[name] = template_str

    def add_case(self, case: TestCase) -> None:
        self._cases.append(case)

    # ------------------------- 渲染 -------------------------
    def _render(self, template_name: str, variables: dict) -> str:
        if template_name not in self._templates:
            raise KeyError(f"模板 {template_name!r} 未注册")
        return self._env.from_string(self._templates[template_name]).render(**variables)

    # ------------------------- LLM 调用 -------------------------
    def _call_llm(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return resp.choices[0].message.content or ""

    # ------------------------- 运行 -------------------------
    def run(self, mock: bool = True, model: str = "gpt-4o-mini") -> TestReport:
        report = TestReport()
        for case in self._cases:
            # 1. 渲染模板
            try:
                prompt = self._render(case.template_name, case.variables)
            except Exception as exc:  # noqa: BLE001
                report.results.append(
                    TestResult(case=case, output="", passed=False, error=f"渲染失败: {exc}")
                )
                continue
            # 2. 获取输出（mock 或真实）
            if mock:
                output = case.mock_output if case.mock_output is not None else f"[mock] {prompt}"
            else:
                try:
                    output = self._call_llm(prompt, model)
                except Exception as exc:  # noqa: BLE001
                    report.results.append(
                        TestResult(case=case, output="", passed=False, error=f"LLM 调用失败: {exc}")
                    )
                    continue
            # 3. 断言
            details: list[tuple[bool, str]] = []
            all_pass = True
            for a in case.assertions:
                ok, msg = a.check(output)
                details.append((ok, msg))
                if not ok:
                    all_pass = False
            report.results.append(
                TestResult(case=case, output=output, passed=all_pass, details=details)
            )
        return report


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    runner = PromptTestRunner()

    # 注册模板
    runner.register_template(
        "qa",
        "你是 AISearch 客服，回答用户问题：{{question}}。要求回答中包含「退款」一词。",
    )
    runner.register_template(
        "classify",
        '请对以下文本进行情感分类，只输出 JSON：{"label":"正面"或"负面"}。文本：{{text}}',
    )

    # 测试用例 1：contains
    runner.add_case(TestCase(
        case_id="QA-01",
        template_name="qa",
        variables={"question": "怎么退款？"},
        assertions=[Assertion("contains", "退款", "应包含退款")],
        mock_output="请点击订单页的退款按钮。",
    ))
    # 测试用例 2：not_contains
    runner.add_case(TestCase(
        case_id="QA-02",
        template_name="qa",
        variables={"question": "退款"},
        assertions=[Assertion("not_contains", "不知道", "不应说不知道")],
        mock_output="请提供订单号，我帮您处理退款。",
    ))
    # 测试用例 3：json_schema
    runner.add_case(TestCase(
        case_id="CLS-01",
        template_name="classify",
        variables={"text": "今天很开心"},
        assertions=[
            Assertion(
                "json_schema",
                {"type": "object", "properties": {"label": {"enum": ["正面", "负面"]}}, "required": ["label"]},
                "应为合法 JSON 且 label 为正/负面",
            )
        ],
        mock_output='{"label": "正面"}',
    ))
    # 测试用例 4：regex
    runner.add_case(TestCase(
        case_id="CLS-02",
        template_name="classify",
        variables={"text": "快递丢了"},
        assertions=[Assertion("regex", r'"label"\s*:\s*"负面"', "应匹配负面")],
        mock_output='{"label": "负面"}',
    ))
    # 测试用例 5：失败用例（演示）
    runner.add_case(TestCase(
        case_id="QA-FAIL",
        template_name="qa",
        variables={"question": "退款"},
        assertions=[Assertion("contains", "立即", "应包含立即（演示失败）")],
        mock_output="请稍候。",
    ))

    print("=" * 60)
    print("运行测试（mock 模式）")
    print("=" * 60)
    report = runner.run(mock=True)
    print(report.to_markdown())

    # pytest 集成示例（输出代码，不实际执行）
    print("\n" + "=" * 60)
    print("pytest 集成示例（仅打印代码）")
    print("=" * 60)
    print(
        "# test_prompt.py\n"
        "import pytest\n"
        "from your_module import PromptTestRunner, TestCase, Assertion\n\n"
        "@pytest.fixture\n"
        "def runner():\n"
        "    r = PromptTestRunner()\n"
        "    r.register_template('qa', '回答：{{question}}')\n"
        "    return r\n\n"
        "def test_qa_contains_refund(runner):\n"
        "    runner.add_case(TestCase(\n"
        "        case_id='QA-01', template_name='qa',\n"
        "        variables={'question': '退款'},\n"
        "        assertions=[Assertion('contains', '退款')],\n"
        "        mock_output='请在订单页申请退款。',\n"
        "    ))\n"
        "    report = runner.run(mock=True)\n"
        "    assert report.passed == report.total\n"
    )


if __name__ == "__main__":
    demo()
