"""
03_longterm_store.py
长时记忆：写入、检索（关键词 + 向量语义）、按用户/类型过滤、注入上下文。
向量检索用 numpy 模拟（复用 VectorDB 板块思想），无外部依赖。

运行：python 03_longterm_store.py
"""

import hashlib
import numpy as np


# ---------------------------------------------------------------------------
# 语义向量化（哈希词袋；真实项目接 Embedding 模型）
# ---------------------------------------------------------------------------
def embed(text: str, dim: int = 128) -> np.ndarray:
    """词袋 + 中文字符 bigram 哈希向量（真实项目接 Embedding 模型）。"""
    vec = np.zeros(dim, dtype=np.float32)
    tokens = str(text).split()                      # 英文/空格分词
    compact = "".join(tokens)
    for i in range(len(compact) - 1):              # 字符 bigram（适配中文）
        tokens.append(compact[i:i + 2])
    for w in tokens:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0
    n = np.linalg.norm(vec)
    return vec / n if n > 0 else vec


class LongTermStore:
    """长时记忆库：支持关键词与语义两种检索。"""

    def __init__(self):
        self.entries = []            # {"text","meta","vec"}

    def write(self, text: str, meta: dict):
        self.entries.append({"text": text, "meta": meta, "vec": embed(text)})

    # 检索一：关键词
    def search_keyword(self, q: str, top_k: int = 3) -> list[dict]:
        hits = [{"text": e["text"], "meta": e["meta"], "score": 1.0}
                for e in self.entries if q in e["text"]]
        return hits[:top_k]

    # 检索二：语义（余弦）
    def search_semantic(self, q: str, top_k: int = 3, meta_filter: dict = None) -> list[dict]:
        pool = [e for e in self.entries
                if all(e["meta"].get(k) == v for k, v in (meta_filter or {}).items())]
        if not pool:
            return []
        qv = embed(q)
        sims = [float(np.dot(qv, e["vec"])) for e in pool]
        order = np.argsort(sims)[::-1][:top_k]
        return [{"text": pool[i]["text"], "meta": pool[i]["meta"], "score": round(sims[i], 3)}
                for i in order]


# ---------------------------------------------------------------------------
# 演示：写入 -> 检索 -> 注入上下文
# ---------------------------------------------------------------------------
def main():
    store = LongTermStore()

    # 1) 写入（对话中沉淀的事实与经验）
    memories = [
        ("用户偏好中文回复，称呼为 张工", {"user": "zhang", "type": "fact"}),
        ("用户所在时区是 Asia/Shanghai", {"user": "zhang", "type": "fact"}),
        ("任务经验：查环比要先取两期数据再用 calc 工具", {"user": "zhang", "type": "exp"}),
        ("用户偏好中文回复，称呼为 李总", {"user": "li", "type": "fact"}),
        ("任务经验：品类明细要用 query_sales 加 category 参数", {"user": "li", "type": "exp"}),
    ]
    for text, meta in memories:
        store.write(text, meta)

    print("=" * 62)
    print("1) 关键词检索：'偏好'")
    for r in store.search_keyword("偏好"):
        print(f"  {r['text']}  {r['meta']}")

    print("\n2) 语义检索：'用户喜欢怎么被称呼'（字面不同，语义相近）")
    for r in store.search_semantic("用户喜欢怎么被称呼", top_k=2, meta_filter={"user": "zhang"}):
        print(f"  score={r['score']}  {r['text']}")

    print("\n3) 语义检索：'环比怎么算'（召回任务经验）")
    for r in store.search_semantic("环比怎么算", top_k=2, meta_filter={"user": "zhang"}):
        print(f"  score={r['score']}  {r['text']}")

    print("\n4) 注入上下文（作为 system 前缀给模型）")
    hits = store.search_semantic("称呼与偏好", top_k=2, meta_filter={"user": "zhang"})
    injected = "\n".join(f"- {h['text']}" for h in hits)
    prompt_prefix = f"[你记得]\n{injected}\n\n请基于以上记忆继续对话。"
    print(prompt_prefix)

    print("\n要点：")
    print("  1. 长时记忆=写入(事实/经验)+检索(关键词/语义)+注入(上下文前缀)")
    print("  2. 语义检索能召回『字面不同但语义相近』的记忆（本例哈希向量较简，真实用 Embedding）")
    print("  3. meta 过滤（user/type）实现多用户隔离——这是生产硬要求")
    print("  4. 检索结果注入要克制（top_k 小），避免记忆挤占任务上下文")


if __name__ == "__main__":
    main()