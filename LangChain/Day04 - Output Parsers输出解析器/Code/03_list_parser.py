# 文件用途：列表与枚举解析
# CommaSeparatedListOutputParser 解析为列表
# EnumOutputParser 限制输出选项
# DatetimeOutputParser 解析日期
# 场景：情感分类枚举 / 关键词列表提取

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. CommaSeparatedListOutputParser
# ============================================================
def demo_list_parser():
    """逗号分隔列表解析器"""
    print("=" * 60)
    print("【1】CommaSeparatedListOutputParser")
    print("=" * 60)

    from langchain_core.output_parsers import CommaSeparatedListOutputParser

    parser = CommaSeparatedListOutputParser()

    # 查看格式指令
    print(f"  格式指令：{parser.get_format_instructions()}\n")

    # 解析逗号分隔文本
    text1 = "苹果, 香蕉, 橙子, 葡萄"
    result1 = parser.parse(text1)
    print(f"  输入：{text1}")
    print(f"  输出类型：{type(result1).__name__}")
    print(f"  输出值：{result1}\n")

    # 中文逗号也能处理
    text2 = "Python，Java，Go，Rust"
    result2 = parser.parse(text2)
    print(f"  输入（中文逗号）：{text2}")
    print(f"  输出值：{result2}\n")


# ============================================================
# 2. CommaSeparatedListOutputParser 在 Chain 中
# ============================================================
def demo_list_parser_in_chain():
    """列表解析器在 Chain 中使用"""
    print("=" * 60)
    print("【2】列表解析器在 Chain 中")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import CommaSeparatedListOutputParser

    parser = CommaSeparatedListOutputParser()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是关键词提取助手。"),
        ("human", "提取以下文本的关键词：\n{text}\n\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model | parser

    text = "LangChain 是一个用于构建 LLM 应用的开源框架，支持 Prompt 管理、输出解析、链式调用等功能。"
    result = chain.invoke({"text": text})

    print(f"  输入：{text}")
    print(f"  关键词列表：{result}")
    print(f"  数量：{len(result)} 个\n")


# ============================================================
# 3. EnumOutputParser 枚举解析
# ============================================================
def demo_enum_parser():
    """枚举解析器"""
    print("=" * 60)
    print("【3】EnumOutputParser")
    print("=" * 60)

    from langchain_core.output_parsers import EnumOutputParser
    from enum import Enum

    # 定义枚举
    class Sentiment(str, Enum):
        POSITIVE = "positive"
        NEGATIVE = "negative"
        NEUTRAL = "neutral"

    parser = EnumOutputParser(enum=Sentiment)

    print(f"  格式指令：{parser.get_format_instructions()}\n")

    # 解析
    result = parser.parse("positive")
    print(f"  输入：'positive'")
    print(f"  输出类型：{type(result).__name__}")
    print(f"  输出值：{result}")
    print(f"  等于 Sentiment.POSITIVE：{result == Sentiment.POSITIVE}\n")


# ============================================================
# 4. EnumOutputParser 在 Chain 中（情感分类）
# ============================================================
def demo_enum_parser_in_chain():
    """枚举解析器在 Chain 中（情感分类）"""
    print("=" * 60)
    print("【4】情感分类 Chain")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import EnumOutputParser
    from enum import Enum

    class Sentiment(str, Enum):
        POSITIVE = "正面"
        NEGATIVE = "负面"
        NEUTRAL = "中性"

    parser = EnumOutputParser(enum=Sentiment)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是情感分析助手，只输出情感分类结果。"),
        ("human", "分析情感：{text}\n\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model | parser

    texts = [
        "这家餐厅的菜太好吃了，服务也很棒！",
        "质量太差了，再也不来了。",
        "还行吧，一般般。",
    ]

    for text in texts:
        result = chain.invoke({"text": text})
        print(f"  文本：{text}")
        print(f"  情感：{result.value}\n")


# ============================================================
# 5. DatetimeOutputParser
# ============================================================
def demo_datetime_parser():
    """日期解析器"""
    print("=" * 60)
    print("【5】DatetimeOutputParser")
    print("=" * 60)

    from langchain_core.output_parsers import DatetimeOutputParser

    parser = DatetimeOutputParser()

    print(f"  格式指令：{parser.get_format_instructions()[:200]}...\n")

    # 解析 ISO 8601 日期
    date_str = "2024-01-15T10:30:00"
    result = parser.parse(date_str)
    print(f"  输入：{date_str}")
    print(f"  输出类型：{type(result).__name__}")
    print(f"  输出值：{result}")
    print(f"  年：{result.year}，月：{result.month}，日：{result.day}\n")


# ============================================================
# 6. 各种 Parser 的格式指令对比
# ============================================================
def demo_format_instructions_comparison():
    """各种 Parser 的 get_format_instructions 对比"""
    print("=" * 60)
    print("【6】格式指令对比")
    print("=" * 60)

    from langchain_core.output_parsers import (
        StrOutputParser,
        JsonOutputParser,
        CommaSeparatedListOutputParser,
        EnumOutputParser,
        DatetimeOutputParser,
        PydanticOutputParser,
    )
    from pydantic import BaseModel, Field
    from enum import Enum

    class TestEnum(str, Enum):
        A = "a"
        B = "b"

    class TestModel(BaseModel):
        name: str = Field(description="名称")

    parsers = {
        "StrOutputParser": StrOutputParser(),
        "JsonOutputParser": JsonOutputParser(),
        "CommaSeparatedListOutputParser": CommaSeparatedListOutputParser(),
        "EnumOutputParser": EnumOutputParser(enum=TestEnum),
        "DatetimeOutputParser": DatetimeOutputParser(),
        "PydanticOutputParser": PydanticOutputParser(pydantic_object=TestModel),
    }

    for name, parser in parsers.items():
        instructions = parser.get_format_instructions()
        # 截取前 80 字符
        short = instructions[:80].replace("\n", " ") + "..."
        print(f"  {name}:")
        print(f"    {short}\n")


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day04 - 列表与枚举解析\n")

    demo_list_parser()
    demo_list_parser_in_chain()
    demo_enum_parser()
    demo_enum_parser_in_chain()
    demo_datetime_parser()
    demo_format_instructions_comparison()

    print("=" * 60)
    print("✅ 列表与枚举解析演示完成")
    print("总结：")
    print("  - CommaSeparatedListOutputParser：逗号分隔 → 列表")
    print("  - EnumOutputParser：限制输出为枚举值之一")
    print("  - DatetimeOutputParser：解析日期时间")
    print("  - 每种 Parser 都有 get_format_instructions() 指导 LLM 输出")
    print("=" * 60)
