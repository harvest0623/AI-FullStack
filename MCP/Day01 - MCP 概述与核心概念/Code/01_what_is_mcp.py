# -*- coding: utf-8 -*-
"""
Day01 - 01 MCP 是什么

介绍 MCP 的定位：它是连接 AI 应用与外部工具/数据源的开放协议，
并拆解它真正解决的核心痛点。

离线可运行（纯讲解）。
"""


def what_is_mcp():
    print("MCP（Model Context Protocol · 模型上下文协议）\n")
    print("  一句话：让 AI 应用通过标准化的 Server，安全、统一地连接外部")
    print("           工具、数据源与服务。\n")
    print("  三个关键词：")
    print("    标准化  —— 一套协议，任意客户端可接入任意 Server")
    print("    上下文 —— 把外部数据/能力『塞进』模型的上下文")
    print("    协议   —— 客户端与服务端的通信约定（含消息格式、生命周期）\n")


def pain_points():
    print("它解决的核心痛点：\n")
    rows = [
        ("模型只会想不会做", "模型能生成文本，但要『行动』（写文件/查库/调API）就卡住"),
        ("接入每个工具都要定制", "N 个工具 = N 套私有集成代码，无法复用"),
        ("上下文很『窄』", "模型只能看到喂给它的文本，看不到文件/数据库/线上服务"),
        ("能力暴露不统一", "每个团队各自定义『怎么被调用』，生态割裂"),
        ("安全难管", "权限、可控性、可审计在私有接入里欠标准"),
    ]
    for title, desc in rows:
        print(f"  ■ {title}")
        print(f"     {desc}\n")


def before_after():
    print("有/无 MCP 的对比：\n")
    print("  无 MCP：每个工具都要单独写集成")
    print("    写文件工具 → 专用插件A；GitHub工具 → 专用插件B；浏览器 → 专用插件C")
    print("    换个宿主App，全部重写。\n")
    print("  有 MCP：Server 包一层，任意客户端即插即用")
    print("    [我做的 Server1](工具) ──► 可被 Claude / Cline / Cursor / 自研App 使用")
    print("    [官方 GitHub Server] ────► 同样一套标准\n")


def main():
    print(">> MCP 是什么\n")
    what_is_mcp()
    pain_points()
    before_after()
    print("  tips: MCP 的核心贡献不是『某种工具』，而是『统一标准』。")
    print("        后续章节的一切都围绕这套标准展开。")


if __name__ == "__main__":
    main()