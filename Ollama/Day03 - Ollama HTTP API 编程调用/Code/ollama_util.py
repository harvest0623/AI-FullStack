# -*- coding: utf-8 -*-
"""
ollama_util.py - Ollama 双模式共享工具

统一提供：
1. is_ollama_available(model)  检测本机 Ollama 服务 + 指定模型是否可用
2. SimOllama                   内置模拟器（无环境时自动退化）
3. chat_wrapper() / embed_wrapper() 封装 switch 逻辑

说明：
- 有真实 Ollama 环境 -> 走 requests 调用 127.0.0.1:11434，返回真实模型输出
- 无环境            -> SimOllama 按规则模拟响应，保证离线可运行

仅供教学复用，本板块各天共用此思路。
"""

import json
import urllib.request
import urllib.error

DEFAULT_HOST = "http://127.0.0.1:11434"


# ============================================================
# 1. 环境检测
# ============================================================

def _server_alive(host: str = DEFAULT_HOST, timeout: float = 1.0) -> bool:
    """探测 Ollama 服务是否存活"""
    try:
        with urllib.request.urlopen(f"{host}/", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def list_local_models(host: str = DEFAULT_HOST) -> list[str]:
    """列出本地已安装的模型名列表（无环境返回空列表）"""
    if not _server_alive(host):
        return []
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2) as r:
            data = json.loads(r.read().decode())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def is_ollama_available(model: str = "llama3.1", host: str = DEFAULT_HOST) -> bool:
    """主检测函数：服务存活且指定模型已拉取？"""
    if not _server_alive(host):
        return False
    models = list_local_models(host)
    # 允许多种标签写法（llama3.1 / llama3.1:latest / ollama.com/library/llama3.1）
    norm = model.split(":")[0].split("/")[-1]
    return any(m.split(":")[0].split("/")[-1] == norm for m in models)


# ============================================================
# 2. 真实 API 调用（供启用环境时使用）
# ============================================================

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
    """真实调用 /api/chat，返回助手回复文本"""
    resp = _post("/api/chat", {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options or {},
    })
    return resp.get("message", {}).get("content", "").strip()


def real_embed(model: str, input_text: str | list[str]) -> list:
    """真实调用 /api/embed，返回向量（单文本返回第一个嵌入）"""
    resp = _post("/api/embed", {"model": model, "input": input_text})
    embs = resp.get("embeddings", [])
    if isinstance(input_text, str):
        return embs[0] if embs else []
    return embs


# ============================================================
# 3. SimOllama 模拟器
# ============================================================

class SimOllama:
    """
    无 Ollama 环境时的规则模拟器。
    接口与真实 Ollama 对齐，返回可预期的教学文本。
    """

    @staticmethod
    def chat(model: str, messages: list[dict], options: dict | None = None) -> str:
        user_text = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        temp = (options or {}).get("temperature", 0.7)
        return (f"[SimOllama:{model}] 已收到你的提问：「{user_text}」。"
                f"（模拟响应 @temperature={temp:.2f}，请安装 Ollama 后查看真实输出）")

    @staticmethod
    def generate(model: str, prompt: str, options: dict | None = None) -> str:
        return (f"[SimOllama:{model}] 对文本「{prompt[:40]}...」的模拟生成结果。"
                f"（离线教学模式）")

    @staticmethod
    def embed(model: str, input_text: str) -> list:
        """用简单的字符统计生成一个伪向量（维度=64），仅供演示结构"""
        vec = [0.0] * 64
        for i, ch in enumerate(input_text):
            vec[i % 64] += (ord(ch) % 100) / 100.0
        # 归一化
        norm = (sum(v * v for v in vec) ** 0.5) or 1.0
        return [v / norm for v in vec]


# ============================================================
# 4. 统一封装（推荐使用）
# ============================================================

def chat_wrapper(model: str, messages: list[dict], options: dict | None = None,
                 verbose: bool = False) -> str:
    """
    推荐入口：智能选择真实/模拟。
    verbose=True 时打印当前模式，便于教学观察。
    """
    if is_ollama_available(model):
        if verbose:
            print(f"  [模式] 真实 API（模型 {model} 已就绪）")
        return real_chat(model, messages, options)
    if verbose:
        print(f"  [模式] SimOllama 模拟（模型 {model} 未就绪或未安装 Ollama）")
    return SimOllama.chat(model, messages, options)


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