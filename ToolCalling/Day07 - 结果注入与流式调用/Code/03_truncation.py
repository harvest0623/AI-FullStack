# -*- coding: utf-8 -*-
"""
Day07 - 03 大结果截断/摘要策略

工具返回巨大时，如何控制注入模型上下文的大小。

离线可运行（讲解 + 演示）。
"""


def truncate(text, limit=200):
    """按字符截断，保留开头。"""
    return text[:limit] + ("…" if len(text) > limit else "")


def first_lines(text, n=5):
    """只保留前 n 行。"""
    lines = text.splitlines()
    return "\n".join(lines[:n]) + ("\n…" if len(lines) > n else "")


def summarize_placeholder(text):
    """示意：可调用 LLM 或规则生成摘要（这里演示占位）。"""
    return f"（摘要）共 {len(text)} 字，要点见正文……"


def main():
    print(">> 大结果的截断与摘要\n")
    big = "\n".join(f"这是日志的第 {i} 行，包含一些详细内容 " + "x" * 30
                    for i in range(1, 101))
    print(f"原始结果：{len(big)} 字\n")

    print(f"① 截断到 200 字：\n   {truncate(big)!r}\n")
    print(f"② 只取前 5 行：\n   {first_lines(big)!r}\n")
    print(f"③ 摘要占位：\n   {summarize_placeholder(big)!r}\n")

    print("策略选择：")
    print("  · 需要细节 → 截断（保留头/关键段）")
    print("  · 只需概况 → 摘要，或只给统计信息")
    print("  · 超大量   → 落盘后回填『结果已存入 source.txt』，按需再读")


if __name__ == "__main__":
    main()