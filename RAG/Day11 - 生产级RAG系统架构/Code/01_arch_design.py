# -*- coding: utf-8 -*-
"""
文件用途：Day11 - 01 生产架构骨架
演示"离线数据管道(ingest)"与"在线检索服务(serve)"分离的目录与调用结构，
并给一个可运行的最小骨架。

运行：python 01_arch_design.py（无需联网）
"""


class IngestionPipeline:
    """离线管道：加载→切块→嵌入→入库（此处模拟，仅打点）。"""
    def __init__(self):
        self.vectors = []

    def process(self, docs):
        print("[ingest] 开始批量处理文档...")
        for i, d in enumerate(docs):
            chunks = self._chunk(d)
            vecs = self._embed(chunks)
            self.vectors.extend(vecs)
            print(f"  · {d[:20]}... → {len(chunks)} 块")
        print(f"[ingest] 完成，共入库 {len(self.vectors)} 个向量")
        return self.vectors

    def _chunk(self, text):
        # 简化切块
        return [text[i:i+10] for i in range(0, len(text), 10)] or [text]

    def _embed(self, chunks):
        return [(c, len(c)) for c in chunks]


class RetrieveServe:
    """在线服务：查询→检索→返回（此处模拟）。"""
    def __init__(self, index):
        self.index = index

    def query(self, question):
        print("[serve] 收到查询：", question)
        qwords = set(question)
        best = max(self.index, key=lambda v: sum(c in v[0] for c in qwords))
        print(f"[serve] 最相关块：{best[0]}")
        # 真实中继续重排 + 生成
        return best[0]


def main() -> None:
    print("===== 索引与检索解耦骨架 =====\n")
    pipe = IngestionPipeline()
    docs = [
        "报销需在出差结束后5个工作日内提交申请，附有效发票。",
        "住宿每日上限500元，超出部分自理。",
    ]
    index = pipe.process(docs)

    serve = RetrieveServe(index)
    serve.query("住宿能报销多少啊？")
    print("\n结论：离线管道负责进库（可慢/批量/重试），在线服务只做查询（要快/高并发）。")


if __name__ == "__main__":
    main()