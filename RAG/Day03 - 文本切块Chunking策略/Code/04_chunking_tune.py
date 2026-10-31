# -*- coding: utf-8 -*-
"""
文件用途：Day03 - 04 chunk_size 与 chunk_overlap 参数调优
量化对比不同 chunk_size / overlap 下的块数与语义覆盖，
帮助你建立"参数 ↔ 成本/粒度"的直觉。

运行：python 04_chunking_tune.py（无需联网）
依赖：langchain-text-splitters
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 生成一段较长且带结构的文本
TEXT = "\n\n".join(
    f"第{i}条条款：关于某业务规则，请员工严格遵守。"
    f"补充说明包括第一条细则、第二条细则与第三条例外情况，具体操作以最新版本为准。"
    for i in range(20)
)


def run(size: int, overlap: int) -> None:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap,
        separators=["\n\n", "\n", "；", "。", "，", " ", ""],
    )
    chunks = splitter.split_text(TEXT)
    avg = sum(len(c) for c in chunks) / len(chunks)
    print(f"size={size:>4} overlap={overlap:>3} → 块数={len(chunks):>3} "
          f"平均块长={avg:6.1f} 覆盖跨度≈{len(chunks) * (size - overlap)}")


def main() -> None:
    print("原始文本长度：", len(TEXT))
    print("-" * 70)
    print("chunk_size 拉伸对比（overlap=20）：")
    for size in (100, 300, 500, 800):
        run(size, 20)
    print("-" * 70)
    print("overlap 对比（chunk_size=300）：")
    for overlap in (0, 30, 60):
        run(300, overlap)
    print("-" * 70)
    print("结论：size 越大块越少、成本越低但颗粒越粗；overlap 越大保留边界信息越充分。")


if __name__ == "__main__":
    main()