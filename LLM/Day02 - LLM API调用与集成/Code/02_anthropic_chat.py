# 文件用途：Anthropic Claude API 调用完整示例
# 演示：基础对话 / system 顶级参数 / max_tokens 必填 / 多轮对话
# 并对比与 OpenAI API 的关键差异。
# 依赖：pip install anthropic python-dotenv
# 在 .env 中配置 ANTHROPIC_API_KEY

import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    print("缺少依赖 python-dotenv，请执行: pip install python-dotenv")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("缺少依赖 anthropic，请执行: pip install anthropic")
    sys.exit(1)

load_dotenv()


def build_client() -> anthropic.Anthropic:
    """构造 Claude 客户端。"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未检测到 ANTHROPIC_API_KEY，请在 .env 文件中写入：\n"
            'ANTHROPIC_API_KEY=sk-ant-你的密钥'
        )
    return anthropic.Anthropic(api_key=api_key)


# ============================================================
# 1. 基础对话（注意：max_tokens 是必填参数）
# ============================================================
def basic_chat(client: anthropic.Anthropic) -> None:
    print("=" * 60)
    print("1. Claude 基础对话")
    print("=" * 60)
    # 与 OpenAI 关键差异①：system 是顶级参数，不在 messages 中
    # 与 OpenAI 关键差异②：max_tokens 必填（OpenAI 可选）
    resp = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,  # 必填！
        system="你是一位简洁的技术助手，回答不超过 60 字。",
        messages=[
            {"role": "user", "content": "什么是 RLHF？"}
        ],
    )
    # 与 OpenAI 差异③：返回内容在 content 数组中
    text = "".join(block.text for block in resp.content if block.type == "text")
    print(f"回复: {text}")
    print(f"stop_reason: {resp.stop_reason}")
    print(f"usage: input={resp.usage.input_tokens} output={resp.usage.output_tokens}\n")


# ============================================================
# 2. system 参数对比 OpenAI
# ============================================================
def system_param_demo(client: anthropic.Anthropic) -> None:
    print("=" * 60)
    print("2. system 顶级参数（设定为代码审查专家）")
    print("=" * 60)
    resp = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        system=(
            "你是严格的代码审查专家。对用户给出的代码指出 1-2 个问题，"
            "语气专业，不超过 100 字。"
        ),
        messages=[
            {"role": "user", "content": "def add(a,b):return a+b\nprint(add(1,'2'))"}
        ],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    print(f"回复: {text}\n")


# ============================================================
# 3. 多轮对话
# ============================================================
def multi_turn_chat(client: anthropic.Anthropic) -> None:
    print("=" * 60)
    print("3. Claude 多轮对话")
    print("=" * 60)
    # 注意：Claude 的 messages 中 user 与 assistant 必须交替出现
    messages = [
        {"role": "user", "content": "什么是向量数据库？"},
        {
            "role": "assistant",
            "content": "向量数据库是专门存储和检索高维向量的数据库，"
                       "支持近似最近邻搜索，常用于语义检索和 RAG。",
        },
        {"role": "user", "content": "它和传统数据库最大的区别是什么？"},
    ]
    resp = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=messages,
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    print(f"回复: {text}\n")


# ============================================================
# 4. temperature 参数（Claude 默认 1.0）
# ============================================================
def temperature_demo(client: anthropic.Anthropic) -> None:
    print("=" * 60)
    print("4. temperature 对比（Claude 默认 1.0）")
    print("=" * 60)
    for temp in [0.0, 1.0]:
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=128,
            temperature=temp,
            messages=[{"role": "user", "content": "用一句话形容 Embedding 的作用。"}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        print(f"temperature={temp}: {text}\n")


def main() -> None:
    client = build_client()
    basic_chat(client)
    system_param_demo(client)
    multi_turn_chat(client)
    temperature_demo(client)
    print("=" * 60)
    print("Claude vs OpenAI 关键差异小结：")
    print("=" * 60)
    print("1. system 是顶级参数，而非 messages 内的一条消息")
    print("2. max_tokens 必填（OpenAI 可选）")
    print("3. 返回内容在 content 数组中（OpenAI 是 message.content 字符串）")
    print("4. temperature 默认 1.0，范围 0-1（OpenAI 默认 1.0，范围 0-2）")
    print("5. messages 必须严格 user/assistant 交替")


if __name__ == "__main__":
    main()
