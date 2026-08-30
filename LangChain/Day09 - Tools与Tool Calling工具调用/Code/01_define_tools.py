# 文件用途：演示 LangChain 三种 Tool 定义方式（@tool 装饰器 / Tool 类 / StructuredTool）
# 以及使用 Pydantic 模型定义参数 Schema。场景：天气查询 / 计算器 / 文本搜索
# 运行：python 01_define_tools.py
# 依赖：pip install langchain langchain-openai python-dotenv pydantic

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# LangChain 0.3+ 工具相关导入
from langchain_core.tools import StructuredTool, tool
from langchain.tools import Tool

load_dotenv()


# ============================================================
# 方式一：@tool 装饰器（最简洁，推荐）
# ============================================================

@tool
def search_weather(city: str) -> str:
    """查询指定城市的实时天气情况。当用户询问某地天气时使用本工具。

    参数:
        city: 要查询的城市中文名，例如 "北京"、"上海"
    """
    # 模拟天气数据（真实场景调用天气 API）
    weather_db = {
        "北京": "晴，气温 25°C，湿度 40%",
        "上海": "多云，气温 28°C，湿度 65%",
        "广州": "雷阵雨，气温 31°C，湿度 80%",
    }
    return weather_db.get(city, f"暂无 {city} 的天气数据")


@tool
def simple_calculator(expression: str) -> str:
    """计算数学表达式的值。当用户需要做数学计算时使用本工具。

    参数:
        expression: 数学表达式字符串，例如 "1+2*3"、"(10+5)/3"
    """
    try:
        # 注意：生产环境请用 ast.literal_eval 或 sympy 替代 eval
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算失败：{e}"


# ============================================================
# 方式一进阶：@tool + Pydantic 参数 Schema（复杂参数）
# ============================================================

class TextSearchInput(BaseModel):
    """文本搜索工具的参数 Schema"""
    query: str = Field(description="要搜索的关键词")
    top_k: int = Field(default=3, description="返回结果数量，默认 3")
    mode: Literal["exact", "fuzzy"] = Field(
        default="fuzzy", description="搜索模式：exact 精确匹配 / fuzzy 模糊匹配"
    )


@tool(args_schema=TextSearchInput)
def search_text(query: str, top_k: int = 3, mode: str = "fuzzy") -> str:
    """在本地文档库中搜索包含指定关键词的文本。

    当用户需要在文档中查找信息时使用本工具。支持精确匹配和模糊匹配两种模式。
    """
    docs = [
        "LangChain 是一个 LLM 应用开发框架",
        "LCEL 是 LangChain 的表达式语言",
        "Tool Calling 让 LLM 能调用外部函数",
        "Retriever 用于检索相关文档",
        "Memory 管理多轮对话历史",
    ]
    if mode == "exact":
        results = [d for d in docs if query in d][:top_k]
    else:
        results = [d for d in docs if any(w in d for w in query.split())][:top_k]
    return f"找到 {len(results)} 条结果：\n" + "\n".join(f"- {r}" for r in results)


# ============================================================
# 方式二：Tool 类（传统方式，快速包装现成函数）
# ============================================================

def _word_count(text: str) -> str:
    """统计文本字数（现成函数）"""
    count = len(text)
    return f"文本字数：{count} 个字符"


word_count_tool = Tool(
    name="word_counter",
    func=_word_count,
    description="统计输入文本的字符数量。当用户想知道一段文字有多长时使用。",
)


# ============================================================
# 方式三：StructuredTool（结构化工具，显式 Schema）
# ============================================================

class CalculatorInput(BaseModel):
    """计算器参数 Schema，显式定义在 StructuredTool 中复用"""
    expression: str = Field(description="要计算的数学表达式，例如 '2*(3+4)'")
    precision: int = Field(default=2, description="结果保留小数位数，默认 2")


def _advanced_calc(expression: str, precision: int = 2) -> str:
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果：{result:.{precision}f}"
    except Exception as e:
        return f"计算失败：{e}"


advanced_calc_tool = StructuredTool.from_function(
    func=_advanced_calc,
    name="advanced_calculator",
    description="高级计算器，支持指定小数精度。当需要精确控制计算结果精度时使用。",
    args_schema=CalculatorInput,
)


# ============================================================
# 演示：查看工具的 Schema 信息
# ============================================================

def show_tool_info(tool_obj, title: str) -> None:
    """打印工具的关键信息，帮助理解工具结构"""
    print(f"\n{'=' * 60}")
    print(f"工具名称：{title}")
    print(f"-' * 40")
    print(f"name        : {tool_obj.name}")
    print(f"description : {tool_obj.description}")
    print(f"args_schema : {tool_obj.args_schema.model_json_schema() if tool_obj.args_schema else 'None'}")
    print(f"{'=' * 60}")


def demo_invoke_tools() -> None:
    """直接调用工具（不经过 LLM），验证工具本身可用"""
    print("\n" + "🔧 " + "工具直接调用演示" + " 🔧".center(50, "="))

    # 1. @tool 装饰器工具
    print("\n[1] @tool 装饰器 - search_weather:")
    print("    输入: city='北京'")
    print(f"    输出: {search_weather.invoke({'city': '北京'})}")

    # 2. @tool + Pydantic Schema
    print("\n[2] @tool + Pydantic - search_text:")
    print("    输入: query='LangChain 工具', top_k=2")
    print(f"    输出: {search_text.invoke({'query': 'LangChain 工具', 'top_k': 2})}")

    # 3. Tool 类
    print("\n[3] Tool 类 - word_counter:")
    print(f"    输入: 'Hello LangChain'")
    print(f"    输出: {word_count_tool.invoke('Hello LangChain')}")

    # 4. StructuredTool
    print("\n[4] StructuredTool - advanced_calculator:")
    print("    输入: expression='10/3', precision=4")
    print(f"    输出: {advanced_calc_tool.invoke({'expression': '10/3', 'precision': 4})}")


def main() -> None:
    print("=" * 60)
    print("Day09 - 01 Tool 定义方式对比演示")
    print("场景：天气查询 / 计算器 / 文本搜索")
    print("=" * 60)

    # 展示三种工具的 Schema 信息
    show_tool_info(search_weather, "@tool 装饰器（基础）")
    show_tool_info(search_text, "@tool + Pydantic Schema")
    show_tool_info(word_count_tool, "Tool 类（传统）")
    show_tool_info(advanced_calc_tool, "StructuredTool（结构化）")

    # 直接调用工具验证
    demo_invoke_tools()

    print("\n" + "=" * 60)
    print("✅ 三种 Tool 定义方式演示完成")
    print("对比要点：")
    print("  - @tool 装饰器：最简洁，自动从 docstring + 类型注解生成 Schema")
    print("  - Tool 类：适合快速包装现成函数，但参数 Schema 较粗")
    print("  - StructuredTool：显式指定 args_schema，参数控制最精细")
    print("=" * 60)


if __name__ == "__main__":
    # 检查 API Key 是否配置（本文件不需要调用模型，但保持一致性）
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  提示：未检测到 OPENAI_API_KEY，本文件直接调用工具不依赖模型，可正常运行。")

    main()
