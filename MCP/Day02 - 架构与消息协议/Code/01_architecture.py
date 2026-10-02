# -*- coding: utf-8 -*-
"""
Day02 - 01 MCP 架构层次与生命周期

讲解 MCP 的分层结构（原语/生命周期/消息/传输）以及一次会话的生命周期流程。

离线可运行（纯讲解）。
"""


def layers():
    print("MCP 协议层次：\n")
    print("""   ┌──────────────────────────────────────────────┐
   │ 原语层    Tools / Resources / Prompts / Roots  │  ← 业务能力
   ├──────────────────────────────────────────────┤
   │ 生命周期    initialize → initialized → 操作     │  ← 会话流程
   ├──────────────────────────────────────────────┤
   │ 消息层    JSON-RPC 2.0                        │  ← 通信格式
   │           (request / response / notification)  │
   ├──────────────────────────────────────────────┤
   │ 传输层    stdio ｜ Streamable HTTP             │  ← 落地管道
   └──────────────────────────────────────────────┘
   """)
    print("  一句话：原语层决定『能做什么』，消息层决定『格式』，")
    print("          传输层决定『怎么传』，生命周期决定『顺序』。")


def lifecycle():
    print("一次会话的生命周期：\n")
    steps = [
        ("Client", "── initialize(request) ──▶", "Server", "首个握手：协商版本与能力"),
        ("Client", "◀── initialize(result) ──", "Server", "返回协议版本、capabilities"),
        ("Client", "── notifications/initialized ──▶", "Server", "告知『我准备好了』"),
        ("Client", "── tools/list ──▶", "Server", "能力发现（按需）"),
        ("Client", "── tools/call ──▶", "Server", "实际调用工具/读资源"),
        ("Client", "◀── 返回结果 ──", "Server", "回传给 LLM"),
        ("Client", "── 关闭连接 ──", "Server", "会话结束"),
    ]
    for a, arrow, b, note in steps:
        print(f"    {a:<10} {arrow:<30} {b:<8}  {note}")

    print("\n  关键约束：")
    print("    · initialize 必须是第一条消息（唯一握手）")
    print("    · notifications/initialized 表示 Client 就绪")
    print("    · initialize 里互相汇报 capabilities（支持的子能力）")


def main():
    print(">> MCP 架构与生命周期\n")
    layers()
    print("\n" + "=" * 60)
    lifecycle()
    print("\n  tips: 用 SDK 写代码时握手是自动的，你只需关心业务原语。")


if __name__ == "__main__":
    main()