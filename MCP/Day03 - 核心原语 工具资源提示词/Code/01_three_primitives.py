# -*- coding: utf-8 -*-
"""
Day03 - 01 三大原语总览

Tools（工具）/ Resources（资源）/ Prompts（提示词）的定位与区别。

离线可运行（纯讲解）。
"""


def overview():
    print("三大原语总览：\n")
    rows = [
        ("Tools 工具", "让模型『动手』——执行动作、产生副作用", "手"),
        ("Resources 资源", "让模型『读』——获取上下文数据", "眼睛/资料库"),
        ("Prompts 提示词", "复用固定话术/流程的模板", "模板库"),
    ]
    for name, desc, analogy in rows:
        print(f"  ■ {name}")
        print(f"     作用：{desc}")
        print(f"     类比：{analogy}\n")


def memory():
    print("  一句话记忆：")
    print("    『工具用来做事，资源用来读数据，提示词用来复用话术。』\n")


def decide():
    print("如何选择：\n")
    print("  需要改变外部世界吗  → Tools（写文件/发消息/调API）")
    print("  只需读取数据吗      → Resources（读配置/读文档/查schema）")
    print("  复用一段固定话术呢  → Prompts（代码评审/文档总结等）")


def main():
    print(">> MCP 三大原语\n")
    overview()
    memory()
    decide()
    print("\n  tips: 用『手、眼睛、模板』三个类比记最牢固。")


if __name__ == "__main__":
    main()