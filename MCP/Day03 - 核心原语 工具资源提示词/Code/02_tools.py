# -*- coding: utf-8 -*-
"""
Day03 - 02 Tools（工具）详解

工具的结构、JSON Schema 参数、以及 tools/call 的调用形态。

离线可运行（讲解 + 演示）。
"""


def tool_schema():
    print("一个工具的结构（tools/list 会返回它）：\n")
    tool = {
        "name": "write_file",
        "description": "向指定路径写入文本内容",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的内容"},
            },
            "required": ["path", "content"],
        },
    }
    # 用 JSON 排印
    import json
    print(json.dumps(tool, ensure_ascii=False, indent=2))


def key_points():
    print("\n关键特性：\n")
    rows = [
        ("name", "唯一标识，供 tools/call 调用"),
        ("description", "告诉模型『何时该用、怎么用』——越清楚越好"),
        ("inputSchema", "JSON Schema 描述参数，让模型知道怎么填"),
        ("副作用", "工具通常会产生效果，因此客户端常需用户授权"),
    ]
    for k, v in rows:
        print(f"  · {k:<12}{v}")


def call_example():
    print("\ntools/call 调用形态：\n")
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "write_file",
            "arguments": {"path": "/tmp/note.txt", "content": "hello mcp"},
        },
    }
    import json
    print(json.dumps(req, ensure_ascii=False, indent=2))
    print("\n  Server 执行后返回 result（含内容与是否 isError）。")


def main():
    print(">> Tools 详解\n")
    tool_schema()
    key_points()
    call_example()
    print("\n  tips: description 决定模型『会不会用、何时用』，要多写场景。")


if __name__ == "__main__":
    main()