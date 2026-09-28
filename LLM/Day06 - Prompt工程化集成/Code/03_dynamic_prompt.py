# 文件用途：动态 Prompt 构建
# DynamicPromptBuilder 类：根据用户类型(VIP/普通) / 对话历史 / 任务复杂度
# 动态选择模板和参数；动态拼接 Few-Shot 示例；展示同一任务在不同条件下的 Prompt 差异。
# 运行前：pip install jinja2

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from jinja2 import Environment, StrictUndefined


class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class BuildContext:
    """构建上下文：决定动态选择哪些模板与参数。"""

    user_tier: Literal["free", "vip"] = "free"
    history: list[dict] = field(default_factory=list)  # [{"role":..., "content":...}]
    complexity: Complexity = Complexity.SIMPLE
    language: str = "zh"


# ---------------------------------------------------------------------------
# 模板库（生产环境应放在文件里，此处内联以便单文件运行）
# ---------------------------------------------------------------------------
SYSTEM_BASE = """你是 AISearch 智能问答助手。
{% block rules %}默认规则：准确、简洁、礼貌。{% endblock %}
{% block vip %}{% endblock %}
当前服务语言：{{language}}。"""

SYSTEM_VIP = """{% extends "system_base" %}
{% block rules %}VIP 规则：优先响应、深度解答、必要时给出多方案权衡。{% endblock %}
{% block vip %}您是 VIP 用户，享受 7x24 专属服务。{% endblock %}"""

# 主体问答模板
QA_TEMPLATE = """{% if history %}
对话历史：
{% for h in history %}{{h.role | capitalize}}: {{h.content}}
{% endfor %}
{% endif %}
{% if few_shot %}
参考示例：
{% for ex in few_shot %}Q: {{ex.q}}
A: {{ex.a}}
{% endfor %}
{% endif %}
用户问题：{{question}}
请回答："""

# 摘要压缩模板（历史超阈值时启用）
SUMMARIZE_HISTORY = """请把以下多轮对话压缩为不超过 100 字的摘要，保留关键信息：
{% for h in history %}{{h.role | capitalize}}: {{h.content}}
{% endfor %}
摘要："""


