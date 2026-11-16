# -*- coding: utf-8 -*-
"""
Day01 - 01 工具调用是什么

讲清工具调用的本质：模型"只提议、不执行"，执行由应用完成。

离线可运行（纯讲解）。
"""


def essence():
    print("工具调用（Tool / Function Calling）的本质：\n")
    print("  大模型在生成时，可以结构化地说：『我需要调用这个工具，传这些参数』")
    print("  但——模型不执行！真正执行永远是应用代码。\n")
    print("  一句话：模型是『总指挥』，应用是『执行大队』，")
    print("          工具的后果由应用负责。\n")


def example():
    print("一个直观示例（天气查询）：\n")
    print("  用户：『北京天气如何？』\n")
    print("  模型内部决策：调用 get_weather(city='北京')\n")
    print("  模型返回（结构化）：")
    print("""  {
    "tool_calls": [
      { "id": "call_1",
        "type": "function",
        "function": { "name": "get_weather",
                      "arguments": "{\\"city\\": \\"北京\\"}" } }
    ]
  }""")
    print("\n  应用收到后自己执行 get_weather，再把结果回填给模型。")


def why():
    print("\n为什么这样设计？\n")
    rows = [
        ("安全", "执行权在应用手里，可校验/授权/审计"),
        ("灵活", "同一工具可被不同模型/应用复用"),
        ("解耦", "决策（模型）与动作（执行器）清晰分离"),
        ("可控", "结果回填，模型基于真实结果继续作答"),
    ]
    for k, v in rows:
        print(f"  · {k:<4}{v}")


def main():
    print(">> 工具调用是什么\n")
    essence()
    example()
    why()
    print("\n  tips: 抓住『提议 vs 执行』这一对概念，后续全是它的展开。")


if __name__ == "__main__":
    main()