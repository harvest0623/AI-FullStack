# 文件用途：分词器 Tokenizer 演示
# 使用 tiktoken 演示 GPT 的 BPE（Byte Pair Encoding）分词：
#   - 对英文 / 中文 / 代码三种文本分别切分，打印每个 Token 及其 ID
#   - 统计不同语言的 Token 效率（每 Token 平均字符数、字符/Token 比）
#   - 直观展示中文比英文消耗更多 Token 的现象
# 依赖：pip install tiktoken
# 本文件不需要 API Key，tiktoken 是本地分词库。

import sys

try:
    import tiktoken
except ImportError:
    print("缺少依赖 tiktoken，请先执行: pip install tiktoken")
    sys.exit(1)


def get_encoder(model: str = "gpt-4o") -> tiktoken.Encoding:
    """获取指定模型对应的 BPE 编码器。"""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        # 回退到通用 cl100k_base 编码（GPT-4 / GPT-3.5-turbo 通用）
        return tiktoken.get_encoding("cl100k_base")


def show_tokens(text: str, encoder: tiktoken.Encoding, label: str) -> None:
    """展示一段文本的 Token 切分情况。"""
    token_ids = encoder.encode(text)
    print(f"\n【{label}】 共 {len(token_ids)} 个 Token")
    print(f"原文: {text}")
    print(f"字符数: {len(text)}  |  Token 数: {len(token_ids)}  |  字符/Token: {len(text) / len(token_ids):.2f}")
    print("-" * 60)
    print(f"{'序号':<6}{'Token ID':<14}{'Token 文本'}")
    print("-" * 60)
    for idx, tid in enumerate(token_ids, 1):
        # decode 单个 Token 还原其文本（可能为不完整词或乱码字节）
        token_text = encoder.decode([tid])
        # 替换换行/空白以便显示
        display = token_text.replace("\n", "\\n").replace("\t", "\\t")
        print(f"{idx:<6}{tid:<14}{display}")


def compare_token_efficiency(encoder: tiktoken.Encoding) -> None:
    """对比英文/中文/代码的 Token 效率。"""
    samples = {
        "英文": "The quick brown fox jumps over the lazy dog. Natural language processing is fascinating.",
        "中文": "敏捷的棕色狐狸跳过了懒狗。自然语言处理非常有趣，是大语言模型的基础技术。",
        "代码": "def add(a, b):\n    return a + b\n\nprint(add(1, 2))",
    }

    print("\n" + "=" * 60)
    print("不同语言的 Token 效率对比")
    print("=" * 60)
    print(f"{'语言':<8}{'字符数':<10}{'Token数':<12}{'字符/Token':<14}{'Token/字'}")
    print("-" * 60)
    for lang, text in samples.items():
        token_ids = encoder.encode(text)
        char_count = len(text)
        token_count = len(token_ids)
        chars_per_token = char_count / token_count
        tokens_per_char = token_count / char_count
        print(f"{lang:<8}{char_count:<10}{token_count:<12}{chars_per_token:<14.2f}{tokens_per_char:.3f}")

    print("\n结论：")
    print("- 英文：约 4 个字符 / Token，效率最高")
    print("- 中文：约 1.5-2 个字符 / Token，相同语义消耗更多 Token（成本更高）")
    print("- 代码：含大量符号与缩进，Token 消耗介于英文与中文之间")


def compare_models(text: str) -> None:
    """对比不同编码器对同一段文本的 Token 数量。"""
    print("\n" + "=" * 60)
    print("不同编码器对比（同一中文文本）")
    print("=" * 60)
    print(f"文本: {text}\n")
    encodings = {
        "cl100k_base (GPT-4/3.5)": tiktoken.get_encoding("cl100k_base"),
        "o200k_base (GPT-4o)": tiktoken.get_encoding("o200k_base"),
    }
    for name, enc in encodings.items():
        try:
            n = len(enc.encode(text))
            print(f"  {name:<28} -> {n} 个 Token")
        except Exception as e:  # noqa: BLE001
            print(f"  {name:<28} -> 编码失败: {e}")


def main() -> None:
    encoder = get_encoder("gpt-4o")
    print("=" * 60)
    print("GPT BPE 分词器演示（tiktoken）")
    print(f"使用编码器: {encoder.name}")
    print("=" * 60)

    show_tokens("Hello world", encoder, "英文示例")
    show_tokens("大语言模型正在改变世界", encoder, "中文示例")
    show_tokens("print('hello')\nfor i in range(3):\n    print(i)", encoder, "代码示例")

    compare_token_efficiency(encoder)
    compare_models("大语言模型正在改变世界，让自然语言处理变得前所未有的强大。")

    print("\n提示：BPE 会将未见过的词拆成子词甚至字节，所以中文常被拆为单字或更小单位，导致 Token 数偏多。")


if __name__ == "__main__":
    main()
