# -*- coding: utf-8 -*-
"""
Day02 - 03 传输方式：stdio 与 Streamable HTTP

对比 MCP 的两种传输，理解其适用场景。

离线可运行（纯讲解）。
"""


def transports():
    print("两种传输方式：\n")
    print("  ① stdio（标准输入/输出）")
    print("     · 本地：Host 以子进程启动 Server，经 stdin/stdout 交换消息")
    print("     · 每行一条 JSON 消息")
    print("     · 适合：本地开发、桌面客户端\n")
    print("     Client 进程 ──stdin──▶ Server 进程")
    print("     Client 进程 ◀──stdout─ Server 进程\n")
    print("  ② Streamable HTTP（可流式 HTTP）")
    print("     · 远程：基于 HTTP，支持 SSE 流式返回")
    print("     · Client 用 POST 请求，Server 可流式下发结果")
    print("     · 适合：把 Server 部署到服务器，远程/多客户端接入\n")


def compare():
    print("对比表：\n")
    rows = [
        ("场景", "本地子进程", "远程 / 多客户端"),
        ("通道", "stdin / stdout", "HTTP + SSE"),
        ("认证", "无需", "常需 OAuth 等"),
        ("部署", "随宿主进程", "独立服务，可横向扩展"),
        ("适用例", "Claude Desktop、自研本工具", "云端服务、多应用共享能力"),
    ]
    print(f"{'维度':<8}{'stdio':<16}{'Streamable HTTP'}")
    print("-" * 52)
    for a, b, c in rows:
        print(f"{a:<8}{b:<16}{c}")


def how_to_choose():
    print("\n怎么选？\n")
    print("  · 单机 / 桌面 / 安全敏感    → 用 stdio（简单、无需暴露端口）")
    print("  · 云端 / 多客户端 / 共享能力 → 用 Streamable HTTP")
    print("  · 一个 Server 也可同时支持两种传输（SDK 常可配置）")


def main():
    print(">> 传输方式：stdio vs HTTP\n")
    transports()
    compare()
    how_to_choose()
    print("\n  tips: 初学建议先把 stdio 跑通——它不需要网络配置，聚焦业务本身。")


if __name__ == "__main__":
    main()