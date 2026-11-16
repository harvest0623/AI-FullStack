# -*- coding: utf-8 -*-
"""
Day06 - 02 错误处理与回填

演示各种工具调用错误的捕获，并把错误转成 tool 角色内容回填给模型。

离线可运行。
"""

import json


def get_stock(code):
    if code == "A":
        return "13.5"
    raise ValueError(f"查不到股票 {code}")


TOOLS = {"get_stock": get_stock}


def safe_execute(tc):
    """执行单个 tool_call，任何错误都转成字符串结果（不抛出）。"""
    name = tc["function"]["name"]
    try:
        args = json.loads(tc["function"]["arguments"]) if tc["function"].get("arguments") else {}
    except json.JSONDecodeError:
        return "参数解析失败（非法 JSON）"
    if name not in TOOLS:
        return f"未知工具：{name}"
    try:
        return TOOLS[name](**args)
    except Exception as e:
        return f"工具执行失败：{e}"


def main():
    print(">> 错误处理与回填\n")
    cases = [
        ("正常", {"id": "a", "function": {"name": "get_stock",
                                          "arguments": json.dumps({"code": "A"})}}),
        ("参数非法JSON", {"id": "b", "function": {"name": "get_stock", "arguments": "not-json"}}),
        ("执行抛错", {"id": "c", "function": {"name": "get_stock",
                                              "arguments": json.dumps({"code": "X"})}}),
        ("未知工具", {"id": "d", "function": {"name": "none_tool", "arguments": "{}"}}),
    ]
    for label, tc in cases:
        result = safe_execute(tc)
        print(f"  {label}：")
        print(f"    结果回填 → role=tool, id={tc['id']}, content={result}\n")

    print("  tips: 把错误作为 tool 结果回填，模型读完就知道失败并可尝试兜底或重试。")


if __name__ == "__main__":
    main()