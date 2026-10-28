# -*- coding: utf-8 -*-
"""
ollama_util.py - Ollama 双模式共享工具（Day09）
本日主要用于检测环境（is_ollama_available / list_local_models），
供 04_multi_framework.py 判断真实接入是否可行。
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