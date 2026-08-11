# 文件用途：第一个 LangChain 程序
# 用 ChatOpenAI 调用 GPT-4o-mini 进行简单对话，展示 invoke/stream 两种方式，并与直接调用 openai SDK 对比
# 运行前请确保已安装：pip install langchain langchain-openai python-dotenv openai
# 并在 .env 中配置 OPENAI_API_KEY

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量（API Key 等）
load_dotenv()


def check_api_key():
    """检查 OpenAI API Key 是否已配置"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("=" * 60)
        print("错误：未检测到 OPENAI_API_KEY")
        print("请在项目根目录创建 .env 文件，添加：")
        print("OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx")
        print("=" * 60)
        sys.exit(1)
    print(f"已检测到 OPENAI_API_KEY（前 8 位：{api_key[:8]}...）\n")


# ============================================================
# 方式一：直接调用 OpenAI SDK（原生方式，作为对比参考）
# ============================================================
def call_with_openai_sdk():
    """使用原生 OpenAI SDK 调用 GPT-4o-mini"""
    print("=" * 60)
    print("方式一：直接调用 OpenAI SDK")
    print("=" * 60)

    from openai import OpenAI

    client = OpenAI()  # 自动读取环境变量 OPENAI_API_KEY
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一个简洁的助手，回答尽量精炼。"},
            {"role": "user", "content": "用一句话解释什么是 LangChain。"},
        ],
        temperature=0.7,
    )

    print(f"回复：{response.choices[0].message.content}")
    print(f"Token 用量：{response.usage.total_tokens}\n")


# ============================================================
# 方式二：使用 LangChain（invoke 单次调用）
# ============================================================
def call_with_langchain_invoke():
    """使用 LangChain ChatOpenAI 的 invoke 方法"""
    print("=" * 60)
    print("方式二：LangChain invoke 调用")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    # 实例化 ChatModel
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500,
    )

    # 构造消息列表（角色体系）
    messages = [
        SystemMessage(content="你是一个简洁的助手，回答尽量精炼。"),
        HumanMessage(content="用一句话解释什么是 LangChain。"),
    ]

    # invoke 单次调用，返回 AIMessage 对象
    result = model.invoke(messages)

    # AIMessage 包含丰富的结构化信息
    print(f"content（回复正文）：{result.content}")
    print(f"type（消息类型）：{result.type}")
    print(f"response_metadata（模型元数据）：{result.response_metadata}")
    print(f"usage_metadata（Token 用量）：{result.usage_metadata}")
    print(f"id（消息 ID）：{result.id}\n")


# ============================================================
# 方式三：使用 LangChain（stream 流式输出）
# ============================================================
def call_with_langchain_stream():
    """使用 LangChain ChatOpenAI 的 stream 方法流式输出"""
    print("=" * 60)
    print("方式三：LangChain stream 流式输出")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    # 开启流式输出
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        streaming=True,
    )

    messages = [
        SystemMessage(content="你是一个简洁的助手。"),
        HumanMessage(content="用三句话介绍 LangChain 的核心组件。"),
    ]

    print("流式输出中（逐字显示）：\n")
    full_content = ""
    # stream 返回 AIMessageChunk 迭代器，每个 chunk 包含一小段文本
    for chunk in model.stream(messages):
        # 每个 chunk 是 AIMessageChunk，content 属性是当前分片文本
        print(chunk.content, end="", flush=True)
        full_content += chunk.content

    print(f"\n\n[拼接完成，总字符数：{len(full_content)}]\n")


# ============================================================
# 方式四：使用 LCEL 管道（预览 Day05 内容）
# ============================================================
def call_with_lcel_chain():
    """使用 LCEL 管道符组合 prompt | model | parser"""
    print("=" * 60)
    print("方式四：LCEL 管道（预览 Day05 内容）")
    print("=" * 60)

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser

    # 1. 定义 Prompt 模板
    prompt = ChatPromptTemplate.from_template(
        "你是一个简洁的助手，请用一句话回答：{question}"
    )
    # 2. 实例化模型
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    # 3. 字符串输出解析器
    parser = StrOutputParser()

    # 4. 用管道符 | 组合成链（LCEL 核心语法）
    chain = prompt | model | parser

    # 5. invoke 调用，输入是包含 question 变量的字典
    answer = chain.invoke({"question": "什么是 LangChain 的 LCEL？"})
    print(f"链式调用结果：{answer}\n")
    print("（LCEL 详解见 Day05 - Chains 链式调用与 LCEL）\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 第一个 LangChain 程序\n")

    # 检查 API Key
    check_api_key()

    # 方式一：直接调用 OpenAI SDK（对比基准）
    try:
        call_with_openai_sdk()
    except ImportError:
        print("（未安装 openai 包，跳过方式一。可运行：pip install openai）\n")
    except Exception as e:
        print(f"（方式一运行失败：{e}）\n")

    # 方式二：LangChain invoke
    call_with_langchain_invoke()

    # 方式三：LangChain stream
    call_with_langchain_stream()

    # 方式四：LCEL 管道预览
    call_with_lcel_chain()

    print("=" * 60)
    print("✅ 第一个 LangChain 程序运行完成")
    print("对比总结：")
    print("  - 直接调用 OpenAI SDK：灵活但需手动管理 Prompt/解析/记忆")
    print("  - LangChain invoke：结构化输出，含 usage_metadata 等元数据")
    print("  - LangChain stream：流式输出，提升用户体验")
    print("  - LCEL 管道：组件化组合，prompt | model | parser 一行成链")
    print("=" * 60)
