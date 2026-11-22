"""
Day02 工具/函数定义 schema
=========================
核心: 工具怎么"说明"给模型, 决定了模型能不能用对。
FunctionSpec 一份需要:
  - name          函数名(模型用来选择)
  - description   描述(模型判断"何时用")
  - parameters    JSON Schema 描述参数(类型/必填/枚举)
演示: 定义一个结构完整的多参数工具, 并打印它转成的 OpenAI tools 结构;
      用规则 planner 模拟模型读懂 schema 后正确传参。

运行:
  python "Day02 - 工具与函数定义schema/Code/02-schema.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_get_weather,
    tool_add,
)


def main() -> None:
    # ---------- 1. 定义一个参数较复杂的气象工具 ----------
    weather_spec = FunctionSpec(
        name="get_weather",
        description="查询城市今天天气; 城市用中文名, 可选温度单位 C/F。",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名, 必需"},
                "unit": {"type": "string", "enum": ["C", "F"],
                         "description": "温度单位, 默认 C"},
            },
            "required": ["city"],     # 只有 city 必填
        },
        func=tool_get_weather,
    )

    # ---------- 2. 看转成的 OpenAI 风格 tools ----------
    print("转成的 OpenAI tools 结构:")
    tool = weather_spec.to_openai_tool()
    # 格式化打印
    import json
    print(json.dumps(tool, ensure_ascii=False, indent=2))

    # ---------- 3. 用规则 planner 演示"模型读懂必填参数" ----------
    def planner(messages, tools):
        if any(m["role"] == "tool" for m in messages):
            for m in messages:
                if m["role"] == "tool":
                    return ("text", m["content"])
        text = messages[-1]["content"]
        # 规则: 含"上海"就传 city=上海; 含"华氏"就再加 unit=F
        args = {"city": next((c for c in ("上海", "北京", "广州", "深圳") if c in text), "上海")}
        if "华氏" in text:
            args["unit"] = "F"
        return ("call", [{"name": "get_weather", "args": args}])

    reg = FunctionRegistry().add(weather_spec)
    llm = FunctionCallingLLM(plan=planner)

    print("=" * 60)
    print("问: '北京温度按华氏来'")
    print("答:", llm.chat_with_tools("北京温度按华氏来", reg))

    # ---------- 4. 对比: 一个参数简单函数 ----------
    add_spec = FunctionSpec(
        name="add",
        description="两个数相加",
        parameters={"type": "object",
                    "properties": {"a": {"type": "number"},
                                   "b": {"type": "number"}},
                    "required": ["a", "b"]},
        func=tool_add,
    )
    print("=" * 60)
    print("add 工具的 parameters:", add_spec.parameters)

    assert weather_spec.name == "get_weather"
    assert "unit" in weather_spec.parameters["properties"]
    assert weather_spec.parameters["required"] == ["city"]
    print("schema 断言通过 ✓")


if __name__ == "__main__":
    main()