# -*- coding: utf-8 -*-
"""
ollama_util.py - Ollama 双模式共享工具（Day08 工具调用版）

在 Day07 版基础上支持：
- real_chat_with_tools()：把 tools 定义传给 /api/chat，返回可能的 tool_calls
- SimOllama 规则模拟工具调用（无环境兜底）

有 Ollama + 支持 tools 的模型（qwen2.5/llama3.1 等）-> 真实调用；
无 -> 按规则模拟"模型想调工具"的过程。
"""

import json
import urllib.request

DEFAULT_HOST = "http://127.0.0.1:11434"


def _server_alive(host: str = DEFAULT_HOST, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"{host}/", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def list_local_models(host: str = DEFAULT_HOST) -> list[str]:
    if not _server_alive(host):
        return []
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2) as r:
            data = json.loads(r.read().decode())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def is_ollama_available(model: str = "llama3.1", host: str = DEFAULT_HOST) -> bool:
    if not _server_alive(host):
        return False
    models = list_local_models(host)
    norm = model.split(":")[0].split("/")[-1]
    return any(m.split(":")[0].split("/")[-1] == norm for m in models)


def _post(path: str, payload: dict, host: str = DEFAULT_HOST) -> dict:
    req = urllib.request.Request(
        f"{host}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def real_chat_with_tools(model: str, messages: list[dict], tools: list[dict],
                         options: dict | None = None) -> dict:
    """真实调用 /api/chat 并传 tools；返回完整响应 dict"""
    return _post("/api/chat", {
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": False,
        "options": options or {},
    })


# ---- 工具 schema 常量 ----
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，如 北京"}
            },
            "required": ["city"],
        },
    },
}