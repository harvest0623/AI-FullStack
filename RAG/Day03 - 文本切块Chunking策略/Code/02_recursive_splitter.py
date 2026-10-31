# -*- coding: utf-8 -*-
"""
文件用途：Day03 - 02 递归字符切块
演示 RecursiveCharacterTextSplitter：按优先级从高到低的分隔符递归切，
尽量把切点放在语义自然边界（段落/句/分号）。

运行：python 02_recursive_splitter.py（无需联网）
依赖：langchain-text-splitters
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


TEXT = """DataIQ 员工制度手册

第一章 报销规则
差旅报销需在出差结束后五个工作日内提交；住宿每日上限五百元；升级舱位需提前向直属经理邮件申请获准。

第二章 年假规则
DataIQ 提供每年十五天带薪年假，入职满一年即可领取；年假需提前三天在 HR 系统提交；不允许跨年累计。

第三章 支付规则
支持支付宝、微信支付、对公转账与云闪付；不支持货到付款。
"""


def main() -> None:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=80,
        chunk_overlap=10,
        separators=["\n\n", "\n", "；", "。", "，", " ", ""],
    )
    chunks = splitter.split_text(TEXT)

    print(f"共 {len(chunks)} 块（chunk_size=80, overlap=10）：\n")
    for i, c in enumerate(chunks, 1):
        print(f"--- 块{i} (len={len(c)}) ---")
        print(c)
        print()


if __name__ == "__main__":
    main()