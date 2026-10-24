# -*- coding: utf-8 -*-
"""
Day03 - 01 REST API 总览：端点图谱与请求/响应结构速查

以纯文本方式展示 Ollama 全部核心端点的请求/响应骨架（教学对照表）。
"""


def endpoints_table():
    table = [
        ("/api/chat", "POST", "model, messages, stream, options", "多轮对话"),
        ("/api/generate", "POST", "model, prompt, stream, options", "单次文本生成/补全"),
        ("/api/embed", "POST", "model, input", "文本 -> 向量"),
        ("/api/tags", "GET", "—", "本地模型列表"),
        ("/api/show", "POST", "model", "模型详情"),
        ("/api/pull", "POST", "model, stream", "拉取模型"),
        ("/api/ps", "GET", "—", "已加载（内存）模型"),
    ]
    print(f"{'端点':<16}{'方法':<8}{'关键请求体':<32}{'用途'}")
    print("-" * 72)
    for ep, m, body, use in table:
        print(f"{ep:<16}{m:<8}{body:<32}{use}")


def chat_contract():
    print("\n" + "=" * 60)
    print("【/api/chat】请求与响应契约")
    print("=" * 60)
    req = {
        "model": "llama3.1",
        "messages": [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "hi"},
        ],
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 128},
    }
    res_ok = {
        "message": {"role": "assistant", "content": "你好！..."},
        "done": True,
        "total_duration": 123456789,
        "prompt_eval_count": 20,
        "eval_count": 45,
        "eval_duration": 40000000,
    }
    print("\n请求体：")
    import json
    print(json.dumps(req, ensure_ascii=False, indent=2))
    print("\n非流式响应（片段）：")
    print(json.dumps(res_ok, ensure_ascii=False, indent=2))
    print("\n  → 答案取自 message.content；eval_count/时长用于统计")


def stream_contract():
    print("\n" + "=" * 60)
    print("【流式】stream:true 响应（NDJSON，每行一个对象）")
    print("=" * 60)
    lines = [
        '{"message":{"content":"你"},"done":false}',
        '{"message":{"content":"好"},"done":false}',
        '{"message":{"content":"！"},"done":false}',
        '{"done":true,"eval_count":3,"eval_duration":12000000}',
    ]
    for ln in lines:
        print("  " + ln)
    print("  ↑ 最后一个 done:true 行带统计，作为结束标志")


def main():
    print(">>> 本文件为纯对照表，任意环境可运行\n")
    endpoints_table()
    chat_contract()
    stream_contract()


if __name__ == "__main__":
    main()