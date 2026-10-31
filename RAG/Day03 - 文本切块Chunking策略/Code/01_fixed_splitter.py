# -*- coding: utf-8 -*-
"""
文件用途：Day03 - 01 固定大小切块
演示最基础的按字符数固定切块，观察其在句子中"硬切"导致语义断裂的问题。

运行：python 01_fixed_splitter.py（无需联网）
依赖：langchain-text-splitters（或仅用内置函数）
"""

try:
    from langchain_text_splitters import CharacterTextSplitter
    HAS_LC = True
except ImportError:
    HAS_LC = False


TEXT = (
    "DataIQ 是金融科技企业。我们提供企业知识库问答服务。"
    "员工可以通过自然语言查询制度文档。"
    "报销规则要求出差结束后五个工作日内提交申请。"
    "住宿每天上限五百元，升级舱位需提前申请。"
    "年假每年十五天，入职满一年即可领取。"
)


def main() -> None:
    print("原始文本长度：", len(TEXT))
    print("-" * 50)

    if HAS_LC:
        splitter = CharacterTextSplitter(separator="\n", chunk_size=30, chunk_overlap=0)
        chunks = splitter.split_text(TEXT)
    else:
        # 无依赖时用内置等价实现
        chunks = [TEXT[i:i + 30] for i in range(0, len(TEXT), 30)]

    for i, c in enumerate(chunks, 1):
        print(f"块{i} (len={len(c)}): {c}")
    print("-" * 50)
    print("观察：固定长度切块可能从句子中间断开，破坏语义单元。")


if __name__ == "__main__":
    main()