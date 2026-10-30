# -*- coding: utf-8 -*-
"""
Day09 - 03 澄清（Clarification）

演示内容：
1. 检测任务中的缺失关键参数
2. 一次性打包提问（避免连环追问），给选项 + 默认值
3. 澄清结果写入记忆：同样的问题不问第二遍
4. 有合理默认值的参数不问，直接声明使用

全部离线可运行。
"""

from dataclasses import dataclass, field


# ============================================================
# 第一部分：参数缺失检测
# ============================================================

@dataclass
class ParamSpec:
    """参数规格：名字、是否关键、选项、默认值"""
    name: str
    critical: bool                  # 关键参数：缺失必须问
    options: list[str] = field(default_factory=list)
    default: str | None = None      # 有默认值的非关键参数：直接用


# 预订机票任务的参数规格
TICKET_SPECS = [
    ParamSpec("出发日期", critical=True),                       # 无默认，必须问
    ParamSpec("舱位", critical=False, options=["经济舱", "商务舱"], default="经济舱"),
    ParamSpec("时间段", critical=False, options=["上午", "下午", "晚上"], default="上午"),
    ParamSpec("乘客姓名", critical=True),                       # 必须问
]


def detect_missing(user_task: str, specs: list[ParamSpec]) -> tuple:
    """
    检测缺失参数。
    返回 (critical_missing, defaults_to_apply)
    """
    critical_missing = []
    defaults = []

    for spec in specs:
        # 简单检测：任务文本中是否提及该参数名或其选项值
        mentioned = spec.name in user_task or any(
            opt in user_task for opt in spec.options
        )
        if mentioned:
            continue

        if spec.critical:
            critical_missing.append(spec.name)
        else:
            defaults.append((spec.name, spec.default))  # 非关键：用默认值

    return critical_missing, defaults


# ============================================================
# 第二部分：打包提问（一个对话框问全）
# ============================================================

def build_clarification(missing: list[str], defaults: list) -> str:
    """
    生成一条打包好的澄清消息：关键项提问 + 默认项声明。
    选择题优于填空题，一次问全。
    """
    lines = ["在开始之前，请补充以下信息："]
    for i, name in enumerate(missing, 1):
        lines.append(f"  {i}. {name}：请直接输入")

    if defaults:
        lines.append("\n以下将使用默认值（如需修改请一并说明）：")
        for name, val in defaults:
            lines.append(f"  - {name}：{val}")

    return "\n".join(lines)


# ============================================================
# 第三部分：澄清记忆（同样的问题不问第二遍）
# ============================================================

class ClarifyMemory:
    """
    记住用户的澄清结果。
    第 1 次问了"舱位"，之后所有任务直接用记忆里的答案。
    """

    def __init__(self):
        self.user_prefs: dict[str, str] = {}

    def learn(self, key: str, value: str):
        self.user_prefs[key] = value

    def get(self, key: str) -> str | None:
        return self.user_prefs.get(key)


# ============================================================
# 第四部分：带澄清的预订 Agent
# ============================================================

class BookingAgent:
    def __init__(self):
        self.memory = ClarifyMemory()
        self.history: list[str] = []

    def handle(self, user_task: str) -> str:
        """处理一次预订请求"""
        self.history.append(f"用户：{user_task}")

        # 检测：记忆能覆盖的关键参数不再追问
        critical_missing, defaults = detect_missing(user_task, TICKET_SPECS)
        covered = [k for k in critical_missing if self.memory.get(k)]
        # 用户偏好（如舱位）在记忆里则替换默认值
        defaults = [
            (name, self.memory.get(name) or val) for name, val in defaults
        ]

        if critical_missing:
            # 模拟用户只回答关键问题，非关键项保持默认
            reply = build_clarification(critical_missing, defaults)
            self.history.append(f"Agent：\n{reply}")

            # 模拟用户的澄清回答（第一次）
            simulated_answer = "9月20日，乘客张三"
            self.history.append(f"用户：{simulated_answer}")

            # 把澄清结果写入记忆
            if "9月20日" in simulated_answer:
                self.memory.learn("出发日期", "9月20日")
                self.memory.learn("乘客姓名", "张三")
            user_task = f"{user_task} {simulated_answer}"

        # 重新检测：应当无缺失
        critical_missing2, defaults2 = detect_missing(user_task, TICKET_SPECS)
        # 记忆覆盖后二次检测
        critical_missing2 = [
            k for k in critical_missing2 if not self.memory.get(k)
        ]

        if critical_missing2:
            return f"仍缺少：{critical_missing2}（演示中不应出现）"

        # 生成预订
        date = self.memory.get("出发日期") or "今天"
        name = self.memory.get("乘客姓名") or "本人"
        applied = {n: (self.memory.get(n) or v) for n, v in defaults2}
        result = (
            f"已预订：{date} {applied.get('时间段', '上午')} "
            f"{applied.get('舱位', '经济舱')} 机票，乘客 {name}"
        )
        self.history.append(f"Agent：{result}")
        return result

    def handle_again_with_memory(self, user_task: str) -> str:
        """
        第二次类似请求：乘客姓名已记忆，不再追问（只问新缺失项）。
        """
        self.history.append(f"用户：{user_task}")
        critical_missing, defaults = detect_missing(user_task, TICKET_SPECS)

        # 关键参数被记忆覆盖
        still_missing = [k for k in critical_missing if not self.memory.get(k)]
        if still_missing:
            reply = build_clarification(still_missing, defaults)
            self.history.append(f"Agent：\n{reply}")
            # 模拟回答新缺失项（出发日期变了）
            self.memory.learn("出发日期", "10月8日")
            user_task = f"{user_task} 10月8日"

        date = self.memory.get("出发日期")
        name = self.memory.get("乘客姓名")
        applied = {n: (self.memory.get(n) or v) for n, v in defaults}
        result = (
            f"已预订：{date} {applied.get('时间段', '上午')} "
            f"{applied.get('舱位', '经济舱')} 机票，乘客 {name}"
        )
        self.history.append(f"Agent：{result}")
        return result


# ============================================================
# 第五部分：演示
# ============================================================

def main():
    agent = BookingAgent()

    print("=" * 56)
    print("第 1 次请求：缺少日期和姓名 -> 触发澄清")
    print("=" * 56)
    agent.handle("帮我订一张去北京的机票")
    print("\n--- 完整对话轨迹 ---")
    for h in agent.history:
        print(h)
        print()

    print("=" * 56)
    print("第 2 次请求：姓名已在记忆中 -> 只问新的缺失项")
    print("=" * 56)
    agent.history.clear()
    agent.handle_again_with_memory("再帮我订一张去上海的机票")

    print("--- 第二次对话轨迹（注意：没有再问乘客姓名） ---")
    for h in agent.history:
        print(h)
        print()

    print("--- 记忆中的用户偏好 ---")
    for k, v in agent.memory.user_prefs.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
