# Day10 - RAG 质量评估

> "感觉还行"靠不住。要持续优化 RAG，必须先**量化**：检索召回了多少正确的、回答是否忠实、上下文是否切题。今天建立 RAG 的评估体系——检索指标、生成指标、RAGAS 框架，以及"评估→优化→再评估"的闭环。

## 学习目标

完成本章后，你将能够：

- 说出 RAG 评估的三个层面（检索/生成/端到端）
- 计算检索指标 Recall / Precision / MRR / nDCG
- 理解生成指标 Faithfulness / Relevancy / Correctness
- 用 RAGAS 评估端到端质量
- 构建评估数据集并形成优化闭环

---

## 一、为什么要评估

- 无法量化 → 无法判断改了什么 / 是否变好 → 优化全靠猜。
- 评估提供**回归保护**：改一处别让别处"塌方"。
- 评估是你的**决策依据**：该上重排/混合/HyDE，用数字说话。

> RAG 调试铁律：**先分层定位（检索还是生成），再针对性优化，用指标确认。**

---

## 二、评估的三个层面

```
端到端（User Experience）
 ├── 检索层：召回的相关文档列表  (Recall/MRR/nDCG)
 ├── 生成层：回答与上下文的忠实、切题  (Faithfulness/Relevancy)
 └── 上下文层：检索到的上下文本身是否相关  (Context Relevance)
```

| 层面 | 回答的问题 | 核心指标 |
|------|-----------|---------|
| 检索层 | 该拿的拿到的？排得好吗？ | Recall@K, Precision@K, MRR, nDCG |
| 上下文层 | 拿到的上下文切题吗？ | Context Relevance |
| 生成层 | 答案是忠实、相关、正确的吗？ | Faithfulness, Relevancy, Correctness |

---

## 三、检索层指标

以"标注出哪些文档块与问题的真相关"为前提：

| 指标 | 计算 | 含义 |
|------|------|------|
| **Recall@K** | 命中真相关数 / 真相关总数 | 有没有漏 |
| **Precision@K** | 命中真相关数 / 返回数 K | 返回的准不准 |
| **MRR** | 首个真相关排名的倒数 | 首个是否正确 |
| **nDCG@K** | 按排名位置加权 | 排序质量 |

```python
# Recall@K
def recall_at_k(hits, relevant, k):
    top = set(hits[:k])
    return len(top & relevant) / len(relevant)
```

---

## 四、生成层指标

| 指标 | 评估 | 说明 |
|------|------|------|
| **Faithfulness（忠实性）** | 回答是否**忠实于提供的上下文** | 抓"幻觉"：答了上下文没有的内容 = 扣分 |
| **Relevancy（相关性）** | 回答是否**切题** | 抓"答非所问" |
| **Correctness（正确性）** | 与标准参考答案对比 | 需标注参考答案 |

**忠实性**是防幻觉的关键：即使召回全对，若生成乱加料，也要扣分。

---

## 五、RAGAS 端到端框架

RAGAS 提供开箱即用的评估指标（基于 LLM judge），三大核心：

| 指标 | 含义 | 评估对象 |
|------|------|---------|
| **context_precision** | 检索到的上下文是否含真相关 | 上下文层 |
| **context_recall** | 真相关信息是否被检索到 | 上下文层 |
| **faithfulness** | 回答忠实于上下文 | 生成层 |
| **answer_relevancy** | 回答切题 | 生成层 |

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
results = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
results
```

> 用 LLM 打分（如 GPT-4/本地 judge）给出各指标分数，形成可复用的评估脚本（CI 里跑）。

---

## 六、构建评估数据集

高质量评估集 = 少量、覆盖各失败模式、有正确答案：

```json
[
  {"question": "报销住宿上限是多少？",
   "ground_truth": "每日500元",
   "reference_contexts": ["住宿每日上限500元"],   // 用于检索指标标注
   "expected_source": "报销合规手册"}
]
```

关键：
- **覆盖难例**（口语化、专有名词、易混淆），避免只测"送分题"。
- 规模不必大（几十到几百条）但要有代表性。
- 人工标注真相关 + 参考答案。

---

## 七、评估驱动的优化闭环

```
建评估集 → 跑基线指标 → 定位弱点（检索 or 生成）
   │
   └─ 针对性优化（切块/嵌入/重排/路由/改写... 见 Day03-09）
        │
        └─ 重跑指标 → 对比提升？→ 保留优化 or 回退
```

- 每次优化**只动一处**，看指标变化，避免无法归因。
- 用 CI 定期跑回归，防止上线后偷偷变差。

---

## 场景：DataIQ 的评估落地

为 DataIQ 建 60 条评估集（覆盖报销/年假/产品/权限等难例），用 RAGAS + 本地 LLM judge：跑出 baseline 的 recall/faithfulness，发现"报销口语化问题 recall 低"，据此上查询改写与混合检索，重跑看到 recall 提升再合入。

---

## 代码文件说明

| 文件 | 内容 | 是否需联网 |
|------|------|-----------|
| `Code/01_retrieval_metrics.py` | Recall/Precision/MRR/nDCG 计算 | 否 |
| `Code/02_generation_metrics.py` | 忠实性等生成指标判定逻辑 | 否 |
| `Code/03_ragas_eval.py` | 用 RAGAS 评估端到端 | 是（需 LLM） |
| `Code/04_eval_dataset.py` | 构建评估数据集的示例 | 否 |
| `Code/README.md` | 运行说明 | - |

---

## 关键知识点总结

1. **评估三层面**：检索 / 上下文 / 生成。
2. **检索指标**：Recall、Precision、MRR、nDCG。
3. **生成指标**：Faithfulness（防幻觉）、Relevancy、Correctness。
4. **RAGAS**：用 LLM judge 自动化端到端评估。
5. **闭环**：建集→基线→定位→优化→重测→保留/回退。

---

## 实战练习

### 练习 1：手算检索指标

给出一组命中列表与真相关集合，手算 Recall@3、MRR、nDCG@3（用 `01` 校验）。

### 练习 2：忠实性判定

给三个回答样例（一个忠实、一个加入上下文没有的细节、一个答非所问），用 `02` 的规则判定其 faithfulness / relevancy。

### 练习 3：跑 RAGAS

在有 Key 时用 `03_ragas_eval.py` 对一个迷你 RAG 评估，观察 faithfulness / answer_relevancy 分数。

### 练习 4：为 DataIQ 建集

设计 10 条覆盖"困难场景"的评估问句（含口语化、专有名词、复合问题、权限类），并给出参考答案与真相关上下文。

---

## 下一步

评估确认系统"在正确路径上"。最后两天走向生产：Day11 设计生产级 RAG 架构（缓存、观测、FastAPI、安全），Day12 综合实战交付 DataIQ 完整系统。