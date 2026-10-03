# -*- coding: utf-8 -*-
"""
Day08 - 01 MCP 生态图景与参考 Server

讲清生态构成，以及常见官方参考 Server 的能力与用途。

离线可运行（纯讲解）。
"""


def ecosystem():
    print("MCP 生态构成：\n")
    rows = [
        ("官方/社区 Server", "filesystem / github / sqlite / fetch / memory 等"),
        ("框架适配", "LangChain、LlamaIndex、OpenAI/Anthropic 工具转为 MCP"),
        ("真实客户端 Host", "Claude Desktop、Cline、Cursor、VS Code、自研应用"),
        ("协议/SDK", "MCP 规范 + Python/TS 官方 SDK"),
    ]
    for k, v in rows:
        print(f"  ■ {k:<16}{v}\n")


def ref_servers():
    print("常用官方参考 Server（modelcontextprotocol/servers 仓库）：\n")
    rows = [
        ("filesystem", "读写文件系统", "本地文件操作、存取"),
        ("github", "GitHub Repo/Issue/PR 操作", "代码协作、自动化"),
        ("sqlite", "SQLite 查询与操作", "本地数据探查"),
        ("fetch", "抓取网页转 Markdown", "网页内容读取"),
        ("memory", "长期记忆存储", "Agent 记忆/知识库"),
    ]
    for name, ability, scene in rows:
        print(f"  · {name:<12} {ability}")
        print(f"      场景：{scene}")


def why_references():
    print("\n为什么值得看参考 Server？\n")
    print("  它们是官方维护、最小且规范的实现，是学习 Server 写法的最佳样本：")
    print("  如何组织工具/资源、如何处理错误、如何划分模块。")


def main():
    print(">> MCP 生态\n")
    ecosystem()
    ref_servers()
    why_references()
    print("\n  tips: 生态的关键是『统一协议』——同一套 Server 可被任意客户端复用。")


if __name__ == "__main__":
    main()