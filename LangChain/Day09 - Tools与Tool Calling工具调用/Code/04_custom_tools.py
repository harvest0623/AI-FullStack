# 文件用途：自定义工具 + Chain 集成（ToolCallingChain 模式）
# 场景：ChainQA 智能问答系统——根据问题选择工具→执行→生成回答
# 包含：天气查询工具 / 数据库查询工具 / API 调用工具 + 工具错误处理
# 运行：python 04_custom_tools.py
# 依赖：pip install langchain langchain-openai python-dotenv pydantic
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.tools import tool

load_dotenv()


# ============================================================
# 自定义工具1：天气查询（含错误处理）
# ============================================================

@tool
def query_weather(city: str) -> str:
    """查询指定城市的实时天气信息。

    当用户询问某个城市的天气、气温、是否下雨等问题时使用本工具。

    参数:
        city: 城市中文名，例如 "北京"、"上海"、"广州"
    """
    # 模拟天气 API（真实场景调用第三方天气服务）
    weather_db = {
        "北京": "晴，气温 25°C，湿度 40%，北风 3 级",
        "上海": "多云，气温 28°C，湿度 65%，东南风 2 级",
        "广州": "雷阵雨，气温 31°C，湿度 80%，南风 4 级",
        "深圳": "多云转晴，气温 30°C，湿度 70%",
        "杭州": "晴，气温 27°C，湿度 55%",
    }
    if not city or not city.strip():
        return "错误：城市名不能为空，请提供有效城市名。"
    return weather_db.get(city.strip(), f"暂无 {city} 的天气数据。")


# ============================================================
# 自定义工具2：数据库查询（含错误处理，模拟）
# ============================================================

class DBQueryInput(BaseModel):
    """数据库查询参数 Schema"""
    table: str = Field(description="要查询的表名，例如 users / orders / products")
    condition: str = Field(
        default="",
        description="查询条件（WHERE 子句），例如 'age > 18'。留空表示查全部。"
    )


@tool(args_schema=DBQueryInput)
def query_database(table: str, condition: str = "") -> str:
    """查询 ChainQA 内置数据库中的数据。

    当用户需要查询用户信息、订单信息、产品信息等结构化数据时使用本工具。
    支持的表：users（用户表）、orders（订单表）、products（产品表）。

    参数:
        table: 表名
        condition: 可选的查询条件
    """
    # 模拟数据库（真实场景连接 MySQL/PostgreSQL）
    db = {
        "users": [
            {"id": 1, "name": "张三", "age": 25, "city": "北京"},
            {"id": 2, "name": "李四", "age": 30, "city": "上海"},
            {"id": 3, "name": "王五", "age": 17, "city": "广州"},
        ],
        "orders": [
            {"id": 101, "user_id": 1, "amount": 199.0, "status": "已支付"},
            {"id": 102, "user_id": 2, "amount": 89.5, "status": "待发货"},
        ],
        "products": [
            {"id": 1, "name": "LangChain 教程", "price": 99.0, "stock": 50},
            {"id": 2, "name": "Python 进阶", "price": 79.0, "stock": 30},
        ],
    }

    # 错误处理：表不存在时返回友好提示（而非抛异常）
    if table not in db:
        available = "、".join(db.keys())
        return f"错误：表 '{table}' 不存在。可用的表有：{available}。"

    rows = db[table]
    # 简单条件过滤模拟（真实场景用 SQL 引擎）
    if condition:
        # 这里仅做演示性过滤，生产环境应使用正规 SQL 解析
        try:
            # 提取条件中的关键字做简单匹配（避免直接 eval 带来的安全风险）
            if "age >" in condition:
                threshold = int(condition.split(">")[1].strip())
                rows = [r for r in rows if r.get("age", 0) > threshold]
            elif "city" in condition and "=" in condition:
                city_val = condition.split("=")[1].strip().strip("'\"")
                rows = [r for r in rows if r.get("city") == city_val]
        except Exception as e:
            return f"条件解析失败：{e}。请使用如 'age > 18' 的简单条件。"

    if not rows:
        return f"表 {table} 中无满足条件 '{condition}' 的记录。"
    return f"查询到 {len(rows)} 条记录：{rows}"


# ============================================================
# 自定义工具3：API 调用工具（模拟外部 API）
# ============================================================

@tool
def call_external_api(endpoint: str) -> str:
    """调用 ChainQA 外部 API 获取扩展信息。

    当用户需要获取系统状态、版本信息、外部服务等信息时使用本工具。

    参数:
        endpoint: API 端点路径，例如 '/status'、'/version'、'/health'
    """
    # 模拟 API 响应（真实场景用 requests/httpx 调用）
    api_responses = {
        "/status": "系统状态：正常运行，当前在线用户 128 人",
        "/version": "ChainQA v1.2.0，构建于 2025-01-15",
        "/health": "健康检查：所有服务正常，数据库连接 OK",
    }
    if endpoint not in api_responses:
        available = "、".join(api_responses.keys())
        return f"错误：端点 '{endpoint}' 不存在。可用端点：{available}。"
    return api_responses[endpoint]


# 工具映射表
TOOL_MAP = {
    "query_weather": query_weather,
    "query_database": query_database,
    "call_external_api": call_external_api,
}


