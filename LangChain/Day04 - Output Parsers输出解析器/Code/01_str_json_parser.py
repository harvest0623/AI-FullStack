# 文件用途：字符串与 JSON 解析
# 演示 StrOutputParser 基础使用 / JsonOutputParser 解析+Schema约束
# get_format_instructions() 注入 Prompt / 解析结果为 dict
# 场景：客服意图识别输出 JSON

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. StrOutputParser 基础
# ============================================================
def demo_str_parser():
    """StrOutputParser 基础使用"""
    print("=" * 60)
    print("【1】StrOutputParser 基础")
    print("=" * 60)

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.messages import AIMessage

    parser = StrOutputParser()

    # StrOutputParser 从 AIMessage 提取 content 字符串
    msg = AIMessage(content="你好，我是 ChainQA 助手")
    result = parser.invoke(msg)
    print(f"  输入：AIMessage(content='你好，我是 ChainQA 助手')")
    print(f"  输出类型：{type(result).__name__}")
    print(f"  输出值：{result}\n")

    # 也支持直接传入字符串
    result2 = parser.invoke("直接传字符串")
    print(f"  直接传字符串：{result2}\n")


# ============================================================
# 2. StrOutputParser 在 Chain 中使用
# ============================================================
def demo_str_parser_in_chain():
    """StrOutputParser 在 LCEL 链中使用"""
    print("=" * 60)
    print("【2】StrOutputParser 在 Chain 中使用")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser

    prompt = ChatPromptTemplate.from_template("用一句话解释 {topic}")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = StrOutputParser()

    # 没有 parser 时，输出是 AIMessage
    # 有 parser 时，输出是字符串
    chain = prompt | model | parser

    result = chain.invoke({"topic": "LangChain"})
    print(f"  输出类型：{type(result).__name__}（字符串，非 AIMessage）")
    print(f"  输出值：{result}\n")


# ============================================================
# 3. JsonOutputParser 基础
# ============================================================
def demo_json_parser_basic():
    """JsonOutputParser 基础使用"""
    print("=" * 60)
    print("【3】JsonOutputParser 基础")
    print("=" * 60)

    from langchain_core.output_parsers import JsonOutputParser

    parser = JsonOutputParser()

    # 查看格式指令
    print("  格式指令（get_format_instructions）：")
    print(f"  {parser.get_format_instructions()[:200]}...\n")

    # 解析 JSON 字符串
    json_text = '{"name": "张三", "age": 28, "city": "北京"}'
    result = parser.parse(json_text)
    print(f"  输入：{json_text}")
    print(f"  输出类型：{type(result).__name__}")
    print(f"  输出值：{result}")
    print(f"  name：{result['name']}, age：{result['age']}\n")


# ============================================================
# 4. JsonOutputParser + Pydantic Schema 约束
# ============================================================
def demo_json_parser_with_schema():
    """JsonOutputParser + Pydantic Schema 约束"""
    print("=" * 60)
    print("【4】JsonOutputParser + Schema 约束")
    print("=" * 60)

    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field

    # 定义 Schema
    class CustomerIntent(BaseModel):
        """客服意图识别结果"""
        intent: str = Field(description="用户意图，如：退款/咨询/投诉/建议")
        confidence: float = Field(description="置信度，0-1 之间")
        keywords: list = Field(description="关键词列表")

    # 创建带 Schema 的 parser
    parser = JsonOutputParser(pydantic_object=CustomerIntent)

    print("  Schema 约束的格式指令：")
    print(f"  {parser.get_format_instructions()[:300]}...\n")

    # 解析带 Schema 的输出
    json_text = """
    {
        "intent": "退款",
        "confidence": 0.95,
        "keywords": ["退款", "商品", "质量"]
    }
    """
    result = parser.parse(json_text)
    print(f"  解析结果：{result}")
    print(f"  intent：{result['intent']}")
    print(f"  confidence：{result['confidence']}\n")


# ============================================================
# 5. 完整 Chain：客服意图识别
# ============================================================
def demo_intent_recognition_chain():
    """完整 Chain：客服意图识别（输出 JSON）"""
    print("=" * 60)
    print("【5】完整 Chain：客服意图识别")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field

    # 1. 定义输出 Schema
    class IntentResult(BaseModel):
        """意图识别结果"""
        intent: str = Field(description="意图类别：退款/咨询/投诉/建议/其他")
        confidence: float = Field(description="置信度 0-1")
        response: str = Field(description="建议的客服回复")

    # 2. 创建 Parser
    parser = JsonOutputParser(pydantic_object=IntentResult)

    # 3. 创建 Prompt，注入格式指令
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是客服意图识别系统，分析用户消息并返回 JSON。"),
        ("human", "用户消息：{message}\n\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    # 4. 组成 Chain
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model | parser

    # 5. 测试不同用户消息
    messages = [
        "我买的商品有质量问题，要求退款！",
        "请问你们的工作时间是什么时候？",
        "你们的服务太差了，我要投诉！",
    ]

    for msg in messages:
        result = chain.invoke({"message": msg})
        print(f"  用户：{msg}")
        print(f"  意图：{result['intent']}（置信度：{result['confidence']}）")
        print(f"  回复：{result['response'][:50]}...")
        print()


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day04 - 字符串与 JSON 解析\n")

    demo_str_parser()
    demo_str_parser_in_chain()
    demo_json_parser_basic()
    demo_json_parser_with_schema()
    demo_intent_recognition_chain()

    print("=" * 60)
    print("✅ 字符串与 JSON 解析演示完成")
    print("总结：")
    print("  - StrOutputParser：最简单，提取 content 字符串")
    print("  - JsonOutputParser：解析 JSON，可加 Schema 约束")
    print("  - get_format_instructions() 注入 Prompt 指导输出格式")
    print("  - prompt | model | parser 是标准 Chain 模式")
    print("=" * 60)