class DynamicPromptBuilder:
    """
    动态 Prompt 构建器。

    使用方式：
        builder = DynamicPromptBuilder()
        ctx = BuildContext(user_tier="vip", complexity=Complexity.COMPLEX)
        system, user, params = builder.build("怎么退款？", ctx)
    """

    # 复杂度 → 推荐参数
    COMPLEXITY_PARAMS = {
        Complexity.SIMPLE: {"temperature": 0.7, "max_tokens": 512},
        Complexity.MEDIUM: {"temperature": 0.4, "max_tokens": 1024},
        Complexity.COMPLEX: {"temperature": 0.2, "max_tokens": 2048},
    }

    # 历史压缩阈值（轮数）
    HISTORY_COMPRESS_THRESHOLD = 5

    # Few-Shot 示例库（按问题类型）
    FEW_SHOT_BANK = {
        "refund": [
            {"q": "怎么退款？", "a": "请在订单页点击「申请退款」，1-3 个工作日到账。"},
            {"q": "退款没到账", "a": "请提供订单号，我帮您查退款进度。"},
        ],
        "default": [
            {"q": "你能做什么？", "a": "我可以回答产品咨询、订单、售后等问题。"},
        ],
    }

    def __init__(self) -> None:
        # 用FileSystemLoader才支持 extends；这里改用字符串映射
        self._env = Environment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)

    # ------------------------- 系统模板选择 -------------------------
    def _render_system(self, ctx: BuildContext) -> str:
        """根据用户类型选择系统模板。"""
        if ctx.user_tier == "vip":
            # 简化继承：手动替换 block
            tpl = (
                "你是 AISearch 智能问答助手。\n"
                "VIP 规则：优先响应、深度解答、必要时给出多方案权衡。\n"
                "您是 VIP 用户，享受 7x24 专属服务。\n"
                f"当前服务语言：{ctx.language}。"
            )
        else:
            tpl = (
                "你是 AISearch 智能问答助手。\n"
                "默认规则：准确、简洁、礼貌。\n"
                f"当前服务语言：{ctx.language}。"
            )
        return tpl

    # ------------------------- 历史处理 -------------------------
    def _compress_history(self, history: list[dict]) -> tuple[list[dict], str | None]:
        """历史超阈值时压缩。返回 (用于拼装的简短历史, 摘要 Prompt 或 None)。"""
        if len(history) <= self.HISTORY_COMPRESS_THRESHOLD:
            return history, None
        # 用摘要模板生成压缩 Prompt（实际压缩需调 LLM，此处仅生成 Prompt）
        summary_prompt = self._env.from_string(SUMMARIZE_HISTORY).render(history=history)
        # 简短历史：保留最近 2 轮
        return history[-2:], summary_prompt

    # ------------------------- Few-Shot 选择 -------------------------
    def _select_few_shot(self, question: str, complexity: Complexity) -> list[dict]:
        """复杂任务才带 Few-Shot；按问题关键词选示例。"""
        if complexity == Complexity.SIMPLE:
            return []
        q_lower = question.lower()
        if "退款" in question or "refund" in q_lower:
            return self.FEW_SHOT_BANK["refund"]
        return self.FEW_SHOT_BANK["default"]

    # ------------------------- 构建入口 -------------------------
    def build(self, question: str, ctx: BuildContext) -> tuple[str, str, dict]:
        """
        根据上下文构建完整 Prompt。

        返回：(system_prompt, user_prompt, model_params)
        """
        # 1. 系统模板
        system = self._render_system(ctx)

        # 2. 历史压缩
        history_to_use, summary_prompt = self._compress_history(ctx.history)
        if summary_prompt:
            system += "\n（已自动压缩对话历史，参考摘要）"

        # 3. Few-Shot
        few_shot = self._select_few_shot(question, ctx.complexity)

        # 4. 渲染用户 Prompt
        user = self._env.from_string(QA_TEMPLATE).render(
            history=history_to_use,
            few_shot=few_shot,
            question=question,
        )

        # 5. 模型参数
        params = dict(self.COMPLEXITY_PARAMS[ctx.complexity])
        return system, user, params


# ---------------------------------------------------------------------------
# 演示：同一问题在不同条件下的 Prompt 差异
# ---------------------------------------------------------------------------
def show(label: str, system: str, user: str, params: dict) -> None:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    print(f"[参数] {params}")
    print(f"\n--- System ---\n{system}")
    print(f"\n--- User ---\n{user}")


def demo() -> None:
    builder = DynamicPromptBuilder()

    question = "我昨天买的会员怎么退款？"

    # 场景 1：普通用户、简单任务、无历史
    ctx1 = BuildContext(user_tier="free", complexity=Complexity.SIMPLE)
    s, u, p = builder.build(question, ctx1)
    show("场景 1：免费用户 / 简单 / 无历史", s, u, p)

    # 场景 2：VIP 用户、复杂任务、无历史
    ctx2 = BuildContext(user_tier="vip", complexity=Complexity.COMPLEX)
    s, u, p = builder.build(question, ctx2)
    show("场景 2：VIP / 复杂 / 无历史（带 Few-Shot）", s, u, p)

    # 场景 3：普通用户、中等任务、带历史（触发压缩）
    long_history = [
        {"role": "user", "content": f"第{i}轮问题"},
        {"role": "assistant", "content": f"第{i}轮回答"},
        for i in range(1, 7)
    ]
    ctx3 = BuildContext(user_tier="free", complexity=Complexity.MEDIUM, history=long_history)
    s, u, p = builder.build(question, ctx3)
    show("场景 3：免费 / 中等 / 6 轮历史（触发压缩）", s, u, p)


if __name__ == "__main__":
    demo()
