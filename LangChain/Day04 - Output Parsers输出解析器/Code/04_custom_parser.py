# 文件用途：自定义解析器与错误重试
# 继承 BaseOutputParser 实现自定义解析器
# parse() 方法实现 / 解析错误处理
# RetryOutputParser 自动重试 / parse_with_prompt() 重试机制
# 场景：自定义 Markdown 表格解析器 + 解析失败自动重试

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 1. 自定义 Output Parser 基础
# ============================================================
def demo_base_output_parser():
    """BaseOutputParser 基类介绍"""
    print("=" * 60)
    print("【1】BaseOutputParser 基类介绍")
    print("=" * 60)

    from langchain_core.output_parsers import BaseOutputParser

    print("  BaseOutputParser 核心方法：")
    print("    - parse(text: str) → Any        解析文本")
    print("    - parse_with_prompt(text, prompt) 重试时用")
    print("    - get_format_instructions() → str 格式指令")
    print("    - _type 属性                     类型标识\n")

    # 最简单的自定义 parser
    class LengthParser(BaseOutputParser):
        """统计输出文本长度"""

        def parse(self, text: str) -> int:
            return len(text.strip())

        @property
        def _type(self) -> str:
            return "length_parser"

    parser = LengthParser()
    result = parser.invoke("Hello World")
    print(f"  LengthParser 示例：")
    print(f"    输入：'Hello World'")
    print(f"    输出：{result}（长度）")
    print(f"    类型：{parser._type}\n")


# ============================================================
# 2. 自定义 Markdown 表格解析器
# ============================================================
def demo_markdown_table_parser():
    """自定义 Markdown 表格解析器"""
    print("=" * 60)
    print("【2】自定义 Markdown 表格解析器")
    print("=" * 60)

    from langchain_core.output_parsers import BaseOutputParser
    from langchain_core.exceptions import OutputParserException

    class MarkdownTableParser(BaseOutputParser):
        """将 Markdown 表格解析为二维列表（行 × 列）"""

        def parse(self, text: str) -> list[list[str]]:
            """解析 Markdown 表格"""
            lines = text.strip().split("\n")
            rows = []

            for line in lines:
                line = line.strip()
                if not line or not line.startswith("|"):
                    continue
                # 跳过分隔行（|---|---|）
                if set(line.replace("|", "").replace(" ", "" + "-" + "")) <= set("-"):
                    continue
                # 按竖线分割
                cells = [c.strip() for c in line.strip("|").split("|")]
                rows.append(cells)

            if not rows:
                raise OutputParserException(
                    f"未找到有效的 Markdown 表格。输入：{text[:50]}..."
                )
            return rows

        @property
        def _type(self) -> str:
            return "markdown_table_parser"

    # 测试解析
    markdown_table = """
    | 姓名 | 年龄 | 城市 |
    |------|------|------|
    | 张三 | 28   | 北京 |
    | 李四 | 32   | 上海 |
    """

    parser = MarkdownTableParser()
    result = parser.parse(markdown_table)

    print(f"  输入 Markdown 表格：")
    print(f"  {markdown_table}")
    print(f"  解析结果（二维列表）：")
    for row in result:
        print(f"    {row}")
    print()


# ============================================================
# 3. 解析错误处理
# ============================================================
def demo_error_handling():
    """解析错误处理"""
    print("=" * 60)
    print("【3】解析错误处理")
    print("=" * 60)

    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.exceptions import OutputParserException
    from pydantic import BaseModel, Field

    class PersonInfo(BaseModel):
        name: str = Field(description="姓名")
        age: int = Field(description="年龄")

    parser = PydanticOutputParser(pydantic_object=PersonInfo)

    # 故意解析错误的 JSON
    bad_outputs = [
        "这不是 JSON 格式",
        "{name: 张三, age: 28}",       # 缺少引号
        '{"name": "张三"}',            # 缺少 age
    ]

    for bad in bad_outputs:
        print(f"  输入：{bad[:40]}")
        try:
            result = parser.parse(bad)
            print(f"  结果：{result}")
        except OutputParserException as e:
            print(f"  ❌ 解析失败：{str(e)[:80]}...")
        except Exception as e:
            print(f"  ❌ 其他错误：{type(e).__name__}")
        print()


