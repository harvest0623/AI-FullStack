# -*- coding: utf-8 -*-
"""
Day09 - 02 上线自检清单

把本模块要点收敛成一份上线前 checklist，逐项核对降低踩坑率。

离线可运行（纯清单）。
"""


def checklist():
    print("上线自检清单：\n")
    checks = [
        ("工具定义", "每个工具 name 稳定 + description 写清目的/参数/何时用？"),
        ("参数约束", "类型与必填都用 JSON Schema 明确约束？enum 范围合理？"),
        ("参数校验", "执行前有必填/类型校验？非法输入能拒绝？"),
        ("异常兜底", "执行异常统一转成 tool 错误结果回填？"),
        ("权限安全", "有副作用的危险工具已控制权限/需用户确认？不信任模型参数？"),
        ("防死循环", "循环设了最大迭代数？达限能优雅结束？"),
        ("上下文控制", "大结果已截断/摘要？不撑爆上下文？"),
        ("流式正确", "流式场景按 index 正确拼接 tool_calls？"),
        ("可移植", "无硬编码 key/路径？换模型端点也能跑？"),
        ("可观测", "有日志能定位是哪次调用失败？"),
    ]
    for i, (title, q) in enumerate(checks, 1):
        print(f"  ☐ {i}. {title}\n     质询：{q}\n")


def summary():
    print("=" * 60)
    print("回顾本模块：")
    print("  · 本质：模型提议、应用执行、结果回填（Day01）")
    print("  · 形态：tools + tool_calls + role=tool（Day02/04/07）")
    print("  · 工程：schema、解析校验、循环、错误、流式（Day03-07）")
    print("  · 落地：接入框架 / 自建 Agent / 最佳实践（Day08-09）")


def main():
    print(">> 上线自检清单\n")
    checklist()
    summary()
    print("\n  tips: 循清单走一遍，就是一次完整的 ToolCalling 工程走查。")


if __name__ == "__main__":
    main()