# -*- coding: utf-8 -*-
"""
Day02 - 02 查看模型详情（ollama show）

展示模型元信息字段的语义，并演示如何解析（真实环境走 /api/show）。
"""

import json
import urllib.request

# 模型元信息的"字段 -> 含义"字典
FIELD_MEANING = {
    "architecture": "模型架构（llama/qwen/mistral 等）",
    "parametersize": "参数量（如 8.0B）",
    "context length": "最大上下文长度（token）",
    "embedding length": "嵌入向量维度",
    "quantization": "量化方式（如 Q4_K_M）",
    "capabilities": "能力（completion/vision/embedding 等）",
    "parameters": "模型默认采样参数",
    "modified_at": "最后修改时间",
    "size": "磁盘占用大小",
}


def real_show(model="llama3.1"):
    """真实环境：调 /api/show"""
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/show",
            data=json.dumps({"model": model}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def demo_show_data():
    """无环境时用的示例元信息"""
    return {
        "model": "llama3.1:latest",
        "architecture": "llama",
        "parametersize": "8.0B",
        "contextlength": 131072,
        "embeddinglength": 4096,
        "quantization": "Q4_K_M",
        "capabilities": ["completion"],
        "parameters": {"temperature": 0.0, "top_p": 0.9, "num_ctx": 4096},
        "modified_at": "2026-09-10T08:00:00",
        "size": 4693779555,
    }


def format_size(n):
    if n >= 1 << 30:
        return f"{n / (1<<30):.2f}GB"
    if n >= 1 << 20:
        return f"{n / (1<<20):.1f}MB"
    return f"{n} B"


def render(info: dict):
    if not info:
        print("  未获取到模型信息")
        return
    print(f"  模型：{info.get('model', '?')}")
    print("-" * 60)
    for field, meaning in FIELD_MEANING.items():
        val = info.get(field)
        if isinstance(val, (dict, list)):
            val = json.dumps(val, ensure_ascii=False)
        if field == "size" and val:
            val = f"{format_size(int(val))}"
        if field == "context length":
            val = info.get("contextlength", val)
        print(f"  {field:<18} {val}")
        print(f"      ↳ 含义：{meaning}")


def main():
    print("=" * 60)
    print("01 模型详情 ollama show")
    print("=" * 60)
    if real_show():
        render(real_show())
        print("\n [真实环境] 数据来自 /api/show")
    else:
        render(demo_show_data())
        print("\n [模拟数据] 安装 Ollama 并 pull 模型后显示真实元信息")

    print("\n" + "=" * 60)
    print("02 关于参数量与内存")
    print("=" * 60)
    print("  8B 模型在不同量化下的近似内存：")
    rows = [("FP16", 16), ("Q8", 8), ("Q4_K_M", 4)]
    for name, bits in rows:
        bytes_ = 8e9 * (bits / 8) if False else 8000000000 * bits / 8  # ~8e9 参数 * bits/8
        print(f"   {name:<8} ≈ {bytes_/1e9:.1f} GB")
    print("  结论：Q4 量化省一半内存，是做本地应用的主流选择。")


if __name__ == "__main__":
    main()