# ============================================================
# 4. 自定义解析器在 Chain 中
# ============================================================
def demo_custom_parser_in_chain():
    """自定义解析器在 Chain 中使用"""
    print("=" * 60)
    print("【4】自定义解析器在 Chain 中")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.output_parsers import BaseOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    class KeywordListParser(BaseOutputParser):
        """将每行一个关键词的文本解析为列表"""

        def parse(self, text: str) -> list[str]:
            lines = text.strip().split("\n")
            keywords = []
            for line in lines:
                line = line.strip().strip("- ").strip()
                if line:
                    keywords.append(line)
            return keywords

        @property
        def _type(self) -> str:
            return "keyword_list_parser"

    parser = KeywordListParser()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是关键词提取助手，每行输出一个关键词，不要编号。"),
        ("human", "提取以下文本的关键词（5个）：\n{text}"),
    ])

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model | parser

    text = "LangChain 提供模块化组件构建 LLM 应用，包括模型调用、Prompt 管理、输出解析等。"
    result = chain.invoke({"text": text})

    print(f"  输入：{text}")
    print(f"  关键词：{result}\n")


# ============================================================
# 5. RetryOutputParser 自动重试
# ============================================================
def demo_retry_parser():
    """RetryOutputParser 自动重试机制"""
    print("=" * 60)
    print("【5】RetryOutputParser 自动重试")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  未配置 OPENAI_API_KEY，跳过\n")
        return

    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.exceptions import OutputParserException
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    class ProductInfo(BaseModel):
        name: str = Field(description="产品名")
        price: float = Field(description="价格")

    parser = PydanticOutputParser(pydantic_object=ProductInfo)

    # 创建 Prompt
    prompt = ChatPromptTemplate.from_template(
        "提取产品信息：{text}\n\n{format_instructions}"
    ).partial(format_instructions=parser.get_format_instructions())

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建 RetryOutputParser
    try:
        from langchain.output_parsers import RetryOutputParser
        retry_parser = RetryOutputParser.from_llm(parser=parser, llm=model)
    except ImportError:
        print("  ⚠️  无法导入 RetryOutputParser，使用 langchain_core 替代方案\n")
        # 替代方案：手动重试
        print("  手动重试示例：")
        bad_output = "产品是 iPhone，价格未知"

        try:
            parser.parse(bad_output)
        except OutputParserException as e:
            print(f"  第一次解析失败：{str(e)[:60]}...")
            # 手动在 Prompt 中追加错误信息重试
            retry_prompt = f"""
            之前的输出格式有误：{bad_output}
            错误：{str(e)[:100]}
            请重新输出正确的 JSON 格式。
            """
            print(f"  追加错误信息重试...\n")
        return

    # 模拟解析失败的场景
    bad_output = "产品是 iPhone，价格 5999 元"  # 不是 JSON

    print("  模拟解析失败场景：")
    print(f"  LLM 输出：{bad_output}")

    try:
        result = parser.parse(bad_output)
        print(f"  直接解析成功：{result}")
    except OutputParserException as e:
        print(f"  直接解析失败：{str(e)[:60]}...")

        # 使用 parse_with_prompt 重试
        print("\n  使用 RetryOutputParser 重试...")
        prompt_value = prompt.invoke({"text": "iPhone 价格 5999"})
        try:
            result = retry_parser.parse_with_prompt(bad_output, prompt_value)
            print(f"  ✅ 重试成功：{result}")
        except Exception as e:
            print(f"  重试也失败：{str(e)[:60]}...")
    print()


# ============================================================
# 6. 完整的错误重试 Chain
# ============================================================
def demo_retry_chain():
    """带错误重试的完整 Chain"""
    print("=" * 60)
    print("【6】带错误处理的 Chain 模式")
    print("=" * 60)

    print("  推荐的错误处理模式：")
    print("""
    1. 基本 Chain：prompt | model | parser
       - 简单场景，LLM 输出质量高

    2. try-except 降级：直接捕获解析错误
       try:
           result = chain.invoke(input)
       except OutputParserException:
           result = fallback_value  # 降级处理

    3. RetryOutputParser：自动重试
       - 解析失败 → 追加错误信息 → 重新调用 LLM

    4. with_fallbacks：模型级回退
       - 主模型失败 → 切换备用模型
    """)
    print()


# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    print("🚀 Day04 - 自定义解析器与错误重试\n")

    demo_base_output_parser()
    demo_markdown_table_parser()
    demo_error_handling()
    demo_custom_parser_in_chain()
    demo_retry_parser()
    demo_retry_chain()

    print("=" * 60)
    print("✅ 自定义解析器与错误重试演示完成")
    print("总结：")
    print("  - 继承 BaseOutputParser 实现 parse() 方法")
    print("  - OutputParserException 处理解析错误")
    print("  - RetryOutputParser 解析失败自动重试")
    print("  - parse_with_prompt 传入原始 Prompt 用于重试")
    print("=" * 60)
