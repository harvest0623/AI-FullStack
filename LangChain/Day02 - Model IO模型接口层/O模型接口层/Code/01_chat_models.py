# 文件用途：ChatModel 实例化与调用
# 演示 ChatOpenAI / ChatAnthropic / ChatOllama 三种 ChatModel 的实例化
# 调用 invoke 并分析 AIMessage 的结构（content / usage_metadata / response_metadata）
# 运行前请确保已安装依赖并配置 .env 中的 API Key

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def check_api_key(key_name="OPENAI_API_KEY"):
    """检查 API Key 是否配置"""
    if not os.getenv(key_name):
        print(f"⚠️  未检测到 {key_name}，将跳过对应模型调用\n")
        return False
    return True


# ============================================================
# 1. ChatOpenAI 实例化与调用
# ============================================================
def demo_chat_openai():
    """ChatOpenAI 实例化与 AIMessage 结构分析"""
    print("=" * 60)
    print("【1】ChatOpenAI 实例化与调用")
    print("=" * 60)

    if not check_api_key("OPENAI_API_KEY"):
        return

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    # 实例化 ChatOpenAI
    model = ChatOpenAI(
        model="gpt-4o-mini",      # 模型名称
        temperature=0.7,            # 随机性
        max_tokens=500,             # 最大输出 Token
        timeout=30,                 # 超时秒数
        max_retries=2,              # 最大重试
    )

    print(f"模型类型：{type(model).__name__}")
    print(f"模型名称：{model.model_name}")
    print(f"温度参数：{model.temperature}\n")

    # 构造消息列表
    messages = [
        SystemMessage(content="你是一个简洁的技术助手，回答不超过 50 字。"),
        HumanMessage(content="什么是 LangChain 的 LCEL？"),
    ]

    # invoke 调用，返回 AIMessage
    result = model.invoke(messages)

    # 分析 AIMessage 的结构
    print("AIMessage 结构分析：")
    print(f"  ① content（正文）：{result.content}")
    print(f"  ② type（类型）：{result.type}")
    print(f"  ③ id（消息 ID）：{result.id}")
    print(f"  ④ usage_metadata（Token 用量）：")
    for key, value in result.usage_metadata.items():
        print(f"      {key}: {value}")
    print(f"  ⑤ response_metadata（模型元数据）：")
    for key, value in result.response_metadata.items():
        print(f"      {key}: {value}")
    print()


# ============================================================
# 2. ChatAnthropic 实例化与调用
# ============================================================
def demo_chat_anthropic():
    """ChatAnthropic 实例化与调用"""
    print("=" * 60)
    print("【2】ChatAnthropic 实例化与调用")
    print("=" * 60)

    if not check_api_key("ANTHROPIC_API_KEY"):
        return

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import SystemMessage, HumanMessage
    except ImportError:
        print("⚠️  未安装 langchain-anthropic，跳过。可运行：pip install langchain-anthropic\n")
        return

    # 实例化 ChatAnthropic
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=500,
        timeout=30,
    )

    print(f"模型类型：{type(model).__name__}")
    print(f"模型名称：{getattr(model, 'model', 'N/A')}")

    messages = [
        SystemMessage(content="你是一个简洁的技术助手，回答不超过 50 字。"),
        HumanMessage(content="什么是 LangChain 的 LCEL？"),
    ]

    result = model.invoke(messages)

    print(f"  content（正文）：{result.content}")
    print(f"  usage_metadata：{result.usage_metadata}")
    print(f"  response_metadata.model：{result.response_metadata.get('model', 'N/A')}")
    print()


# ============================================================
# 3. ChatOllama 实例化（本地模型，无需 API Key）
# ============================================================
def demo_chat_ollama():
    """ChatOllama 实例化与调用（本地模型）"""
    print("=" * 60)
    print("【3】ChatOllama 实例化（本地模型）")
    print("=" * 60)

    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError:
        print("⚠️  未安装 langchain-community，跳过。\n")
        return

    # ChatOllama 不需要 API Key，但需要本地 Ollama 服务
    model = ChatOllama(
        model="qwen2.5:7b",                            # 本地模型名
        base_url="http://localhost:11434/v1",        # Ollama 服务地址
        temperature=0.7,
    )

    print(f"模型类型：{type(model).__name__}")
    print(f"模型名称：{model.model}")
    print(f"服务地址：{model.base_url}")
    print("（需要本地已启动 ollama serve 并拉取模型）\n")

    # 尝试调用（可能因 Ollama 未启动而失败）
    try:
        from langchain_core.messages import HumanMessage
        result = model.invoke([HumanMessage(content="你好")])
        print(f"  content：{result.content}\n")
    except Exception as e:
        print(f"  ⚠️  本地调用失败（{e}）")
        print("  请确保已运行：ollama serve && ollama pull qwen2.5:7b\n")


# ============================================================
# 4. 多模型统一接口对比
# ============================================================
def demo_unified_interface():
    """多模型统一接口对比"""
    print("=" * 60)
    print("【4】多模型统一接口对比")
    print("=" * 60)

    models = {}

    # 收集可用模型
    if check_api_key("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        models["ChatOpenAI"] = ChatOpenAI(model="gpt-4o-mini", max_tokens=100)

    if check_api_key("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            models["ChatAnthropic"] = ChatAnthropic(
                model="claude-3-5-sonnet-20241022", max_tokens=100
            )
        except ImportError:
            pass

    if not models:
        print("  无可用模型，请至少配置一个 API Key\n")
        return

    from langchain_core.messages import HumanMessage

    # 同一个 Prompt，调用不同模型
    prompt = "用一句话解释什么是递归。"

    for name, model in models.items():
        try:
            result = model.invoke([HumanMessage(content=prompt)])
            print(f"  {name}：")
            print(f"    回复：{result.content}")
            print(f"    Token：{result.usage_metadata}\n")
        except Exception as e:
            print(f"  {name} 调用失败：{e}\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day02 - ChatModel 实例化与调用\n")

    # 1. ChatOpenAI
    demo_chat_openai()

    # 2. ChatAnthropic
    demo_chat_anthropic()

    # 3. ChatOllama（本地）
    demo_chat_ollama()

    # 4. 多模型统一接口
    demo_unified_interface()

    print("=" * 60)
    print("✅ ChatModel 演示完成")
    print("关键点：")
    print("  - 所有 ChatModel 继承 BaseChatModel，接口统一")
    print("  - invoke 返回 AIMessage，含 content/usage_metadata/response_metadata")
    print("  - 不同模型实例化参数略有差异，但调用方式完全一致")
    print("=" * 60)
