# 文件用途：国内大模型 API 调用示例
# 演示三类调用方式：
#   1) 通义千问 DashScope —— 兼容 OpenAI 格式（用 openai SDK 指向 dashscope base_url）
#   2) 智谱清言 GLM       —— 原生 zhipuai SDK
#   3) DeepSeek           —— 兼容 OpenAI 格式（用 openai SDK 指向 deepseek base_url）
# 依赖：pip install openai zhipuai python-dotenv
# 在 .env 中配置对应 Key（见各函数）

import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    print("缺少依赖 python-dotenv，请执行: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("缺少依赖 openai，请执行: pip install openai")
    sys.exit(1)

load_dotenv()


# ============================================================
# 1. 通义千问 DashScope（兼容 OpenAI 格式）
# ============================================================
def dashscope_via_openai_sdk() -> None:
    """
    通义千问 DashScope 提供 OpenAI 兼容接口：
    只需把 base_url 指向 https://dashscope.aliyuncs.com/compatible-mode/v1，
    即可用 openai SDK 调用 Qwen 系列。
    需要 .env 中配置：DASHSCOPE_API_KEY
    """
    print("=" * 60)
    print("1. 通义千问 Qwen（DashScope 兼容 OpenAI 格式）")
    print("=" * 60)
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("⚠️ 未配置 DASHSCOPE_API_KEY，跳过本示例\n")
        return
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是中文写作助手，回答简洁。"},
            {"role": "user", "content": "用一句话介绍杭州。"},
        ],
    )
    print(f"Qwen 回复: {resp.choices[0].message.content}\n")


# ============================================================
# 2. 智谱清言 GLM（原生 zhipuai SDK）
# ============================================================
def zhipu_native_sdk() -> None:
    """
    智谱清言提供原生 zhipuai SDK，接口风格与 OpenAI 类似但有差异。
    需要 .env 中配置：ZHIPUAI_API_KEY
    依赖：pip install zhipuai
    """
    print("=" * 60)
    print("2. 智谱清言 GLM（原生 zhipuai SDK）")
    print("=" * 60)
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        print("⚠️ 未配置 ZHIPUAI_API_KEY，跳过本示例\n")
        return
    try:
        from zhipuai import ZhipuAI
    except ImportError:
        print("⚠️ 缺少依赖 zhipuai，请执行: pip install zhipuai，跳过本示例\n")
        return
    client = ZhipuAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "user", "content": "用一句话介绍深度学习。"}
        ],
    )
    print(f"GLM 回复: {resp.choices[0].message.content}\n")


# ============================================================
# 3. DeepSeek（兼容 OpenAI 格式）
# ============================================================
def deepseek_via_openai_sdk() -> None:
    """
    DeepSeek 完全兼容 OpenAI API 格式，把 base_url 指向
    https://api.deepseek.com 即可用 openai SDK 调用。
    需要 .env 中配置：DEEPSEEK_API_KEY
    """
    print("=" * 60)
    print("3. DeepSeek（兼容 OpenAI 格式）")
    print("=" * 60)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️ 未配置 DEEPSEEK_API_KEY，跳过本示例\n")
        return
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "用一句话解释 MoE（混合专家）架构的优势。"}
        ],
    )
    print(f"DeepSeek 回复: {resp.choices[0].message.content}\n")


def main() -> None:
    dashscope_via_openai_sdk()
    zhipu_native_sdk()
    deepseek_via_openai_sdk()
    print("=" * 60)
    print("小结：国内模型 API 调用要点")
    print("=" * 60)
    print("- 多数国内模型（Qwen/DeepSeek/Kimi/智谱兼容模式）提供 OpenAI 兼容接口")
    print("- 只需更换 base_url + 对应 API Key，即可复用 openai SDK，迁移成本极低")
    print("- 智谱也提供原生 zhipuai SDK，部分高级能力（如智谱清言特有功能）需用原生 SDK")
    print("- 国产模型中文能力普遍更强、价格更低，适合中文场景与成本敏感业务")


if __name__ == "__main__":
    main()
