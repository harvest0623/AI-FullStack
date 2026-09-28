# 文件用途：模型路由器实现
# ModelRouter 类：根据任务类型 / 输入长度 / 用户分级 / 复杂度自动选择模型。
# 提供两种路由：
#   1. 规则路由（if-else）—— 静态、可解释、零额外成本
#   2. 动态路由—— 先用小模型判断复杂度，再决定是否升级到大模型
# 运行前：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# 任务类型与路由配置
# ---------------------------------------------------------------------------
class TaskType(str, Enum):
    CHAT = "chat"            # 闲聊 / 简单问答
    CLASSIFY = "classify"    # 分类 / 意图识别
    EXTRACTION = "extraction"  # 信息抽取
    REASONING = "reasoning"  # 数学 / 逻辑推理
    CODE = "code"            # 代码生成 / 调试
    LONG_DOC = "long_doc"    # 长文本处理


class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# 模型档位
SMALL_MODEL = "gpt-4o-mini"      # 便宜快
STANDARD_MODEL = "gpt-4o"        # 通用强
REASONING_MODEL = "o1-mini"      # 深度推理
LONG_CONTEXT_MODEL = "gpt-4o"    # 此处沿用 4o；超长可换 gemini-1.5-pro


@dataclass
class RouteDecision:
    """路由决策结果。"""

    model: str
    task_type: TaskType
    complexity: Complexity
    reason: str
    extra_call: bool = False  # 动态路由是否触发了额外的小模型调用


@dataclass
class RouterConfig:
    """路由配置，可按业务调整。"""

    # 任务类型 → 模型（规则路由表）
    task_model_map: dict[TaskType, str] = field(
        default_factory=lambda: {
            TaskType.CHAT: SMALL_MODEL,
            TaskType.CLASSIFY: SMALL_MODEL,
            TaskType.EXTRACTION: STANDARD_MODEL,
            TaskType.REASONING: REASONING_MODEL,
            TaskType.CODE: STANDARD_MODEL,
            TaskType.LONG_DOC: LONG_CONTEXT_MODEL,
        }
    )
    # 输入长度阈值（单位：字符）
    long_doc_threshold: int = 32_000
    # VIP 用户强制走大模型
    vip_force_standard: bool = True
    # 动态路由：复杂度判断模型
    classifier_model: str = SMALL_MODEL
    # 复杂度 → 升级模型
    complexity_model_map: dict[Complexity, str] = field(
        default_factory=lambda: {
            Complexity.SIMPLE: SMALL_MODEL,
            Complexity.MEDIUM: STANDARD_MODEL,
            Complexity.COMPLEX: REASONING_MODEL,
        }
    )


