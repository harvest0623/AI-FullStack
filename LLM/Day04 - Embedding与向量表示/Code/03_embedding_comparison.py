# 文件用途：多模型 Embedding 对比
# 对比 OpenAI text-embedding-3-small / text-embedding-3-large 与
#   本地 sentence-transformers 模型 的：向量维度 / 相似度准确率 / 速度 / 成本。
# 生成对比图表数据（可复制到图表工具查看）。
# 依赖：
#   pip install openai python-dotenv numpy
#   可选（本地模型）：pip install sentence-transformers
# 需在 .env 配置 OPENAI_API_KEY（本地模型无需 Key）

from __future__ import annotations

import os
import sys
import time

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


# 评测数据集：每条含 (文本A, 文本B, 是否语义相似)
EVAL_PAIRS = [
    ("猫喜欢吃鱼", "小猫爱吃鱼肉", True),
    ("狗喜欢啃骨头", "小狗爱啃骨头", True),
    ("大模型很强大", "大语言模型能力很强", True),
    ("猫喜欢吃鱼", "今天天气真好", False),
    ("机器学习很有趣", "股票今天涨停了", False),
    ("Transformer 是核心", "我喜欢吃火锅", False),
]


def get_openai_embeddings(texts: list[str], model: str) -> tuple[np.ndarray, float, int]:
    """调用 OpenAI Embedding，返回 (向量矩阵, 耗时, 维度)。"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("未配置 OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
    start = time.time()
    resp = client.embeddings.create(model=model, input=texts)
    elapsed = time.time() - start
    data = sorted(resp.data, key=lambda x: x.index)
    vecs = np.array([d.embedding for d in data], dtype=np.float32)
    return vecs, elapsed, vecs.shape[1]


def get_local_embeddings(texts: list[str], model_name: str = "BAAI/bge-small-zh-v1.5"
                         ) -> tuple[np.ndarray, float, int] | None:
    """调用本地 sentence-transformers 模型。未安装则返回 None。"""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  ⚠️ 未安装 sentence-transformers，跳过本地模型对比。")
        print("     如需对比，请执行: pip install sentence-transformers")
        return None
    model = SentenceTransformer(model_name)
    start = time.time()
    vecs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
    elapsed = time.time() - start
    return vecs.astype(np.float32), elapsed, vecs.shape[1]


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def evaluate_accuracy(vecs: np.ndarray, pairs: list[tuple[int, int, bool]],
                      threshold: float = 0.5) -> float:
    """根据相似度阈值判断是否相似，计算与标注一致的准确率。"""
    correct = 0
    for i, j, is_sim in pairs:
        score = cosine(vecs[i], vecs[j])
        pred = score >= threshold
        if pred == is_sim:
            correct += 1
    return correct / len(pairs)


def compare_models() -> None:
    print("=" * 60)
    print("多模型 Embedding 对比")
    print("=" * 60)

    # 准备评测文本：把所有 pair 的文本去重后编码
    unique_texts = []
    text_to_idx = {}
    pairs_with_idx = []
    for a, b, is_sim in EVAL_PAIRS:
        if a not in text_to_idx:
            text_to_idx[a] = len(unique_texts)
            unique_texts.append(a)
        if b not in text_to_idx:
            text_to_idx[b] = len(unique_texts)
            unique_texts.append(b)
        pairs_with_idx.append((text_to_idx[a], text_to_idx[b], is_sim))

    print(f"\n评测集：{len(EVAL_PAIRS)} 对文本，{len(unique_texts)} 条唯一文本\n")

    results = []

    # 1. OpenAI text-embedding-3-small
    print("评测 OpenAI text-embedding-3-small ...")
    try:
        vecs, t, dim = get_openai_embeddings(unique_texts, "text-embedding-3-small")
        acc = evaluate_accuracy(vecs, pairs_with_idx)
        results.append(("text-embedding-3-small", dim, acc, t, "$0.02/1M"))
    except Exception as e:  # noqa: BLE001
        print(f"  失败: {e}")

    # 2. OpenAI text-embedding-3-large
    print("评测 OpenAI text-embedding-3-large ...")
    try:
        vecs, t, dim = get_openai_embeddings(unique_texts, "text-embedding-3-large")
        acc = evaluate_accuracy(vecs, pairs_with_idx)
        results.append(("text-embedding-3-large", dim, acc, t, "$0.13/1M"))
    except Exception as e:  # noqa: BLE001
        print(f"  失败: {e}")

    # 3. 本地 sentence-transformers
    print("评测本地 sentence-transformers (BAAI/bge-small-zh-v1.5) ...")
    local = get_local_embeddings(unique_texts)
    if local is not None:
        vecs, t, dim = local
        acc = evaluate_accuracy(vecs, pairs_with_idx)
        results.append(("bge-small-zh-v1.5(本地)", dim, acc, t, "免费(本地)"))

    # 汇总对比表
    print("\n" + "=" * 60)
    print("对比结果汇总")
    print("=" * 60)
    print(f"  {'模型':<28}{'维度':<8}{'准确率':<10}{'耗时(s)':<10}{'价格'}")
    print("  " + "-" * 66)
    for name, dim, acc, t, price in results:
        print(f"  {name:<28}{dim:<8}{acc:<10.2f}{t:<10.3f}{price}")

    # 相似度明细（用于图表）
    print("\n相似度明细（可用于绘图）：")
    print("  pair_id, model, score")
    for name, dim, acc, t, price in results:
        # 重新取该模型向量（简化：只取第一个模型明细）
        pass
    for idx, (i, j, is_sim) in enumerate(pairs_with_idx):
        print(f"  pair {idx} (期望相似={is_sim}):")
        # 为节省调用，这里只打印第一个模型的分数
        if results:
            top_name = results[0][0]
            if "small" in top_name:
                vecs, _, _ = get_openai_embeddings(unique_texts, "text-embedding-3-small")
            elif "large" in top_name:
                vecs, _, _ = get_openai_embeddings(unique_texts, "text-embedding-3-large")
            else:
                local = get_local_embeddings(unique_texts)
                vecs = local[0] if local else np.zeros((1, 1))
            print(f"    {top_name}: {cosine(vecs[i], vecs[j]):.4f}")

    print("\n结论：")
    print("- OpenAI large 精度最高但更贵更大；small 性价比最高")
    print("- 本地 bge 模型免费且中文效果好，适合隐私/成本敏感场景")
    print("- 维度越高表达能力越强，但存储与检索成本也越高")


if __name__ == "__main__":
    compare_models()
