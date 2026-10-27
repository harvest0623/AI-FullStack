# -*- coding: utf-8 -*-
"""
Day07 - 03 文档切块与入库

长文档不能一次整体嵌入检索（会稀释细节），需要切块：
1. 按固定字符长度 + 重叠切块（overlap 保持上下文连续）
2. 每块单独嵌入
3. 形成 (chunk_text, vector) 的"检索池"

双模式：有嵌入模型 -> 真实向量；无 -> 伪向量兜底。
"""

from ollama_util import embed_wrapper

EMBED_MODEL = "nomic-embed-text"

# 一篇长"客服手册"片段
DOC = (
    "我们的退货政策规定，自签收之日起 7 天内可以申请无理由退货，"
    "退货时请保持商品完好并附上原包装。退款将在我们收到退货商品并确认无损后，"
    "在 3-5 个工作日内原路退回您的支付账户。若您是使用优惠券购买，"
    "退款金额将按实付金额计算，优惠券不退不换。发票请在确认收货后 30 天内申请，"
    "逾期无法补开，请务必保留订单号以便查询。我们的客服工作时间是每天 9:00-21:00，"
    "节假日不休息，若有疑问可随时联系我们。"
)


def chunk_text(text: str, size: int = 30, overlap: int = 6) -> list[str]:
    """按固定字符长度切块，块间有 overlap 保持上下文连续"""
    blocks = []
    start = 0
    n = len(text)
    while start < n:
        end = start + size
        blocks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap  # 向后回退 overlap 个字符
    return blocks


def main():
    print(">> 文档切块与入库\n")
    print(f"原始文档长度：{len(DOC)} 字符\n")

    chunks = chunk_text(DOC)
    print(f"共切成 {len(chunks)} 块（size=30, overlap=6）：")
    for i, c in enumerate(chunks):
        print(f"  [{i:>2}] ({len(c):>2}字) {c}")

    print("\n逐块嵌入入库（装入检索池）：")
    store = []
    for i, c in enumerate(chunks):
        v = embed_wrapper(EMBED_MODEL, c)
        store.append((c, v))
        print(f"  chunk[{i}] → 维度 {len(v)}")
    print(f"\n检索池就绪：{len(store)} 个块，可供 Day07-04 检索。")


if __name__ == "__main__":
    main()