# ============================================================
# ToolCallingChain：把工具调用封装为 Chain
# ============================================================

class ToolCallingChain:
    """工具调用链：根据问题选择工具→执行→生成最终回答。

    这是 ChainQA 的工具增强问答核心模式：
    1. 接收用户问题
    2. 模型决定调用哪个工具
    3. 执行工具
    4. 把工具结果回传给模型生成最终回复
    """

    def __init__(self, model_with_tools: Any, tool_map: dict) -> None:
        self.model = model_with_tools
        self.tool_map = tool_map

    def _execute_tool_calls(self, ai_msg) -> list[ToolMessage]:
        """执行 AI 消息中的所有 tool_calls，返回 ToolMessage 列表"""
        tool_messages = []
        for tc in ai_msg.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            selected = self.tool_map.get(tool_name)

            if selected is None:
                result = f"错误：工具 {tool_name} 不存在。"
            else:
                # 执行工具（工具内部已做错误处理）
                result = selected.invoke(tool_args)

            print(f"     ⚙️  执行 {tool_name}({tool_args})")
            print(f"        结果: {result[:100]}{'...' if len(result) > 100 else ''}")

            tool_messages.append(ToolMessage(
                content=result,
                tool_call_id=tc["id"],
            ))
        return tool_messages

    def invoke(self, question: str) -> str:
        """执行完整的工具调用链"""
        print(f"\n📝 问题：{question}")

        # 步骤1：用户提问
        messages = [HumanMessage(content=question)]

        # 步骤2：模型决定调用工具
        ai_msg = self.model.invoke(messages)

        # 步骤3：如果没有工具调用，直接返回
        if not ai_msg.tool_calls:
            print("   ℹ️  模型未调用工具，直接回复")
            return ai_msg.content

        # 步骤4：执行工具
        print(f"   🎯 模型决定调用 {len(ai_msg.tool_calls)} 个工具")
        messages.append(ai_msg)
        tool_msgs = self._execute_tool_calls(ai_msg)
        messages.extend(tool_msgs)

        # 步骤5：模型基于工具结果生成最终回复
        final = self.model.invoke(messages)
        return final.content


def make_tool_calling_runnable(model_with_tools: Any, tool_map: dict) -> Any:
    """把 ToolCallingChain 包装为 LCEL Runnable，便于集成到更大流程。

    返回的 Runnable 接收 {"question": "..."} 输入，输出最终回答字符串。
    """
    chain = ToolCallingChain(model_with_tools, tool_map)

    def _run(input_dict: dict) -> str:
        question = input_dict["question"]
        return chain.invoke(question)

    # 用 RunnableLambda 包装为 Runnable，支持 | 管道组合
    return RunnablePassthrough() | RunnableLambda(_run)


# ============================================================
# 主流程：ChainQA 工具增强问答演示
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day09 - 04 自定义工具 + Chain 集成（ChainQA 工具增强问答）")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        return

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("❌ 未安装 langchain-openai，请安装：pip install langchain-openai")
        return

    # 初始化模型并绑定工具
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [query_weather, query_database, call_external_api]
    model_with_tools = model.bind_tools(tools)

    print("\n已注册工具：")
    for t in tools:
        print(f"  - {t.name}: {t.description[:50]}...")

    # 创建 ToolCallingChain（直接类方式）
    chain = ToolCallingChain(model_with_tools, TOOL_MAP)

    # 创建 LCEL Runnable 方式（便于集成）
    runnable = make_tool_calling_runnable(model_with_tools, TOOL_MAP)

    # 测试用例集：覆盖不同工具
    test_cases = [
        # 天气查询
        "北京和上海今天的天气分别怎么样？",
        # 数据库查询
        "帮我查一下 users 表中年龄大于 18 岁的用户",
        # API 调用
        "ChainQA 系统当前状态如何？",
        # 错误处理：查询不存在的表
        "帮我查一下 logs 表的数据",
        # 无需工具
        "用一句话解释什么是 Tool Calling",
    ]

    print("\n" + "=" * 60)
    print("🔧 测试用例1-3：使用 ToolCallingChain 类")
    print("=" * 60)
    for q in test_cases[:3]:
        answer = chain.invoke(q)
        print(f"   💬 回答：{answer}\n")

    print("=" * 60)
    print("🔧 测试用例4：工具错误处理演示")
    print("=" * 60)
    answer = chain.invoke(test_cases[3])
    print(f"   💬 回答：{answer}\n")

    print("=" * 60)
    print("🔧 测试用例5：使用 LCEL Runnable 方式（便于集成到更大流程）")
    print("=" * 60)
    result = runnable.invoke({"question": test_cases[4]})
    print(f"   💬 回答：{result}\n")

    print("=" * 60)
    print("✅ 自定义工具 + Chain 集成演示完成")
    print("要点总结：")
    print("  1. 自定义工具应包含错误处理，返回友好提示而非抛异常")
    print("  2. ToolCallingChain 封装了'选择→执行→生成'的闭环")
    print("  3. 可用 RunnableLambda 包装为 LCEL Runnable，便于管道组合")
    print("  4. 这是 Agent 的雏形——后续 Agent 板块在此基础上增加循环决策")
    print("=" * 60)


if __name__ == "__main__":
    main()
