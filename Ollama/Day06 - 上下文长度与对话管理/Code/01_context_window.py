# -*- coding: utf-8 -*-
"""
Day06 - 01 num_ctx 与 token 统计

演示上下文窗口如何工作：
1. num_ctx 含义与默认值（2048）
2. 把"系统提示 + 历史 + 当前输入"的估算 token 累加
3. 判断是否超限，超限该怎么做

规则演示（无真实模型也能看到逻辑），有 Ollama 时可叠加真实验证。
"""

# 一个极简的中文 token 估算：这里按"约 1 个汉字 ≈ 1 token"做教学近似
# 注：真实模型是子词切分，此处简化便于理解"算账"
APPROX_TOKEN_PER_CHAR = 1.0


def est_tokens(text: str) -> int:
    """估算文本 token 数（教学简化）"""
    return max(1, int(len(text) * APPROX_TOKEN_PER_CHAR))


def build_context(system: str, history: list[tuple[str, str]], user_input: str):
    """把各部分拼起来，并逐段统计 token"""
    lines = [("system", system), *history, ("user", user_input)]
    total = 0
    rows = []
    for role, content in lines:
        n = est_tokens(content)
        total += n
        rows.append((role, len(content), n))
    return rows, total


def main():
    print(">> num_ctx 与 token 统计\n")

    system = "你是一名耐心的客服：简洁、友好。"
    history = [
        ("user", "我家的灯坏了"),
        ("assistant", "别急，请问是哪里亮不了？"),
        ("user", "客厅落地灯"),
    ]
    user_input = "好的，我该怎么处理？"

    rows, total = build_context(system, history, user_input)
    print("已用 token 明细（估算，1汉字≈1token）：")
    for role, chars, n in rows:
        print(f"  {role:<10} {chars:>4} 字符 → {n:>4} token")
    print(f"\n  合计已用：{total} token")

    for num_ctx in [2048, 512, 128]:
        left = num_ctx - total
        status = "正常" if left >= 0 else "超限！"
        print(f"  num_ctx={num_ctx}: 剩余 {left} token  →  {status}")

    print("\n说明：")
    print("  - num_ctx 默认 2048，可调大装更长文本，但更慢、更吃显存")
    print("  - 超限会被截断或报错，看 Day06 的历史裁剪如何解决")

    # 真实验证提示
    print("\n  tips: 启动 Ollama 后，在请求 options 里加 num_ctx 即可调整窗口")


if __name__ == "__main__":
    main()