# -*- coding: utf-8 -*-
"""
Day02 - 01 模型如何感知工具并决策

说明模型看到的只是文本描述：tools 参数 + 一个最小决策演示。

离线可运行（纯讲解 + 演示）。
"""


def how():
    print("模型如何『感知』工具？\n")
    print("  调用时把工具清单以 tools 参数一并送入模型。")
    print("  对模型而言，每个工具都是一段文本（JSON 描述），不是可执行的代码。\n")
    print("""  模型看到的 get_weather 大概是：
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "查询指定城市的当前天气",
      "parameters": {
        "type": "object",
        "properties": { "city": { "type": "string", "description": "城市名" } },
        "required": ["city"]
      }
    }
  }
  """)
    print("  模型从中知道：有个工具叫 get_weather，能按 city 查天气。")


def decide_demo():
    print("-" * 60)
    print("最小决策演示（模拟模型判断是否要调工具）：\n")
    # 极简'决策器'：规则判断而不是真模型
    def mock_model(prompt: str, description: str) -> bool:
        # 若用户话里含"天气"，判定需要天气工具
        return "天气" in prompt

    cases = [
        ("北京天气如何？", "get_weather 查天气"),
        ("帮我算 1+1", "add 加法工具"),
    ]
    for prompt, tool_desc in cases:
        need = mock_model(prompt, tool_desc)
        print(f"  用户：『{prompt}』")
        print(f"  模型读到工具描述『{tool_desc}』")
        print(f"  → 是否调用工具：{'是（返回 tool_calls）' if need else '否（直接文本回答）'}\n")


def point():
    print("要点：")
    print("  · description 决定模型『知不知道用什么、何时用』")
    print("  · 参数 schema 决定模型『能不能填对参数』")


def main():
    print(">> 模型如何感知与决策\n")
    how()
    decide_demo()
    point()
    print("\n  tips: 工具的『描述文本』就是模型的世界，写好它等于教模型用工具。")


if __name__ == "__main__":
    main()