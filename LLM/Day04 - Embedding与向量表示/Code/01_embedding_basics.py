# 文件用途：Embedding 基础
# 用 OpenAI Embedding API 将文本转为向量，
# 计算余弦相似度 / 欧氏距离 / 点积，
# 展示相似文本与不相关文本的相似度差异。
# 含 EmbeddingClient 类，体现 AISearch 项目 embedding/ 的封装思想。
# 依赖：pip install openai python-dotenv numpy
# 需在 .env 配置 OPENAI_API_KEY

from __future__ import annotations

import os
import sys

import numpy as np

try:
    from dotenv import load_dotenv
except ImportError:
    print("缺少依赖 python-dotenv，请执行: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("缺少依赖 openai，请执行: pip install openai")
    sys.exit(1)

load_dotenv()


class EmbeddingClient:
    """OpenAI Embedding 客户端封装。"""

    def __init__(self, model: str = "text-embedding-3-small",
                 api_key: str | None = None, base_url: str | None = None):
        self.model = model
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "未检测到 OPENAI_API_KEY，请在 .env 中配置：OPENAI_API_KEY=sk-xxx"
            )
        self.client = OpenAI(api_key=key, base_url=base_url or os.getenv("OPENAI_BASE_URL"))

    def embed(self, text: str, dimensions: int | None = None) -> np.ndarray:
        """将单段文本编码为向量。dimensions 可降维（如 1536->256）。"""
        kwargs = {"model": self.model, "input": text}
        if dimensions:
            kwargs["dimensions"] = dimensions
        resp = self.client.embeddings.create(**kwargs)
        return np.array(resp.data[0].embedding, dtype=np.float32)

    def embed_batch(self, texts: list[str], dimensions: int | None = None) -> np.ndarray:
        """批量编码（OpenAI 单次最多支持较多条目，这里按需调用）。"""
        kwargs = {"model": self.model, "input": texts}
        if dimensions:
            kwargs["dimensions"] = dimensions
        resp = self.client.embeddings.create(**kwargs)
        # 按 index 排序保证顺序
        data = sorted(resp.data, key=lambda x: x.index)
        return np.array([d.embedding for d in data], dtype=np.float32)


# ============================================================
# 相似度计算函数
# ============================================================
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """余弦相似度：cos(A,B) = A·B / (|A||B|)，范围 [-1,1]，最常用。"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """欧氏距离：||A-B||，关注绝对距离，越小越相似。"""
    return float(np.linalg.norm(a - b))


def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    """点积：A·B，简洁但受向量长度影响。归一化后 ≈ 余弦相似度。"""
    return float(np.dot(a, b))


def demo() -> None:
    print("=" * 60)
    print("Embedding 基础演示（OpenAI text-embedding-3-small）")
    print("=" * 60)
    client = EmbeddingClient()

    # 三组文本：两句语义相近、一句不相关
    texts = [
        "猫喜欢吃鱼",            # 语义相近
        "小猫爱吃鱼肉",          # 语义相近
        "今天天气真好",          # 不相关
    ]
    print("\n待比较文本：")
    for i, t in enumerate(texts):
        print(f"  [{i}] {t}")

    vecs = client.embed_batch(texts)
    print(f"\n向量维度: {vecs.shape[1]}")

    print("\n相似度对比（0-1 之间，越大越相似）:")
    print(f"  {'对比':<16}{'余弦相似度':<14}{'欧氏距离':<14}{'点积'}")
    print("  " + "-" * 56)
    pairs = [(0, 1, "猫吃鱼 vs 小猫爱吃鱼"), (0, 2, "猫吃鱼 vs 天气好"), (1, 2, "小猫爱吃鱼 vs 天气好")]
    for i, j, label in pairs:
        cos = cosine_similarity(vecs[i], vecs[j])
        euc = euclidean_distance(vecs[i], vecs[j])
        dot = dot_product(vecs[i], vecs[j])
        print(f"  {label:<16}{cos:<14.4f}{euc:<14.4f}{dot:.4f}")

    print("\n结论：")
    print("- 语义相近的文本（猫吃鱼 vs 小猫爱吃鱼）余弦相似度高")
    print("- 不相关文本（猫吃鱼 vs 天气好）余弦相似度低")
    print("- 余弦相似度最常用，因为它对向量长度不敏感")
    print("- 欧氏距离越小越相似，与余弦相似度趋势相反")

    # 演示降维
    print("\n" + "=" * 60)
    print("降维演示（dimensions 参数：1536 -> 256）")
    print("=" * 60)
    vec_small = client.embed("猫喜欢吃鱼", dimensions=256)
    print(f"  原始维度: {vecs.shape[1]} -> 降维后: {vec_small.shape[0]}")
    print("  说明：OpenAI 的 Matryoshka 表示支持降维，牺牲少量精度换取更低存储/计算成本。")


if __name__ == "__main__":
    demo()
