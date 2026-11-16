# -*- coding: utf-8 -*-
"""
Day05 - 01 多工具调用与回填

一次返回多个 tool_calls，遍历执行，按 tool_call_id 一一回填。

离线可运行（纯演示，模拟模型产出多个调用）。
"""

import json


# 工具注册表
def get_weather(city):
    return {"北京": "晴 22°C", "上海": "小雨 30°C", "广州": "多云 28°C"}[city]


def get_time(city):
    return {"北京": "14:00", "上海": "14:00", "广州": "14:00"}[city]


TOOLS = {
    "get_weather": get_weather,
    "get_time": get_time,
}


def mock_model(query):
    """模拟模型：同时请求两个工具的调用。"""
    return [{
        "id": "c_wx",
        "type": "function",
        "function": {"name": "get_weather", "arguments": json.dumps({"city": "北京"})},
    }, {
        "id": "c_tm",
        "type": "function",
        "function": {"name": "get_time", "arguments": json.dumps({"city": "北京"})},
    }]


def execute(tc):
    name = tc["function"]["name"]
    args = json.loads(tc["function"]["arguments"])
    return TOOLS[name](**args)


def main():
    print(">> 多工具调用与回填\n")
    user = "北京现在天气和时间"
    print(f"  用户：『{user}』\n")

    tool_calls = mock_model(user)
    print(f"  模型返回 {len(tool_calls)} 个调用：")
    for tc in tool_calls:
        print(f"    - {tc['function']['name']}  id={tc['id']}")

    print("\n  应用遍历执行并回填：\n")
    tool_messages = []
    for tc in tool_calls:
        result = execute(tc)
        tool_messages.append({
            "role": "tool", "tool_call_id": tc["id"], "content": str(result),
        })
        print(f"    {tc['function']['name']} → {result} （回填到 id={tc['id']}）")

    print("\n  回填后的消息列表（将随原 assistant 消息再发给模型）：")
    for m in tool_messages:
        print(f"    role={m['role']}  id={m['tool_call_id']}  content={m['content']}")

    print("\n  tips: 每个结果必须带对应 tool_call_id，模型才能正确引用。")


if __name__ == "__main__":
    main()