# ---------------------------------------------------------------------------
# 路由器
# ---------------------------------------------------------------------------
class ModelRouter:
    """
    模型路由器。

    使用方式：
        router = ModelRouter()
        decision = router.route_static("帮我翻译这段话", TaskType.CHAT)
        print(decision.model)  # gpt-4o-mini

        decision = router.route_dynamic("证明根号2是无理数")
        print(decision.model)  # 根据复杂度可能升级到 o1-mini
    """

    def __init__(self, config: RouterConfig | None = None) -> None:
        self.config = config or RouterConfig()
        self._client = None

    # ------------------------- 工具方法 -------------------------
    @staticmethod
    def _estimate_length(text: str) -> int:
        """粗略估算输入长度（字符数）。生产环境建议用 tiktoken 精确计算。"""
        return len(text)

    @staticmethod
    def _detect_task_type(prompt: str) -> TaskType:
        """简单的关键词规则：从 prompt 推断任务类型。"""
        text = prompt.lower()
        # 代码相关
        code_kw = ["代码", "python", "java", "function", "def ", "bug", "调试", "code"]
        if any(k in text for k in code_kw):
            return TaskType.CODE
        # 推理相关
        reason_kw = ["证明", "计算", "推理", "为什么", "推导", "数学", "解方程"]
        if any(k in text for k in reason_kw):
            return TaskType.REASONING
        # 抽取相关
        extract_kw = ["提取", "抽取", "识别", "parse", "json", "字段"]
        if any(k in text for k in extract_kw):
            return TaskType.EXTRACTION
        # 分类相关
        classify_kw = ["分类", "判断", "情感", "意图", "属于"]
        if any(k in text for k in classify_kw):
            return TaskType.CLASSIFY
        return TaskType.CHAT

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("未配置 OPENAI_API_KEY，请在 .env 中设置")
            self._client = OpenAI(api_key=api_key)
        return self._client

    # ------------------------- 规则路由 -------------------------
    def route_static(
        self,
        prompt: str,
        task_type: TaskType | None = None,
        user_tier: Literal["free", "vip"] = "free",
    ) -> RouteDecision:
        """
        规则路由：基于任务类型 + 输入长度 + 用户分级的静态决策。
        零额外 LLM 调用，可解释性最强。
        """
        # 自动推断任务类型
        detected = task_type or self._detect_task_type(prompt)
        # 长文本优先
        length = self._estimate_length(prompt)
        if length >= self.config.long_doc_threshold:
            return RouteDecision(
                model=self.config.task_model_map[TaskType.LONG_DOC],
                task_type=TaskType.LONG_DOC,
                complexity=Complexity.MEDIUM,
                reason=f"输入长度 {length} 超过阈值 {self.config.long_doc_threshold}，路由到长文本模型",
            )
        # VIP 强制升级
        if user_tier == "vip" and self.config.vip_force_standard:
            return RouteDecision(
                model=STANDARD_MODEL,
                task_type=detected,
                complexity=Complexity.MEDIUM,
                reason="VIP 用户强制走标准模型",
            )
        # 按任务类型映射
        model = self.config.task_model_map[detected]
        return RouteDecision(
            model=model,
            task_type=detected,
            complexity=Complexity.SIMPLE if detected in {TaskType.CHAT, TaskType.CLASSIFY} else Complexity.MEDIUM,
            reason=f"任务类型 {detected.value} → 默认模型 {model}",
        )

    # ------------------------- 动态路由 -------------------------
    def _classify_complexity(self, prompt: str) -> tuple[Complexity, str]:
        """用小模型判断 prompt 复杂度，返回 (复杂度, 裁判理由)。"""
        client = self._get_client()
        classifier_prompt = (
            "请判断下面用户问题的复杂度，只输出一个词：simple / medium / complex。\n"
            "判定标准：\n"
            "- simple：闲聊、简单问答、单步分类、信息查询\n"
            "- medium：多步推理、中等长度写作、单文件代码\n"
            "- complex：数学证明、多步逻辑链、跨文件代码、长文分析\n\n"
            f"用户问题：{prompt}\n"
            "复杂度："
        )
        resp = client.chat.completions.create(
            model=self.config.classifier_model,
            messages=[{"role": "user", "content": classifier_prompt}],
            temperature=0.0,
            max_tokens=20,
        )
        text = (resp.choices[0].message.content or "").strip().lower()
        # 容错解析
        for c in Complexity:
            if c.value in text:
                return c, text
        return Complexity.MEDIUM, f"未识别，默认 medium（原文：{text}）"

    def route_dynamic(
        self,
        prompt: str,
        task_type: TaskType | None = None,
        user_tier: Literal["free", "vip"] = "free",
    ) -> RouteDecision:
        """
        动态路由：先用小模型判断复杂度，再决定模型档位。
        相比 route_static 多一次小模型调用（约 0.3s + 极低成本），但能更精准地降本。
        """
        detected = task_type or self._detect_task_type(prompt)

        # 长文本直接走长文本模型，不再判断复杂度
        length = self._estimate_length(prompt)
        if length >= self.config.long_doc_threshold:
            return RouteDecision(
                model=self.config.task_model_map[TaskType.LONG_DOC],
                task_type=TaskType.LONG_DOC,
                complexity=Complexity.MEDIUM,
                reason=f"输入长度 {length} 超过阈值，跳过复杂度判断",
            )

        # VIP 直走标准模型
        if user_tier == "vip" and self.config.vip_force_standard:
            return RouteDecision(
                model=STANDARD_MODEL,
                task_type=detected,
                complexity=Complexity.MEDIUM,
                reason="VIP 用户强制走标准模型",
            )

        # 调小模型判复杂度
        try:
            complexity, note = self._classify_complexity(prompt)
        except Exception as exc:  # noqa: BLE001
            # 判断失败则回退到规则路由
            return self.route_static(prompt, task_type, user_tier)

        model = self.config.complexity_model_map[complexity]
        return RouteDecision(
            model=model,
            task_type=detected,
            complexity=complexity,
            reason=f"复杂度判断={complexity.value}（{note}）→ 模型 {model}",
            extra_call=True,
        )


# ---------------------------------------------------------------------------
# 演示入口
# ---------------------------------------------------------------------------
def demo() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[错误] 未配置 OPENAI_API_KEY，请在 .env 中设置")
        return

    router = ModelRouter()

    samples = [
        ("今天天气真好", TaskType.CHAT),
        ("帮我翻译这段话：Hello World", TaskType.CHAT),
        ("证明根号 2 是无理数", TaskType.REASONING),
        ("用 Python 实现快速排序", TaskType.CODE),
        ("从这段文字里提取所有人名和地名", TaskType.EXTRACTION),
    ]

    print("=" * 70)
    print("规则路由（route_static）演示")
    print("=" * 70)
    for prompt, task in samples:
        d = router.route_static(prompt, task)
        print(f"\n输入：{prompt}")
        print(f"  → 模型：{d.model} | 任务：{d.task_type.value} | 理由：{d.reason}")

    print("\n" + "=" * 70)
    print("动态路由（route_dynamic）演示")
    print("=" * 70)
    for prompt, task in samples:
        d = router.route_dynamic(prompt, task)
        extra = "（含额外小模型调用）" if d.extra_call else ""
        print(f"\n输入：{prompt}")
        print(f"  → 模型：{d.model} | 复杂度：{d.complexity.value} | 理由：{d.reason}{extra}")


if __name__ == "__main__":
    demo()
