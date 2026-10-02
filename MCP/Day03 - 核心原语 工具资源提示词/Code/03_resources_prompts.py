# -*- coding: utf-8 -*-
"""
Day03 - 03 Resources 与 Prompts 详解

资源（只读、URI 寻址）与提示词（参数化模板）的结构与用途。

离线可运行（讲解 + 演示）。
"""


def resources():
    print("Resources（资源）——让模型『读』数据：\n")
    res = {
        "uri": "file:///project/config.json",
        "name": "项目配置",
        "description": "当前项目的配置文件",
        "mimeType": "application/json",
    }
    import json
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print("\n  特性：")
    print("    · 通过 URI 引用（file:// / memory:// / db:// ...）")
    print("    · 用 resources/read 读取 contents")
    print("    · 只读：模型读它，不改它（修改用 Tools）")
    print("    · 支持订阅，内容变化可通知客户端\n")
    print("  适用：项目文档、配置文件、数据库 schema、最近消息……\n")


def prompts():
    print("Prompts（提示词）——复用固定话术/流程：\n")
    p = {
        "name": "review_code",
        "description": "生成代码评审提示",
        "arguments": [
            {"name": "language", "description": "编程语言", "required": True}
        ],
    }
    import json
    print(json.dumps(p, ensure_ascii=False, indent=2))
    print("\n  特性：")
    print("    · 用 prompts/get 获取，返回 messages（角色+内容）")
    print("    · 参数在请求时填充")
    print("    · 内容是标准交互流程的入口\n")
    print("  适用：代码评审、文档总结、Bug 分析、入职引导……")


def analogy():
    print("\n" + "=" * 60)
    print("类比强化：")
    print("  Tools     = 动词（做一件事）")
    print("  Resources = 名词（一个数据结构）")
    print("  Prompts   = 快捷按钮（一键进入某流程）")


def main():
    print(">> Resources 与 Prompts\n")
    resources()
    prompts()
    analogy()
    print("\n  tips: 资源保证只读、提示词保证复用——这是它们与工具的本质差异。")


if __name__ == "__main__":
    main()