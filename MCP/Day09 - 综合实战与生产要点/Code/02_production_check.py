# -*- coding: utf-8 -*-
"""
Day09 - 02 上线自检清单

把 9 天要点收敛成一份“上线前 checklist”，逐项核对降低踩坑率。

离线可运行（纯清单）。
"""


def checklist():
    print("上线前自检清单：\n")
    checks = [
        ("最小权限", "工具只暴露该场景必要能力？无关工具已移除？"),
        ("参数校验", "每个工具的输入都做了范围/类型校验？异常已处理？"),
        ("敏感信息", "无硬编码密钥？敏感项走环境变量 / secret / env 字段？"),
        ("资源只读", "资源保持只读？所有写入都改为走 Tools？"),
        ("传输选择", "本地用 stdio？远程用 HTTP+OAuth 并暴露明文端口？"),
        ("认证", "HTTP 场景已配 OAuth？token 有过期与校验？"),
        ("调试验证", "已用 mcp dev / Inspector 逐个调用过工具？") ,
        ("真实客户端", "已在 Claude Desktop / Cline 等接入验证通过？"),
        ("超时容错", "长耗时工具有超时？工具失败不会让 Agent 挂死？"),
        ("可观测", "关键步骤有日志（logging/message）？便于线上排查？"),
    ]
    for i, (title, q) in enumerate(checks, 1):
        print(f"  ☐ {i}. {title}\n     质询：{q}\n")


def best_practice():
    print("=" * 60)
    print("生产最佳实践回顾：\n")
    print("  · 能力切面：一个 Server 只对外暴露一个业务面的能力")
    print("  · 求小求稳：工具名清晰、docstring 具体、参数 schema 严谨")
    print("  · 安全至上：最小权限 + 参数校验 + 密钥外置")
    print("  · 可观测：及时日志，远程用 HTTP + OAuth")


def main():
    print(">> 上线自检清单\n")
    checklist()
    best_practice()
    print("\n  tips: 循清单过一遍，就是一次完整的『MCP 生产走查』。")


if __name__ == "__main__":
    main()