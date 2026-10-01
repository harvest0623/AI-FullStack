# -*- coding: utf-8 -*-
"""
Day01 - 02 三大角色：Host / Client / Server

讲解 MCP 的最小协作模型：宿主、客户端、服务端各自干什么，
以及它们之间的关系（一个 Host 通常有多个 Client，每个 Client 连一个 Server）。

离线可运行（纯讲解）。
"""


def roles():
    print("三角色一览：\n")
    rows = [
        ("Host 宿主", "面向用户的应用程序", "『指挥部/前台』"),
        ("Client 客户端", "宿主体内、与 Server 1:1 连接的中介", "『对接专员』"),
        ("Server 服务端", "暴露能力，封装外部系统", "『能力提供方』"),
    ]
    for name, desc, analogy in rows:
        print(f"  ■ {name}")
        print(f"     职责：{desc}")
        print(f"     类比：{analogy}\n")


def relationship():
    print("关键关系图：\n")
    print("""         ┌──────────── 宿 主 Host ────────────┐
         │ 用户交互    +    LLM 应用逻辑          │
         │   ┌───────────────┐                    │
         │   │ Client 客户端 ─┼──────┐            │
         │   │ Client 客户端 ─┼──┐   │  每个Client│
         │   └───────────────┘  │   │  对应一个  │
         └──────────────┬───────┘   │  Server    │
                        ▼           ▼            │
                 ┌────────────┐ ┌────────────┐    │
                 │ Server A   │ │ Server B   │    │
                 └────────────┘ └────────────┘    │
    """)
    print("  记忆要点：")
    print("    一个 Host 可以有『多个 Client』（每组能力一个）")
    print("    一个 Client 只连『一个 Server』（一对一）")
    print("    用户永远只跟 Host 打交道，不直接碰 Server")


def hb():
    print("\n三者是怎么协作的？\n")
    steps = [
        "用户对 Host 说：『查一下我的待办清单』",
        "Host 让 LLM 规划：这个需求需要『读文件』这个能力",
        "对应 Client 向 Server 发请求，问『你有什么工具/资源？』",
        "Client 调用想要的工具（tools/call），或读取资源（resources/read）",
        "结果回传给 LLM，LLM 组织语言回复用户",
    ]
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")


def main():
    print(">> Host / Client / Server\n")
    roles()
    relationship()
    hb()
    print("\n  tips: 记住『内多外单』—— Host 内部多 Client，外部每个 Server 一对一连。")


if __name__ == "__main__":
    main()