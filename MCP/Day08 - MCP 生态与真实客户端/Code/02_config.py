# -*- coding: utf-8 -*-
"""
Day08 - 02 客户端接入配置（离线演示）

展示如何把自建 Server 以 stdio 方式接入真实客户端（Claude Desktop /
Cline / Cursor / VS Code 等），核心是 mcpServers 里的 command + args。

离线可运行（纯讲解）。
"""


def concept():
    print("接入原理：\n")
    print("  客户端把你声明的『命令 + 参数』作为子进程拉起 Server，")
    print("  然后经 stdio 连上它——这就是『接入』。你不必改 Server 代码。\n")


def json_config():
    print("通用配置形如（JSON）：\n")
    config = '''{
  "mcpServers": {
    "my-docs": {
      "command": "python",
      "args": ["D:/Coding/AI-FullStack/MCP/Day05 - 构建 MCP Server（二）资源与提示词/Code/server_resources.py"],
      "env": {}
    }
  }
}'''
    print(config)


def per_client():
    print("\n不同客户端入口：\n")
    rows = [
        ("Claude Desktop", "claude_desktop_config.json 中填 mcpServers"),
        ("Cline", "MCP 设置界面新增 → Server: 命令 + Args"),
        ("Cursor", "MCP 服务器设置 → 添加 stdio server"),
        ("VS Code", "扩展市场 MCP 配置，或社区扩展"),
    ]
    for k, v in rows:
        print(f"  · {k:<16}{v}")


def tips():
    print("\n注意事项：\n")
    print("  · args 用绝对路径最稳妥（客户端的工作目录未必是你的项目目录）")
    print("  · server 脚本输出不要混入 print 干扰（只有 mcp 消息该走 stdio）")
    print("  · 涉及密钥/token 用 env 字段注入，而不是写死在代码")


def main():
    print(">> 接入真实客户端\n")
    concept()
    json_config()
    per_client()
    tips()
    print("\n  tips: 配置错误时，先单独 `python server_xxx.py` 验证 Server 本身能起。")


if __name__ == "__main__":
    main()