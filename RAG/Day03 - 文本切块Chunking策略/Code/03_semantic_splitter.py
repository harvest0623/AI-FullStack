# -*- coding: utf-8 -*-
"""
文件用途：Day03 - 03 语义切块
用嵌入相似度在"语义变化明显"的边界切分。与固定/递归不同，它按内容含义切，
语义更完整，但需要嵌入模型（无 Key 时用简单的字符相似度降级演示）。

运行：python 03_semantic_splitter.py
依赖：langchain-experimental langchain-openai（配置 OPENAI_API_KEY 时）
"""

import os
from dotenv import load_dotenv

load_dotenv()

TEXT = (
    "DataIQ 为全体员工提供年度体检，统一在春季进行。"
    "体检项目包括血常规、肝肾功能与超声检查。"
    "另外，公司每季度组织一次团队建设活动。"
    "团建包括户外拓展与部门聚餐，费用由公司承担。"
)


def demo_fallback_semantic_split(text: str, break_sentences: float = 0.6) -> list[str]:
    """无嵌入时的训练式降级：以句号为界，近似认为相邻句子若词汇差异大则为一处语义边界。"""
    sents = [s.strip() for s in text.replace("。", "。\n").splitlines() if s.strip()]
    chunks, cur = [], ""
    for s in sents:
        # 词汇重叠度低 → 判定为新主题边界
        old = set(cur[:-1].replace("，", "")) if cur else set()
        new = set(s.replace("，", ""))
        overlap = len(old & new) / max(len(new), 1)
        if cur and overlap < break_sentences:
            chunks.append(cur)
            cur = s
        else:
            cur += s
    if cur:
        chunks.append(cur)
    return chunks


def main() -> None:
    print("原文本：")
    print(TEXT, "\n")

    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_experimental.text_splitter import SemanticChunker
            from langchain_openai import OpenAIEmbeddings

            splitter = SemanticChunker(
                OpenAIEmbeddings(model="text-embedding-3-small"),
                breakpoint_threshold_type="percentile",
            )
            chunks = splitter.split_text(TEXT)
            print("[语义切块] 使用 OpenAI 嵌入：")
        except Exception as e:
            print(f"[!] 语义切块初始化失败，降级: {e}")
            chunks = demo_fallback_semantic_split(TEXT)
            print("[降级] 使用词汇重叠启发式：")
    else:
        print("[降级] 未配置 OPENAI_API_KEY，使用词汇重叠启发式：")
        chunks = demo_fallback_semantic_split(TEXT)

    for i, c in enumerate(chunks, 1):
        print(f"\n块{i}: {c}")


if __name__ == "__main__":
    main()