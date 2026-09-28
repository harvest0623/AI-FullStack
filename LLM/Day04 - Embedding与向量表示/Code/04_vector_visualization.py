# 文件用途：向量降维可视化
# 用 sklearn 的 t-SNE / PCA 将高维 Embedding 降到 2D/3D，
# 打印可视化数据（可复制到图表工具查看），展示同类文本聚类效果。
# 依赖：pip install openai python-dotenv numpy scikit-learn
# 需在 .env 配置 OPENAI_API_KEY
# 体现 AISearch 项目 embedding/ 中「向量编码」的可视化分析能力。

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

try:
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
except ImportError:
    print("缺少依赖 scikit-learn，请执行: pip install scikit-learn")
    sys.exit(1)

load_dotenv()


# 三个类别的文本（动物 / 食物 / 科技），用于观察聚类
SAMPLES: list[tuple[str, str]] = [
    # 类别: 动物
    ("动物", "猫是一种常见的宠物"),
    ("动物", "狗是人类最忠诚的朋友"),
    ("动物", "兔子喜欢吃胡萝卜"),
    ("动物", "老虎是森林之王"),
    # 类别: 食物
    ("食物", "苹果富含维生素"),
    ("食物", "面条是常见的主食"),
    ("食物", "牛奶含有丰富的蛋白质"),
    ("食物", "面包由面粉烘焙而成"),
    # 类别: 科技
    ("科技", "Python 是流行的编程语言"),
    ("科技", "深度学习依赖神经网络"),
    ("科技", "Transformer 是大模型的基础"),
    ("科技", "向量数据库支持相似度检索"),
]


def get_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> np.ndarray:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("未配置 OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
    resp = client.embeddings.create(model=model, input=texts)
    data = sorted(resp.data, key=lambda x: x.index)
    return np.array([d.embedding for d in data], dtype=np.float32)


def reduce_pca(vecs: np.ndarray, dim: int = 2) -> np.ndarray:
    """PCA 线性降维，保留方差最大的方向。"""
    return PCA(n_components=dim).fit_transform(vecs)


def reduce_tsne(vecs: np.ndarray, dim: int = 2) -> np.ndarray:
    """t-SNE 非线性降维，保留局部结构，适合可视化。"""
    # perplexity 需小于样本数
    perplexity = max(2, min(5, len(vecs) - 1))
    return TSNE(n_components=dim, perplexity=perplexity, random_state=42,
                init="random").fit_transform(vecs)


def print_2d(coords: np.ndarray, labels: list[str], texts: list[str], method: str) -> None:
    print(f"\n--- {method} 2D 降维结果（可复制到 Excel/图表工具绘制散点图）---")
    print(f"  {'x':<12}{'y':<12}{'类别':<8}{'文本'}")
    for (x, y), label, text in zip(coords, labels, texts):
        print(f"  {x:<12.4f}{y:<12.4f}{label:<8}{text}")


def print_3d(coords: np.ndarray, labels: list[str], texts: list[str], method: str) -> None:
    print(f"\n--- {method} 3D 降维结果 ---")
    print(f"  {'x':<12}{'y':<12}{'z':<12}{'类别':<8}{'文本'}")
    for (x, y, z), label, text in zip(coords, labels, texts):
        print(f"  {x:<12.4f}{y:<12.4f}{z:<12.4f}{label:<8}{text}")


def demo() -> None:
    print("=" * 60)
    print("向量降维可视化演示（PCA / t-SNE）")
    print("=" * 60)
    texts = [t for _, t in SAMPLES]
    labels = [c for c, _ in SAMPLES]

    print(f"\n样本数: {len(texts)}，类别: {sorted(set(labels))}")
    vecs = get_embeddings(texts)
    print(f"原始向量维度: {vecs.shape[1]}")

    # PCA 2D / 3D
    pca2 = reduce_pca(vecs, 2)
    print_2d(pca2, labels, texts, "PCA")
    pca3 = reduce_pca(vecs, 3)
    print_3d(pca3, labels, texts, "PCA")

    # t-SNE 2D
    tsne2 = reduce_tsne(vecs, 2)
    print_2d(tsne2, labels, texts, "t-SNE")

    print("\n" + "=" * 60)
    print("可视化分析建议")
    print("=" * 60)
    print("1. 把上方 (x, y, 类别, 文本) 数据复制到 Excel / 在线图表工具")
    print("2. 按「类别」着色绘制散点图，观察同类文本是否聚在一起")
    print("3. 预期：动物/食物/科技三类应分别聚成簇，说明 Embedding 捕捉了语义")
    print("4. PCA 保留全局方差结构；t-SNE 更强调局部聚类，可视化效果通常更好")
    print("\n推荐可视化工具：")
    print("- 在线：Plotly Chart Studio、matplotlib（本地）")
    print("- 交互式：TensorFlow Embedding Projector (projector.tensorflow.org)")
    print("- Python：matplotlib + seaborn 绘制散点图")


if __name__ == "__main__":
    demo()
