# -*- coding: utf-8 -*-
"""
ollama_util.py - Ollama 双模式共享工具（Day10 综合版）

整合前面多天能力：
- chat / embed / tools 三种调用
- 双模式：真实 Ollama 或 SimOllama 模拟
供综合实战的客服 Agent 使用。
"""

import json
import math
import urllib.request

DEFAULT_HOST = "http://127.0.0.1:11434"
MODEL = "llama3.1"
EMBED_MODEL = "nomic-embed-text"


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


def is_ollama_available(model: str = MODEL, host: str = DEFAULT_HOST) -> bool:
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


def real_chat(messages: list[dict], options: dict | None = None,
              model: str = MODEL) -> str:
    resp = _post("/api/chat", {"model": model, "messages": messages,
                               "stream": False, "options": options or {}})
    return resp.get("message", {}).get("content", "").strip()


def real_embed(input_text: str | list[str], model: str = EMBED_MODEL) -> list:
    resp = _post("/api/embed", {"model": model, "input": input_text})
    embs = resp.get("embeddings", [])
    if isinstance(input_text, str):
        return embs[0] if embs else []
    return embs


def cos_sim(a, b):
    if not a or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


# ---------- 模拟层 ----------
class SimOllama:
    @staticmethod
    def chat(messages: list[dict], options: dict | None = None) -> str:
        user = next((m["content"] for m in reversed(messages)
                     if m.get("role") == "user"), "")
        return f"[SimOllama] 客服模拟作答：收到「{user}」（离线教学）"

    @staticmethod
    def embed(text: str) -> list:
        vec = [0.0] * 64
        for i, ch in enumerate(text):
            vec[i % 64] += (ord(ch) % 100) / 100.0
        norm = (sum(v * v for v in vec) ** 0.5) or 1.0
        return [v / norm for v in vec]


def chat_wrapper(messages: list[dict], options: dict | None = None, verbose=False) -> str:
    if is_ollama_available(MODEL):
        if verbose:
            print("  [模式] 真实 Ollama")
        return real_chat(messages, options)
    if verbose:
        print("  [模式] SimOllama")
    return SimOllama.chat(messages, options)


def embed_wrapper(text: str | list[str], verbose=False) -> list:
    if is_ollama_available(EMBED_MODEL):
        if verbose:
            print("  [模式] 真实嵌入")
        return real_embed(text)
    if isinstance(text, list):
        return [SimOllama.embed(t) for t in text]
    return SimOllama.embed(text)