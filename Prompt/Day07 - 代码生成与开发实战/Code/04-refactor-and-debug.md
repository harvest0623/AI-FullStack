# 重构与调试模板合集

> 本文件包含 3 个模板：代码重构、Bug 修复、性能优化。每个模板含完整 Prompt 与示例，覆盖代码质量保障的核心场景。

---

## 模板 1：代码重构 - 提取函数与消除重复

### 模板说明
- 用途：在不改变外部行为的前提下重构代码，提升可读性与可维护性
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{code}}`、`{{refactor_goals}}`

### 完整模板

```text
你是一名资深软件工程师，精通代码重构。请重构以下代码。

【待重构代码】
{{code}}

【重构目标】
{{refactor_goals}}

约束（必须严格遵守）：
1. 保持外部可观察行为完全不变（输入输出一致，副作用一致）
2. 不修改公开函数的签名
3. 不引入新的外部依赖
4. 每一处改动都要有明确的动机
5. 保持代码风格一致（缩进、命名、注释规范）

输出格式：
1. 重构后的完整代码
2. 重构说明（表格：改动位置 / 改动类型 / 动机）
3. 行为等价性验证思路（如何确认行为未变）
4. 进一步优化建议（可选，不强制在本次实施）
```

### 使用示例

#### 输入
```text
你是一名资深软件工程师，精通代码重构。请重构以下代码。

【待重构代码】
```python
def process_order(order):
    # 校验
    if not order.get("id"):
        return {"success": False, "error": "订单ID缺失"}
    if not order.get("user_id"):
        return {"success": False, "error": "用户ID缺失"}
    if not order.get("items"):
        return {"success": False, "error": "商品列表为空"}
    for item in order["items"]:
        if not item.get("product_id"):
            return {"success": False, "error": "商品ID缺失"}
        if item.get("quantity", 0) <= 0:
            return {"success": False, "error": "商品数量非法"}
        if item.get("price", 0) <= 0:
            return {"success": False, "error": "商品价格非法"}

    # 计算总价
    total = 0
    for item in order["items"]:
        total += item["quantity"] * item["price"]

    # 应用折扣
    if order.get("user_level") == "gold":
        if total >= 500:
            total = (total - 80) * 0.85
        else:
            total = total * 0.85
    elif order.get("user_level") == "silver":
        total = total * 0.9
    elif order.get("user_level") == "bronze":
        if total >= 200:
            total = total - 20

    # 生成结果
    return {
        "success": True,
        "order_id": order["id"],
        "total": round(total, 2),
        "item_count": len(order["items"]),
    }
```

【重构目标】
1. 提取函数（校验、总价、折扣、结果生成）
2. 消除重复的"返回错误"模式
3. 简化嵌套条件
4. 提升可测试性

约束（必须严格遵守）：
1. 保持外部可观察行为完全不变
2. 不修改 process_order 的签名
3. 不引入新的外部依赖
4. 每一处改动都要有明确的动机
5. 保持代码风格一致

输出格式：
1. 重构后的完整代码
2. 重构说明
3. 行为等价性验证思路
4. 进一步优化建议
```

#### 预期输出
```python
from typing import Any


