# -*- coding: utf-8 -*-
"""
文件用途：Day12 - 01 项目骨架
生成 DataIQ RAG 系统的最小模块结构（便于线上建包）。

运行：python 01_project_structure.py（无需联网）
"""

import os

STRUCTURE = [
    "src/config.py",
    "src/loaders.py",
    "src/chunker.py",
    "src/embedder.py",
    "src/store.py",
    "src/retriever.py",
    "src/router.py",
    "src/generator.py",
    "src/cache.py",
    "src/evaluate.py",
    "src/api.py",
    "data/README.md",
    "scripts/ingest.py",
    "scripts/evaluate.py",
    "requirements.txt",
]


def main() -> None:
    base = "dataiq"
    print("创建项目骨架：")
    files = []
    for rel in STRUCTURE:
        path = os.path.join(base, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
        files.append(path)
    # 补 __init__.py
    os.makedirs(os.path.join(base, "src"), exist_ok=True)
    init_path = os.path.join(base, "src", "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("")
    files.append(init_path)
    print(f"  ✓ 已生成 {len(files)} 个文件/目录（位于 {base}/）")
    print("\n模块职责速览：")
    print("  config: 配置  | loaders: 加载  | chunker: 切块  | embedder: 嵌入")
    print("  store: 向量库  | retriever: 混合检索+重排  | router: 路由")
    print("  generator: 生成  | cache: 缓存  | evaluate: 评估  | api: FastAPI")


if __name__ == "__main__":
    main()