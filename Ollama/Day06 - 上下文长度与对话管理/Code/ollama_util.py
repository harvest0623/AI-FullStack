# -*- coding: utf-8 -*-
"""
ollama_util.py - Ollama 双模式共享工具（Day06 版）

统一提供：
1. is_ollama_available(model)  检测本机 Ollama 服务 + 指定模型是否可用
2. SimOllama                   内置模拟器（无环境时自动退化）
3. chat_wrapper() / real_chat()  封装 switch 逻辑

说明：
- 有真实 Ollama 环境 -> 走 urllib 调用 127.0.0.1:11434，返回真实模型输出
- 无环境            -> SimOllama 按规则模拟响应，保证离线可运行

仅供教学复用。
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


def real_chat(model: str, messages: list[dict], options: dict | None = None) -> str:
    resp = _post("/api/chat", {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options or {},
    })
    return resp.get("message", {}).get("content", "").strip()


class SimOllama:
    @staticmethod
    def chat(model: str, messages: list[dict], options: dict | None = None) -> str:
        user_text = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        temp = (options or {}).get("temperature", 0.7)
        return (f"[SimOllama:{model}] 已收到你的提问：「{user_text}」。"
                f"（模拟响应 @temperature={temp:.2f}，请安装 Ollama 后查看真实输出）")


def chat_wrapper(model: str, messages: list[dict], options: dict | None = None,
                 verbose: bool = False) -> str:
    if is_ollama_available(model):
        if verbose:
            print(f"  [模式] 真实 API（模型 {model} 已就绪）")
        return real_chat(model, messages, options)
    if verbose:
        print(f"  [模式] SimOllama 模拟（模型 {model} 未就绪或未安装 Ollama）")
    return SimOllama.chat(model, messages, options)