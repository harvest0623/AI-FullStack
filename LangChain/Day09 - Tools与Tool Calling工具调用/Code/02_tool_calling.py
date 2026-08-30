# 文件用途：演示 Tool Calling 完整七步流程（含消息流追踪）
# 场景：用户问天气 → 模型调用天气工具 → 返回结果 → 模型生成最终回复
# 运行：python 02_tool_calling.py
# 依赖：pip install langchain langchain-openai python-dotenv pydantic
# 需要：在 .env 中配置 OPENAI_API_KEY

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


# ============================================================
# 步骤0：定义工具
# ============================================================

@tool
def search_weather(city: str) -> str:
    """查询指定城市的实时天气情况。当用户询问某地天气时使用本工具。

    参数:
        city: 要查询的城市中文名，例如 "北京"、"上海"
    """
    weather_db = {
        "北京": "晴，气温 25°C，湿度 40%，北风 3 级",
        "上海": "多云，气温 28°C，湿度 65%，东南风 2 级",
        "广州": "雷阵雨，气温 31°C，湿度 80%，南风 4 级",
        "深圳": "多云转晴，气温 30°C，湿度 70%",
    }
    return weather_db.get(city, f"暂无 {city} 的天气数据")


@tool
def simple_calculator(expression: str) -> str:
    """计算数学表达式的值。当用户需要做数学计算时使用本工具。

    参数:
        expression: 数学表达式字符串，例如 "1+2*3"、"(10+5)/3"
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败：{e}"


# 工具映射表：工具名 → 工具对象，便于根据名字查找执行
TOOL_MAP = {
    "search_weather": search_weather,
    "simple_calculator": simple_calculator,
}


# ============================================================
# 辅助函数：打印消息流（追踪 Tool Calling 全过程）
# ============================================================

def print_message_flow(messages: list, step: str) -> None:
    """打印当前消息列表，追踪 Tool Calling 的消息流变化"""
    print(f"\n{'─' * 60}")
    print(f"📍 {step}")
    print(f"{'─' * 60}")
    for i, msg in enumerate(messages):
        msg_type = msg.__class__.__name__
        content_preview = str(msg.content)[:80] if msg.content else "(空)"
        print(f"  [{i}] {msg_type}: {content_preview}")
        # 如果是 AI 消息且包含 tool_calls，打印工具调用信息
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"       └─ tool_call: name={tc['name']}, args={tc['args']}, id={tc['id']}")
        # 如果是 ToolMessage，打印关联的 tool_call_id
        if isinstance(msg, ToolMessage):
            print(f"       └─ tool_call_id={msg.tool_call_id}")


# ============================================================
# 核心：Tool Calling 完整七步流程
# ============================================================

def tool_calling_pipeline(question: str, model_with_tools: Any) -> str:
    """执行完整的 Tool Calling 七步流程，返回最终回复。

    流程：
        1. 用户提问（构造 HumanMessage）
        2. 模型分析意图，决定调用工具
        3. 模型返回 tool_calls
        4. 执行工具：tool.invoke(args)
        5. 包装结果为 ToolMessage
        6. 将 ToolMessage 发回模型
        7. 模型基于工具结果生成最终回复
    """
    print(f"\n{'=' * 60}")
    print(f"🎯 用户问题：{question}")
    print(f"{'=' * 60}")

    # ── 步骤1：用户提问 ──
    messages: list = [HumanMessage(content=question)]
    print_message_flow(messages, "步骤1：用户提问（构造 HumanMessage）")

    # ── 步骤2-3：模型分析意图并返回 tool_calls ──
    print("\n⏳ 步骤2-3：模型分析意图，决定是否调用工具...")
    ai_response: AIMessage = model_with_tools.invoke(messages)

    # 检查模型是否决定调用工具
    if not ai_response.tool_calls:
        # 模型直接回答，无需工具
        print("ℹ️  模型未调用工具，直接回复")
        print_message_flow(messages + [ai_response], "模型直接回复（无 tool_calls）")
        return ai_response.content

    print(f"✅ 模型决定调用 {len(ai_response.tool_calls)} 个工具：")
    for tc in ai_response.tool_calls:
        print(f"   → {tc['name']}({tc['args']})")

    # 把模型的 AI 回复（含 tool_calls）加入消息流
    # 注意顺序：[Human, AIMessage(tool_calls), ToolMessage, ...]
    messages.append(ai_response)
    print_message_flow(messages, "步骤3：模型返回 AIMessage（含 tool_calls）")

    # ── 步骤4-5：执行工具并包装为 ToolMessage ──
    print("\n⚙️  步骤4-5：执行工具并包装结果为 ToolMessage")
    for tool_call in ai_response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]

        # 根据工具名找到对应工具并执行
        selected_tool = TOOL_MAP.get(tool_name)
        if selected_tool is None:
            tool_result = f"错误：未找到工具 {tool_name}"
        else:
            tool_result = selected_tool.invoke(tool_args)

        print(f"   执行 {tool_name}({tool_args})")
        print(f"   结果: {tool_result}")

        # 包装为 ToolMessage，必须带上 tool_call_id 关联请求
        tool_msg = ToolMessage(
            content=tool_result,
            tool_call_id=tool_call_id,
        )
        messages.append(tool_msg)

    print_message_flow(messages, "步骤5：工具结果包装为 ToolMessage 加入消息流")

    # ── 步骤6-7：把 ToolMessage 发回模型，生成最终回复 ──
    print("\n⏳ 步骤6-7：将工具结果发回模型，生成最终回复...")
    final_response: AIMessage = model_with_tools.invoke(messages)
    messages.append(final_response)

    print_message_flow(messages, "步骤7：模型基于工具结果生成最终回复")

    print(f"\n💬 最终回复：{final_response.content}")
    return final_response.content


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day09 - 02 Tool Calling 完整流程演示")
    print("场景：用户问天气 → 模型调用天气工具 → 返回最终回复")
    print("=" * 60)

    # 检查 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置后运行。")
        print("   本演示需要真实调用模型来观察 tool_calls 生成。")
        return

    # 初始化模型
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # ── 关键：用 bind_tools 把工具绑定到模型 ──
    model_with_tools = model.bind_tools([search_weather, simple_calculator])

    print("\n已绑定工具列表：")
    for t in [search_weather, simple_calculator]:
        print(f"  - {t.name}: {t.description[:40]}...")

    # 测试用例1：天气查询（单工具调用）
    tool_calling_pipeline("北京今天天气怎么样？", model_with_tools)

    # 测试用例2：计算器（单工具调用）
    tool_calling_pipeline("请帮我计算 (15 + 27) * 3 的结果", model_with_tools)

    # 测试用例3：无需工具（模型直接回答）
    tool_calling_pipeline("你好，请用一句话介绍你自己", model_with_tools)

    print("\n" + "=" * 60)
    print("✅ Tool Calling 完整流程演示完成")
    print("关键要点：")
    print("  1. bind_tools() 让模型知道可用工具")
    print("  2. 模型返回的 tool_calls 含 name/args/id")
    print("  3. 执行工具后必须用 ToolMessage 回传，且 tool_call_id 要对应")
    print("  4. 消息流顺序：[Human, AIMessage(tool_calls), ToolMessage, AIMessage(最终)]")
    print("=" * 60)


if __name__ == "__main__":
    main()
