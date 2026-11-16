# -*- coding: utf-8 -*-
"""
Day04 - 01 完整工具调用闭环（离线模拟）

用内置模拟模型把"定义→决策→执行→回填→作答"完整跑一遍。

离线可运行（不真实发请求）。
"""

import json


# ---------- 第①类：工具注册表（简化） ----------
def get_weather(city: str) -> str:
    """真实工具：查天气。给个假数据。"""
    data = {"北京": "晴 25°C", "上海": "小雨 22°C", "广州": "多云 30°C"}
    return f"{city}：{data.get(city, '未知城市')}"


TOOLS = {
    "get_weather": {
        "fn": get_weather,
        "desc": "查询指定城市的天气",
    },
}


def _tool_schema(name):
    return {"type": "function", "function": {
        "name": name,
        "description": TOOLS[name]["desc"],
        "parameters": {"type": "object",
                       "properties": {"city": {"type": "string"}},
                       "required": ["city"]},
    }}


# ---------- 模拟模型 ----------
def mock_model(user_input):
    """极简'模型'：识别城市 → 产出 tool_calls。"""
    city = "北京" if "北京" in user_input else "上海" if "上海" in user_input else "广州"
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_demo",
            "type": "function",
            "function": {"name": "get_weather",
                         "arguments": json.dumps({"city": city})},
        }],
    }


# ---------- 应用侧执行 + 回填 ----------
def execute(tool_call):
    fn = TOOLS[tool_call["function"]["name"]]["fn"]
    args = json.loads(tool_call["function"]["arguments"])
    return fn(**args)


def main():
    user_input = "北京天气怎么样？"
    print(f">> 用户：『{user_input}』\n")

    print(f"  ① 传入工具：{_tool_schema('get_weather')['function']['name']}")

    assistant_message = mock_model(user_input)
    tc = assistant_message["tool_calls"][0]
    print(f"  ② 模型返回 tool_calls：name={tc['function']['name']} "
          f"arguments={tc['function']['arguments']}")

    result = execute(tc)
    print(f"  ③ 应用执行 → {result}")

    # 回填：以 tool 角色带回结果
    tool_message = {"role": "tool", "tool_call_id": tc["id"],
                    "content": str(result)}
    print(f"  ④ 回填（role=tool）→ 内容 {tool_message['content']}")

    weather_part = result  # 结果形如 "北京：晴 25°C"
    print(f"\n  模型收到结果后作答：『北京今天{weather_part}』")


if __name__ == "__main__":
    main()