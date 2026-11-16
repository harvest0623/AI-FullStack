# -*- coding: utf-8 -*-
"""
Day05 - 03 有依赖的顺序处理

演示一个工具的结果作为另一个工具参数的情况，必须分阶段执行，不能并行。

离线可运行。
"""

import json


def get_temp(city):
    return {"北京": 22, "上海": 30, "广州": 28}[city]


def warmer(a, b):
    return "北京" if a > b else "上海"


def parse_temp(text):
    # 从结果里抽数值（演示直接建模）
    return text


def main():
    print(">> 有依赖的顺序处理\n")
    print("  用户：『分别查北京、上海温度，然后告诉我哪更暖』\n")

    # 阶段1：并行的独立查询
    t1 = get_temp("北京")
    t2 = get_temp("上海")
    print(f"  阶段1：get_temp(北京)={t1}°C，get_temp(上海)={t2}°C\n")

    # 阶段2：依赖上面结果的 compare 工具
    warmer_city = warmer(t1, t2)
    print(f"  阶段2：用 {t1}°C 与 {t2}°C 调用『比较』工具 → 更暖的是{warmer_city}\n")

    print("  要点：")
    print("    · 阶段2 的输入来自阶段1 的结果 → 不能和阶段1并行")
    print("    · 这种多步依赖，交给 Agent 的『决策→执行→再决策』循环更自然（见后续）")


if __name__ == "__main__":
    main()