"""
Day09 练习二：优先级与冲突仲裁
================================
多个工具都可能回应同一查询时, 用一个"优先级规则"仲裁,
让 Agent 优先使用更权威/更便宜的工具, 而非让模型乱选。

运行:
  python "Day09 - 多工具复杂 Agent/Code/02-priority-conflict.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402


@tool
def price_web(kw: str) -> str:
    """来自网页的价格(慢, 需 3s, 成本高)"""
    import time; time.sleep(0.01)
    return f"[web] {kw} $110"


@tool
def price_db(kw: str) -> str:
    """来自本库的价格(快, 免费)"""
    return f"[db] {kw} $99"


# 优先级规则: 能力相同时, 先用便宜的/快的
PRIORITY = {"price_db": 1, "price_web": 2}   # 数字越小越优先


def arbitration(reg: ToolRegistry, intent: str, candidates: list[str]) -> str:
    """对一个意图, 选出优先级最高的工具名执行。"""
    available = [c for c in candidates if reg.get(c)]
    if not available:
        return "无工具可调用"
    chosen = min(available, key=lambda n: PRIORITY.get(n, 99))
    return chosen


def main() -> None:
    reg = ToolRegistry([price_web, price_db])
    candidates = ["price_db", "price_web"]        # 两个都能查价

    for intent in ["查询鼠标价格", "查询键盘价格"]:
        chosen = arbitration(reg, intent, candidates)
        result = reg.execute(chosen, kw=intent[2:])
        print(f"意图[{intent}] -> 仲裁选出 {chosen} (优先级{PRIORITY[chosen]}) -> {result}")

    print("\n结论: 当多个工具能力重叠时, 用成本/速度/权威度仲裁, 避免模型滥用昂贵工具。")


if __name__ == "__main__":
    main()