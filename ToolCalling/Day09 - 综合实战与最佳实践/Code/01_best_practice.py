# -*- coding: utf-8 -*-
"""
Day09 - 01 最佳实践

工具描述的写作规范、参数校验与安全、失败降级的要点。

离线可运行（纯讲解）。
"""


def naming():
    print("工具描述写作规范：\n")
    rows = [
        ("名称", "稳定、语义化，动词开头（get/add/update…）"),
        ("description", "写清目的、参数含义、何时用，给取值示例"),
        ("schema", "类型准确、必填明确、enum 限定范围"),
        ("职责", "一个工具只做一件事，短路复用"),
        ("副作用", "会写/改外部状态的在描述里点明"),
    ]
    for k, v in rows:
        print(f"  · {k:<12}{v}")


def safety():
    print("\n参数安全与权限：\n")
    checks = [
        "执行前：必填 + 类型校验",
        "执行中：异常统一转错误结果回填",
        "危险操作（改库/转账）：需用户确认",
        "不『信任』模型参数，应用侧二次校验",
    ]
    for c in checks:
        print(f"  ✓ {c}")


def degrade():
    print("\n失败降级：\n")
    rows = [
        ("工具失败", "回填错误 → 模型重试或换方案"),
        ("缺参数", "可选默认值（如默认北京），但要明确"),
        ("超时/无响应", "终止本轮，给用户兜底话术"),
    ]
    for k, v in rows:
        print(f"  · {k:<12}{v}")


def main():
    print(">> 最佳实践\n")
    naming()
    safety()
    degrade()
    print("\n  tips: 规范的描述 = 更准的调用；二次校验 = 更安全的上线。")


if __name__ == "__main__":
    main()