class OrderError(Exception):
    """订单处理错误，携带错误信息。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _validate_order(order: dict) -> None:
    """校验订单字段，失败时抛出 OrderError。"""
    if not order.get("id"):
        raise OrderError("订单ID缺失")
    if not order.get("user_id"):
        raise OrderError("用户ID缺失")
    if not order.get("items"):
        raise OrderError("商品列表为空")
    for item in order["items"]:
        if not item.get("product_id"):
            raise OrderError("商品ID缺失")
        if item.get("quantity", 0) <= 0:
            raise OrderError("商品数量非法")
        if item.get("price", 0) <= 0:
            raise OrderError("商品价格非法")


def _calculate_total(items: list[dict]) -> float:
    """计算商品总价。"""
    return sum(item["quantity"] * item["price"] for item in items)


def _apply_discount(total: float, user_level: str | None) -> float:
    """根据用户等级应用折扣。"""
    if user_level == "gold":
        if total >= 500:
            return (total - 80) * 0.85
        return total * 0.85
    if user_level == "silver":
        return total * 0.9
    if user_level == "bronze" and total >= 200:
        return total - 20
    return total


def _build_success_result(order: dict, total: float) -> dict:
    """构造成功响应。"""
    return {
        "success": True,
        "order_id": order["id"],
        "total": round(total, 2),
        "item_count": len(order["items"]),
    }


def process_order(order: dict) -> dict:
    """处理订单：校验 → 计算总价 → 应用折扣 → 返回结果。

    Args:
        order: 订单字典，含 id、user_id、items、user_level。

    Returns:
        成功时 {"success": True, ...}；失败时 {"success": False, "error": ...}。
    """
    try:
        _validate_order(order)
        total = _calculate_total(order["items"])
        total = _apply_discount(total, order.get("user_level"))
        return _build_success_result(order, total)
    except OrderError as e:
        return {"success": False, "error": e.message}
```

| 改动位置 | 改动类型 | 动机 |
|---------|---------|------|
| 新增 OrderError | 提取类型 | 统一错误信息载体，消除多处 return {"success": False, "error": ...} 重复 |
| 新增 _validate_order | 提取函数 | 校验逻辑独立，便于单独测试 |
| 新增 _calculate_total | 提取函数 | 总价计算用 sum + 生成器，更简洁 |
| 新增 _apply_discount | 提取函数 | 折扣逻辑独立，扁平化 if/elif 链 |
| 新增 _build_success_result | 提取函数 | 结果构造与主流程分离 |
| process_order 主体 | 简化 | 仅保留编排逻辑，职责单一 |

行为等价性验证思路：
1. 编写单元测试覆盖原函数所有分支（校验失败各类、gold 满/不满 500、silver、bronze 满/不满 200、无 user_level）
2. 用同一组输入分别跑重构前后版本，断言输出完全相等
3. 用 property-based 测试（hypothesis）随机生成订单，验证两版输出一致

进一步优化建议：
1. 用 dataclass / Pydantic 替代 dict，强类型化订单结构
2. 折扣规则可抽为策略模式，便于扩展新等级
3. 引入日志记录每步处理结果

### 调优建议
- 温度：0.0
- 重构后务必让 LLM 列出"等价性验证思路"，便于人工复核
- 若代码量大，可分文件 / 分模块逐个重构

---

## 模板 2：Bug 修复 - 定位 + 分析 + 修复 + 验证

### 模板说明
- 用途：给定代码 + 错误信息 + 期望行为，按"定位 → 分析 → 修复 → 验证"四步修复 Bug
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{code}}`、`{{error_message}}`、`{{expected_behavior}}`、`{{reproduce_steps}}`

### 完整模板

```text
你是一名资深调试工程师。请修复以下代码中的 Bug。

【代码】
{{code}}

【错误信息】
{{error_message}}

【复现步骤】
{{reproduce_steps}}

【期望行为】
{{expected_behavior}}

请严格按以下四步输出：

1. 定位
   - 指出 Bug 所在的行号与代码片段
   - 说明为什么定位到此处

2. 分析（根因分析）
   - 解释 Bug 产生的根本原因
   - 涉及的语言特性 / 框架机制
   - 为什么在某些情况下不会触发

3. 修复
   - 给出修复后的完整代码
   - 标注修改的行

4. 验证
   - 给出至少 3 个测试用例（含原 Bug 触发场景）
   - 说明每个用例预期结果
   - 给出回归测试建议
```

### 使用示例

#### 输入
```text
你是一名资深调试工程师。请修复以下代码中的 Bug。

【代码】
```python
def group_orders_by_user(orders):
    result = {}
    for order in orders:
        user_id = order["user_id"]
        if user_id in result:
            result[user_id].append(order)
        else:
            result[user_id] = order   # ← Bug 在这里
    return result

# 调用
orders = [
    {"user_id": 1, "id": "A"},
    {"user_id": 1, "id": "B"},
    {"user_id": 2, "id": "C"},
]
print(group_orders_by_user(orders))
```

【错误信息】
AttributeError: 'dict' object has no attribute 'append'

【复现步骤】
1. 同一 user_id 出现两次及以上时触发
2. 首次出现的 user_id 不会触发

【期望行为】
返回 {1: [{...A}, {...B}], 2: [{...C}]}，每个 user_id 对应订单列表。

请严格按定位 / 分析 / 修复 / 验证四步输出。
```

#### 预期输出
```markdown
### 1. 定位
- 行号：第 8 行
- 代码片段：`result[user_id] = order`
- 定位依据：错误信息 'dict' object has no attribute 'append' 表明某处把 dict 当成了 list 调用 append。第 5 行 `result[user_id].append(order)` 在第二次遇到同一 user_id 时执行，此时 result[user_id] 的值由第 8 行赋值，赋的是单个 order（dict），而非 list。

### 2. 分析
- 根本原因：else 分支将单个 order 直接赋给 result[user_id]，类型是 dict；而 if 分支假设它是 list 并调用 append。类型不一致导致第二次同 key 触发 AttributeError。
- 涉及机制：Python dict 的引用语义 + 没有类型约束。在静态类型语言中编译期就能发现，Python 需运行时暴露。
- 为什么首次不触发：首次进入 else 分支，赋值后立即进入下一次循环，未调用 append；只有同一 key 第二次出现时才走到 if 分支并 append，此时类型错误暴露。

### 3. 修复
```python
def group_orders_by_user(orders):
    result = {}
    for order in orders:
        user_id = order["user_id"]
        if user_id in result:
            result[user_id].append(order)
        else:
            result[user_id] = [order]   # 修复：用列表包裹
    return result
```
修改行：第 8 行 `result[user_id] = order` → `result[user_id] = [order]`

更 Pythonic 的写法（可选）：
```python
from collections import defaultdict

def group_orders_by_user(orders):
    result = defaultdict(list)
    for order in orders:
        result[order["user_id"]].append(order)
    return dict(result)
```

### 4. 验证
| 用例 | 输入 | 预期 |
|------|------|------|
| 同一 user 多订单（原 Bug 场景） | [{"user_id":1,"id":"A"},{"user_id":1,"id":"B"}] | {1: [A, B]} |
| 不同 user 各一单 | [{"user_id":1,"id":"A"},{"user_id":2,"id":"B"}] | {1:[A], 2:[B]} |
| 空列表 | [] | {} |
| 单个订单 | [{"user_id":1,"id":"A"}] | {1:[A]} |

回归测试建议：
1. 用 pytest 参数化测试以上用例
2. 用 hypothesis 生成随机 orders，断言 result 中所有 value 都是 list
3. 加类型注解 result: dict[int, list[dict]]，配合 mypy 防止类型回归
```

### 调优建议
- 温度：0.0
- 若错误信息不全，可让 LLM 先"模拟运行"输出预期错误
- 复杂 Bug 可追加"请先复现最小化用例"

---

## 模板 3：性能优化 - 分析瓶颈 + 优化建议

### 模板说明
- 用途：分析代码性能瓶颈并给出优化方案
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{code}}`、`{{scenario}}`、`{{performance_target}}`

### 完整模板

```text
你是一名资深性能优化工程师。请分析以下代码的性能问题并给出优化方案。

【代码】
{{code}}

【运行场景】
{{scenario}}

【性能目标】
{{performance_target}}

请按以下结构输出：

1. 性能分析
   - 时间复杂度评估（逐函数）
   - 空间复杂度评估
   - 瓶颈识别（最耗时的操作 Top 3）

2. 优化方案
   - 每个方案包含：方案名 / 思路 / 预期收益 / 实施成本
   - 按"收益 / 成本"比从高到低排序

3. 优化后代码
   - 实施前 2 个最高优先级方案
   - 标注修改点

4. 基准测试建议
   - 给出 benchmark 用例
   - 给出衡量指标（QPS / 延迟 / 内存）

5. 风险提示
   - 优化可能引入的副作用
   - 兼容性 / 可读性 / 正确性风险
```

### 使用示例

#### 输入
```text
你是一名资深性能优化工程师。请分析以下代码的性能问题并给出优化方案。

【代码】
```python
def find_duplicate_orders(orders):
    duplicates = []
    for i in range(len(orders)):
        for j in range(i + 1, len(orders)):
            if orders[i]["amount"] == orders[j]["amount"] \
               and orders[i]["user_id"] == orders[j]["user_id"]:
                duplicates.append((orders[i]["id"], orders[j]["id"]))
    return duplicates

def summarize_by_user(orders):
    result = {}
    for order in orders:
        user_id = order["user_id"]
        if user_id not in result:
            result[user_id] = {"count": 0, "total": 0}
        result[user_id]["count"] += 1
        result[user_id]["total"] += order["amount"]
    return result

def top_users(orders, k=10):
    summary = summarize_by_user(orders)
    # 找消费最高的 k 个用户
    sorted_users = sorted(summary.items(), key=lambda x: x[1]["total"], reverse=True)
    return sorted_users[:k]
```

【运行场景】
电商订单数据，单次处理 100 万条订单，每天运行 1 次。

【性能目标】
当前 find_duplicate_orders 在 100 万条上需 30 分钟，目标 < 10 秒。

请按性能分析 / 优化方案 / 优化后代码 / 基准测试建议 / 风险提示结构输出。
```

#### 预期输出
```markdown
### 1. 性能分析

| 函数 | 时间复杂度 | 空间复杂度 | 备注 |
|------|-----------|-----------|------|
| find_duplicate_orders | O(n²) | O(d) | 双重循环，n=100w 时比较 ~5×10¹¹ 次，瓶颈 |
| summarize_by_user | O(n) | O(u) | u 为用户数，性能可接受 |
| top_users | O(n + u log u) | O(u) | 排序占主导，u 大时略慢 |

瓶颈 Top 3：
1. find_duplicate_orders 的 O(n²) 双重循环 —— 占总耗时 99%
2. top_users 的全量 sorted —— u=10w 时排序 ~1.6ms × log 因子，可优化为堆
3. summarize_by_user 的 dict in 判断 —— 微秒级，可忽略

### 2. 优化方案

| 方案 | 思路 | 预期收益 | 成本 |
|------|------|---------|------|
| A. 哈希分组找重复 | 用 dict 按 (user_id, amount) 分组，组内找重复 | O(n²) → O(n)，30min → <5s | 低，仅改算法 |
| B. top_users 用堆 | heapq.nlargest 替代 sorted | O(u log u) → O(u log k) | 低 |
| C. summarize_by_user 用 defaultdict | 去掉 in 判断 | 微小 | 极低 |
| D. 并行处理 | 多进程分片 | 4-8 倍 | 中，需考虑合并 |

按收益/成本排序：A > B > C > D

### 3. 优化后代码
```python
from collections import defaultdict
import heapq


def find_duplicate_orders(orders):
    """O(n) 哈希分组找重复。"""
    groups = defaultdict(list)
    for order in orders:
        key = (order["user_id"], order["amount"])
        groups[key].append(order["id"])

    duplicates = []
    for ids in groups.values():
        if len(ids) < 2:
            continue
        # 组内两两配对（同组通常很少）
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                duplicates.append((ids[i], ids[j]))
    return duplicates


def summarize_by_user(orders):
    """O(n)，使用 defaultdict。"""
    result = defaultdict(lambda: {"count": 0, "total": 0})
    for order in orders:
        uid = order["user_id"]
        result[uid]["count"] += 1
        result[uid]["total"] += order["amount"]
    return result


def top_users(orders, k=10):
    """O(n + u log k)，堆替代全量排序。"""
    summary = summarize_by_user(orders)
    return heapq.nlargest(
        k, summary.items(), key=lambda x: x[1]["total"]
    )
```

修改点：
- find_duplicate_orders：用 defaultdict 按 (user_id, amount) 分组，组内仅在小列表上两两配对
- summarize_by_user：defaultdict 替代 in 判断
- top_users：heapq.nlargest 替代 sorted + 切片

### 4. 基准测试建议
```python
import random, time
from mymodule import find_duplicate_orders

def gen_orders(n):
    return [{
        "id": i, "user_id": random.randint(1, n // 10),
        "amount": round(random.uniform(1, 1000), 2)
    } for i in range(n)]

for n in [10000, 100000, 1000000]:
    orders = gen_orders(n)
    start = time.perf_counter()
    find_duplicate_orders(orders)
    print(f"n={n}: {time.perf_counter() - start:.3f}s")
```
衡量指标：执行时间（秒）、峰值内存（MB）、重复对数量（验证正确性）。

### 5. 风险提示
1. 哈希分组在 (user_id, amount) 严重倾斜时单组可能很大，极端情况下退化为 O(n²)；可加监控
2. heapq.nlargest 在 k 接近 u 时反而比 sorted 慢，k=10 时收益最大
3. defaultdict(lambda: ...) 不可 pickle，跨进程传递需转为普通 dict
4. 并行方案需注意分片后跨片重复的合并逻辑
```

### 调优建议
- 温度：0.0
- 性能优化必须强调"先测量后优化"，可追加"请先给出 cProfile 分析步骤"
- 若涉及数据库，追加"分析 SQL 执行计划"
- 优化前后必须给出等价性验证，避免"优化即改 Bug"
