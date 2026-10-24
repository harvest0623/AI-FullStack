# -*- coding: utf-8 -*-
"""
Day01 - 01 Ollama 是什么：架构、定位与使用方式
"""


def show_architecture():
    """展示 Ollama 的三层架构"""
    print("=" * 62)
    print("Ollama 三层架构")
    print("=" * 62)
    print("""
┌────────────┐    CLI / REST / SDK    ┌────────────────┐
│  Client    │ ───────────────────▶  │  Ollama Server │
│ (ollama/   │   HTTP 127.0.0.1:11434│  (服务进程)     │
│  requests/ │                        └───────┬────────┘
│  ollama库) │                               │ 加载/推理
└────────────┘                       ┌───────▼────────┐
                                     │   模型仓库      │
                                     │ ~/.ollama/     │
                                     └────────────────┘
""")
    layers = [
        ("Client", "命令/程序发起请求；三态：CLI、REST API、Python SDK"),
        ("Server", "常驻进程；模型加载、推理调度、并发管理"),
        ("Model", "模型二进制文件存于本机 ~/.ollama/models，可多个并存"),
    ]
    for name, desc in layers:
        print(f"  {name:<8} {desc}")
    print()


def show_usage_ways():
    """三种使用方式（间接程度递增）"""
    print("=" * 62)
    print("三种使用方式：对应与 Server 交互的三种距离")
    print("=" * 62)
    ways = [
        ("CLI", "ollama run llama3.1 \"你好\"", "人类手动交互，体验模型"),
        ("REST API", "POST /api/chat", "程序化调用，最灵活（Day03）"),
        ("Python SDK", "ollama.chat(...)", "Pythonic 封装，最简洁（Day04）"),
    ]
    for name, cmd, desc in ways:
        print(f"  [{name:<9}] {cmd}")
        print(f"              ↑ {desc}")
        print()
    print("底层都是走 HTTP（127.0.0.1:11434），SDK 只是请求的封装。\n")


def show_models():
    """常见的可托管开源模型清单"""
    print("=" * 62)
    print("Ollama 可托管的常见开源模型")
    print("=" * 62)
    models = [
        ("llama3.1", "Meta", "通用英文对话/指令", "4.7GB"),
        ("qwen2.5", "阿里", "通用中文对话", "1.5GB(B)/4.7GB(7B)"),
        ("codellama", "Meta", "代码生成/补全", "3.8GB(7B)"),
        ("nomic-embed-text", "Nomic", "文本嵌入（RAG 用）", "274MB"),
        ("llava", "多家", "视觉-语言（图问答）", "4.7GB"),
        ("mistral", "Mistral", "轻量通用对话", "4.1GB"),
    ]
    print(f"{'模型名':<16}{'出品方':<10}{'用途':<20}{'体积'}")
    for name, org, use, size in models:
        print(f"{name:<16}{org:<10}{use:<20}{size}")
    print("\n拉取：ollama pull <模型名>   交互：ollama run <模型名>")


def main():
    print(">>> 本模块无 Ollama 环境也运行（纯文本/结构演示）\n")
    show_architecture()
    show_usage_ways()
    show_models()


if __name__ == "__main__":
    main()