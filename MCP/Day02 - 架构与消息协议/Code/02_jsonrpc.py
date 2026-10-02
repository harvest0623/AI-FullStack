# -*- coding: utf-8 -*-
"""
Day02 - 02 JSON-RPC 消讯分类

用具体示例演示 JSON-RPC 2.0 的三种消息：request / response / notification，
并给出『是按 id 判断类型』的识别逻辑。

离线可运行（纯讲解 + 演示）。
"""


def show(messages):
    for i, msg in enumerate(messages, 1):
        print(f"  消息 {i}:")
        print(f"  {msg}")
        cls = classify(msg)
        print(f"  → 分类：{cls}\n")


def classify(msg: dict) -> str:
    if not isinstance(msg, dict):
        return "非法"
    jr = msg.get("jsonrpc")
    if jr != "2.0":
        return "非法（协议版本错误）"
    has_id = "id" in msg
    method = "method" in msg
    has_result = "result" in msg
    has_error = "error" in msg
    if method:
        # 请求或通知，看是否有 id
        return "Request（请求，带id，需应答）" if has_id else "Notification（通知，无id，单向）"
    else:
        return "Response（响应，需匹配请求id）"


def main():
    print(">> JSON-RPC 2.0 三种消息\n")
    print("  判定规则：有 method + 有 id = 请求；有 method + 无 id = 通知；")
    print("            有 result / error = 响应。\n")

    messages = [
        # 请求 tools/list
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        # 响应
        {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "echo"}]}},
        # 通知 initialized（无 id）
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        # 请求调用工具
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "echo", "arguments": {"text": "hi"}}},
        # 错误响应
        {"jsonrpc": "2.0", "id": 2, "error": {"code": -32602, "message": "Invalid params"}},
    ]
    show(messages)

    print("  要点：")
    print("    · id 用于把『响应』和『请求』对上号（并发安全）")
    print("    · 通知不需要应答（没有 id）")
    print("    · 响应要么带 result，要么带 error（二选一）")


if __name__ == "__main__":
    main()