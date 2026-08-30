# 文件用途：演示 LangChain 内置工具集（DuckDuckGo 搜索 / Wikipedia / 计算器）
# 并封装 BuiltinToolkit 类统一管理常用内置工具
# 运行：python 03_builtin_tools.py
# 依赖：pip install langchain langchain-community langchain-openai python-dotenv
#       pip install duckduckgo-search wikipedia
# 可选依赖（搜索类）：pip install wikipedia

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 内置工具1：DuckDuckGo 搜索（免费，无需 Key）
# ============================================================

def get_ddg_search_tool():
    """创建 DuckDuckGo 搜索工具。需要安装 duckduckgo-search 包。"""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        return DuckDuckGoSearchRun()
    except ImportError:
        print("⚠️  未安装 duckduckgo-search，跳过该工具。安装：pip install duckduckgo-search")
        return None


# ============================================================
# 内置工具2：Wikipedia 查询
# ============================================================

def get_wikipedia_tool():
    """创建 Wikipedia 查询工具。需要安装 wikipedia 包。"""
    try:
        from langchain_community.utilities import WikipediaAPIWrapper
        from langchain_community.tools import WikipediaQueryRun
        # top_k_results 限制返回条数，避免输出过长
        api_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1000)
        return WikipediaQueryRun(api_wrapper=api_wrapper)
    except ImportError:
        print("⚠️  未安装 wikipedia，跳过该工具。安装：pip install wikipedia")
        return None


# ============================================================
# 内置工具3：计算器（基于 llm_math 的现代替代——直接用 Python 实现）
# ============================================================

from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除、括号、幂运算等。

    参数:
        expression: 数学表达式，例如 "2*(3+4)"、"5**2"
    """
    try:
        # 限制可用内建，避免安全风险
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败：{e}。请检查表达式语法。"


# ============================================================
# BuiltinToolkit：封装常用内置工具
# ============================================================

class BuiltinToolkit:
    """统一管理常用内置工具的工具箱类。

    提供：
    - 工具注册与获取
    - 统一的工具列表（用于 bind_tools）
    - 工具名 → 工具对象的映射
    """

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """注册内置工具（已安装依赖的才会注册成功）"""
        # 计算器（本地实现，无外部依赖）
        self.register("calculator", calculator)

        # DuckDuckGo 搜索
        ddg = get_ddg_search_tool()
        if ddg is not None:
            self.register("ddg_search", ddg)

        # Wikipedia
        wiki = get_wikipedia_tool()
        if wiki is not None:
            self.register("wikipedia", wiki)

    def register(self, name: str, tool_obj: Any) -> None:
        """注册一个工具"""
        self._tools[name] = tool_obj

    def get(self, name: str) -> Any:
        """按名字获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[Any]:
        """返回所有工具对象列表（用于 bind_tools）"""
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """返回所有工具名"""
        return list(self._tools.keys())

    def describe(self) -> str:
        """生成工具箱描述文本"""
        lines = ["BuiltinToolkit 已注册工具："]
        for name, t in self._tools.items():
            desc = getattr(t, "description", str(t))[:50]
            lines.append(f"  - {name}: {desc}")
        return "\n".join(lines)


# ============================================================
# 演示：直接调用内置工具（不经过 LLM）
# ============================================================

def demo_direct_invoke(toolkit: BuiltinToolkit) -> None:
    """直接调用内置工具，展示其便捷性"""
    print("\n" + "🔧 内置工具直接调用演示".center(60, "="))

    # 计算器
    print("\n[1] 计算器:")
    calc = toolkit.get("calculator")
    if calc:
        for expr in ["2*(3+4)", "100/7", "2**10"]:
            print(f"    {calc.invoke({'expression': expr})}")

    # DuckDuckGo 搜索（需要网络）
    print("\n[2] DuckDuckGo 搜索:")
    ddg = toolkit.get("ddg_search")
    if ddg:
        try:
            result = ddg.invoke("LangChain 框架 是什么")
            print(f"    搜索结果（前 200 字）: {result[:200]}...")
        except Exception as e:
            print(f"    搜索失败（可能是网络问题）: {e}")
    else:
        print("    未安装，跳过")

    # Wikipedia 查询
    print("\n[3] Wikipedia 查询:")
    wiki = toolkit.get("wikipedia")
    if wiki:
        try:
            result = wiki.invoke("Python (programming language)")
            print(f"    查询结果（前 200 字）: {result[:200]}...")
        except Exception as e:
            print(f"    查询失败（可能是网络问题）: {e}")
    else:
        print("    未安装，跳过")


# ============================================================
# 演示：用 bind_tools 让模型调用内置工具
# ============================================================

def demo_llm_tool_calling(toolkit: BuiltinToolkit) -> None:
    """绑定内置工具到模型，让模型决定调用哪个工具"""
    print("\n" + "🤖 模型驱动工具调用演示".center(60, "="))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  未检测到 OPENAI_API_KEY，跳过模型调用演示。")
        return

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, ToolMessage
    except ImportError:
        print("⚠️  未安装 langchain-openai，跳过。")
        return

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = toolkit.list_tools()
    if not tools:
        print("⚠️  无可用工具，跳过。")
        return

    model_with_tools = model.bind_tools(tools)

    # 测试问题：模型应选择计算器
    question = "请计算 123 乘以 456 等于多少"
    print(f"\n问题：{question}")

    messages = [HumanMessage(content=question)]
    ai_msg = model_with_tools.invoke(messages)

    if ai_msg.tool_calls:
        for tc in ai_msg.tool_calls:
            print(f"模型选择工具: {tc['name']}({tc['args']})")
            # 执行工具
            selected = toolkit.get(tc["name"])
            if selected:
                result = selected.invoke(tc["args"])
                print(f"工具结果: {result}")
                # 回传结果
                messages.append(ai_msg)
                messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))
        # 生成最终回复
        final = model_with_tools.invoke(messages)
        print(f"最终回复: {final.content}")
    else:
        print(f"模型直接回复（未调用工具）: {ai_msg.content}")


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day09 - 03 内置工具使用演示")
    print("工具：DuckDuckGo 搜索 / Wikipedia / 计算器")
    print("=" * 60)

    # 创建工具箱
    toolkit = BuiltinToolkit()
    print("\n" + toolkit.describe())

    # 直接调用演示
    demo_direct_invoke(toolkit)

    # 模型驱动调用演示
    demo_llm_tool_calling(toolkit)

    print("\n" + "=" * 60)
    print("✅ 内置工具演示完成")
    print("内置工具优势：")
    print("  - 开箱即用，无需手写函数")
    print("  - 社区维护，覆盖常见场景（搜索/百科/计算）")
    print("  - 可通过 BuiltinToolkit 统一管理")
    print("=" * 60)


if __name__ == "__main__":
    main()
