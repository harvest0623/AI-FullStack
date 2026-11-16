# -*- coding: utf-8 -*-
"""
Day01 - 02 一次工具调用的生命周期

逐步演示四次调用：定义工具 → 模型决策 → 应用执行 → 回填作答。

离线可运行（纯讲解 + 演示）。
"""


def lifecycle():
    print("一次工具调用的生命周期（4 步）：\n")
    steps = [
        ("① 定义并传入工具", "应用把工具描述成 JSON（tools）"),
        ("② 模型决策", "模型判断需要调用 → 返回 tool_calls（含 id/name/arguments）"),
        ("③ 应用执行", "应用解析参数 → 执行对应函数 → 拿到结果"),
        ("④ 回填与作答", "结果以『角色=tool』消息发回 → 模型基于结果生成最终答复"),
    ]
    for title, desc in steps:
        print(f"  ■ {title}")
        print(f"     {desc}\n")


def demo():
    print("  -------- 一个最小演示 --------\n")
    print("  用户：『2 加 3 等于几』")

    # ① 工具定义（简化）
    tool_def = {"name": "add", "description": "两个数相加",
               "parameters": {"type": "object",
                              "properties": {"a": {"type": "integer"},
                                             "b": {"type": "integer"}},
                              "required": ["a", "b"]}}
    print(f"  ① 传入工具：add（可计算两数之和）")

    # ② 模型决策（演示：直接给出 tool_calls）
    tool_calls = [{"id": "c1", "name": "add", "args": {"a": 2, "b": 3}}]
    print(f"  ② 模型返回：tool_calls = {tool_calls}")

    # ③ 应用执行
    result = tool_calls[0]["args"]["a"] + tool_calls[0]["args"]["b"]
    print(f"  ③ 应用执行 add(2,3) → 结果 {result}")

    # ④ 回填并作答
    print(f"  ④ 以 tool 角色回填结果 {result}，模型作答：『2+3 = {result}』\n")


def main():
    print(">> 工具调用生命周期\n")
    lifecycle()
    demo()
    print("  tips: 当一次调用不够时，②③④ 会反复进行，形成『工具循环』（Day06）。")


if __name__ == "__main__":
    main()