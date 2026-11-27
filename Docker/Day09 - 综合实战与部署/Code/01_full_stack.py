# -*- coding: utf-8 -*-
"""
Day09 - 01 完整应用栈的组合架构

组装一个"可上线的 AI 全栈应用"：前端 + 后端 + 向量库 + Ollama 模型服务。
讲清各服务职责、用 compose 如何互联、数据如何持久化。

离线可运行（纯讲解 + 命令语义）。
"""


def stack():
    print("应用栈组成（见本目录 docker-compose.yml）：\n")
    rows = [
        ("frontend", "Web 界面，对外 8080", "调用 backend"),
        ("backend", "业务/工具/RAG 编排，对外 8000", "依赖 ollama + vectorstore"),
        ("vectorstore", "向量库（如 qdrant），存知识向量", "后端检索"),
        ("ollama", "本地大模型服务，端口 11434", "被后端当底座"),
    ]
    print(f"{'服务':<14}{'职责':<30}{'依赖'}")
    print("-" * 66)
    for a, b, c in rows:
        print(f"{a:<14}{b:<30}{c}")


def flow():
    print("\n一次请求流转：")
    print("""  用户 → frontend → backend → vectorstore 检索 → ollama 生成 → 返回前端
                     │        └（RAG 得到上下文）
                     └── 可选工具调用/查库 ——› 后端再组织生成
""")


def data():
    print("\n持久化：")
    print("  · ollama_models → 模型文件持久化（不随容器删除）")
    print("  · qdrant_data  → 向量数据持久化")
    print("  · 后端若用库（mysql/pg）可再加一个 db 服务 + 卷\n")

    print("组合命令：")
    print("  docker compose up -d        # 拉起全部")
    print("  docker compose logs -f      # 跟踪日志")
    print("  docker compose down         # 停栈（保留卷）")


def main():
    print(">> 完整应用栈架构\n")
    stack()
    flow()
    data()


if __name__ == "__main__":
    main()