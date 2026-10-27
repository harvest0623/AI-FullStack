# -*- coding: utf-8 -*-
"""
ollama_util.py - Ollama 双模式共享工具（Day07 嵌入版）

在 Day06 版基础上新增：
- real_embed() / embed_wrapper()：真实与模拟嵌入
- SimOllama.embed()：字符统计伪向量

有 Ollama + 嵌入模型 -> 真实嵌入；无 -> 规则伪向量（结构与余弦相似度逻辑仍可演示）。
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


def real_embed(model: str, input_text: str | list[str]) -> list:
    """真实调用 /api/embed；单文本返回第一个嵌入，列表返回全部"""
    resp = _post("/api/embed", {"model": model, "input": input_text})
    embs = resp.get("embeddings", [])
    if isinstance(input_text, str):
        return embs[0] if embs else []
    return embs


class SimOllama:
    @staticmethod
    def embed(model: str, input_text: str) -> list:
        """字符统计伪向量（维度 64），仅供演示嵌入结构"""
        vec = [0.0] * 64
        for i, ch in enumerate(input_text):
            vec[i % 64] += (ord(ch) % 100) / 100.0
        norm = (sum(v * v for v in vec) ** 0.5) or 1.0
        return [v / norm for v in vec]


def embed_wrapper(model: str, input_text: str | list[str], verbose: bool = False) -> list:
    if is_ollama_available(model):
        if verbose:
            print(f"  [模式] 真实 API（嵌入模型 {model}）")
        return real_embed(model, input_text)
    if verbose:
        print(f"  [模式] SimOllama 模拟嵌入（{model}）")
    if isinstance(input_text, list):
        return [SimOllama.embed(model, t) for t in input_text]
    return SimOllama.embed(model, input_text)