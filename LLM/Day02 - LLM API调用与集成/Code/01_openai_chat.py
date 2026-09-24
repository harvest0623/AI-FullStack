# 文件用途：OpenAI Chat Completions API 调用完整示例
# 演示：基础对话 / 多轮对话 / System Prompt 设定 / temperature 对比 /
#       max_tokens 限制 / JSON Mode 输出 / response_format 指定 / 错误处理
# 使用 python-dotenv 从 .env 加载 OPENAI_API_KEY，绝不硬编码。
# 依赖：pip install openai python-dotenv

import json
import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    print("缺少依赖 python-dotenv，请执行: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI, APIError, RateLimitError, AuthenticationError
except ImportError:
    print("缺少依赖 openai，请执行: pip install openai")
    sys.exit(1)

# 加载 .env 中的环境变量
load_dotenv()


def build_client() -> OpenAI:
    """构造 OpenAI 客户端，API Key 从环境变量读取。"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未检测到 OPENAI_API_KEY，请在项目根目录创建 .env 文件并写入：\n"
            'OPENAI_API_KEY=sk-你的密钥'
        )
    # 如使用兼容 OpenAI 格式的代理/第三方服务，可设置 OPENAI_BASE_URL
    base_url = os.getenv("OPENAI_BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)


# ============================================================
# 1. 基础对话
# ============================================================
def basic_chat(client: OpenAI) -> None:
    print("=" * 60)
    print("1. 基础对话")
    print("=" * 60)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "用一句话解释什么是 Transformer 架构。"}
        ],
    )
    print(f"回复: {resp.choices[0].message.content}")
    print(f"finish_reason: {resp.choices[0].finish_reason}")
    print(f"usage: {resp.usage}\n")


# ============================================================
# 2. System Prompt 设定身份与行为规范
# ============================================================
def system_prompt_chat(client: OpenAI) -> None:
    print("=" * 60)
    print("2. System Prompt 设定（让模型扮演资深 AI 讲师）")
    print("=" * 60)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "你是一位资深 AI 讲师，回答风格简洁、重点突出，"
                           "每条回答不超过 80 字，结尾附一个思考题。",
            },
            {"role": "user", "content": "什么是注意力机制？"},
        ],
    )
    print(f"回复: {resp.choices[0].message.content}\n")


# ============================================================
# 3. 多轮对话（携带历史消息）
# ============================================================
def multi_turn_chat(client: OpenAI) -> None:
    print("=" * 60)
    print("3. 多轮对话（携带对话历史）")
    print("=" * 60)
    messages = [
        {"role": "system", "content": "你是一个友好的编程助手。"},
        {"role": "user", "content": "Python 中 list 和 tuple 有什么区别？"},
        {
            "role": "assistant",
            "content": "list 可变、用方括号；tuple 不可变、用圆括号，"
                       "tuple 因不可变更轻量、可作字典键。",
        },
        {"role": "user", "content": "那它们谁的访问速度更快？"},
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    print(f"回复: {resp.choices[0].message.content}\n")


# ============================================================
# 4. temperature 参数对比
# ============================================================
def temperature_compare(client: OpenAI) -> None:
    print("=" * 60)
    print("4. temperature 对比（低=稳定，高=多样）")
    print("=" * 60)
    prompt = "用一个比喻形容大语言模型。"
    for temp in [0.0, 0.7, 1.5]:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
        )
        print(f"temperature={temp}:\n  {resp.choices[0].message.content}\n")


# ============================================================
# 5. max_tokens 限制输出长度
# ============================================================
def max_tokens_demo(client: OpenAI) -> None:
    print("=" * 60)
    print("5. max_tokens 限制输出长度")
    print("=" * 60)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "详细介绍 Python 的 GIL。"}],
        max_tokens=50,
    )
    print(f"回复: {resp.choices[0].message.content}")
    print(f"finish_reason: {resp.choices[0].finish_reason}  "
          f"(length 表示因 max_tokens 截断)\n")


# ============================================================
# 6. JSON Mode 输出
# ============================================================
def json_mode_demo(client: OpenAI) -> None:
    print("=" * 60)
    print("6. JSON Mode 结构化输出")
    print("=" * 60)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "你是信息抽取助手，只输出 JSON。",
            },
            {
                "role": "user",
                "content": "抽取这句话的信息：张三，28岁，在北京做算法工程师。"
                           '返回格式 {"name":"","age":0,"city":"","job":""}',
            },
        ],
        response_format={"type": "json_object"},  # 启用 JSON Mode
    )
    raw = resp.choices[0].message.content
    print(f"原始输出: {raw}")
    try:
        parsed = json.loads(raw)
        print(f"解析成功: {parsed}")
    except json.JSONDecodeError:
        print("JSON 解析失败")
    print()


# ============================================================
# 7. 完整错误处理示例
# ============================================================
def chat_with_error_handling(client: OpenAI) -> None:
    print("=" * 60)
    print("7. 带完整错误处理的调用")
    print("=" * 60)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "你好"}],
            timeout=30,
        )
        print(f"回复: {resp.choices[0].message.content}\n")
    except AuthenticationError:
        print("❌ 鉴权失败：请检查 OPENAI_API_KEY 是否正确")
    except RateLimitError:
        print("❌ 触发限流(429)：请降低调用频率或稍后重试（建议指数退避）")
    except APIError as e:
        print(f"❌ API 错误: {e}")
    except Exception as e:  # noqa: BLE001
        print(f"❌ 其他错误: {e}")


def main() -> None:
    client = build_client()
    basic_chat(client)
    system_prompt_chat(client)
    multi_turn_chat(client)
    temperature_compare(client)
    max_tokens_demo(client)
    json_mode_demo(client)
    chat_with_error_handling(client)


if __name__ == "__main__":
    main()
