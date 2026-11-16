# -*- coding: utf-8 -*-
"""
Day03 - 02 description 决定调用准确度

同样的工具，description 写得好坏，直接影响{'模拟模型'}能否正确决策与填参。

离线可运行（讲解 + 比较演示）。
"""


def mock_choose(prompt, tool_desc):
    """极简'决策器'：描述是否包含关键提示词，决定是否调用。"""
    # 描述里有关键词、且与用户诉求匹配才调用
    keys = ["weather", "天气", "temperature", "温度", "气温"] if "天气" in prompt else []
    if "天气" in prompt.strip() or "气温" in prompt.strip():
        keys = ["天气", "气温"]
    return any(k in tool_desc for k in keys)


def main():
    print(">> description 的影响\n")

    bad_desc = "一个查询工具。"
    good_desc = "查询指定城市的当前天气：输入城市名(city)，返回温度与天气状况。"

    prompt = "北京今天气温多少？"
    print(f"  用户：『{prompt}』\n")

    print("  差描述：一个查询工具。")
    print(f"    → 过于含糊，模型可能误判或不知填什么参数。")
    print(f"    （模拟判定是否倾向调用：{mock_choose(prompt, bad_desc)}）\n")

    print("  好描述：查询指定城市的当前天气：输入城市名(city)，返回温度与天气状况。")
    print(f"    → 明确『天气/城市/返回』，模型易锁定工具并填对 city 参数。")
    print(f"    （模拟判定是否倾向调用：{mock_choose(prompt, good_desc)}）\n")

    print("-" * 60)
    print("写 description 的要点：")
    print("  · 说明『目的』：这个工具解决什么问题")
    print("  · 说明『参数』：每个参数是什么、怎么取值")
    print("  · 说明『何时用』：在什么情况下应该调用它")
    print("  · 给取值示例：如城市名的写法，引导填参")


if __name__ == "__main__":
    main()