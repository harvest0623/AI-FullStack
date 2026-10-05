# 文件用途：四种数据结构对比与选型，演示同一问题的不同实现及性能差异
# 电商场景：用 list/tuple/dict/set 四种结构解决同一问题，对比优劣

import sys
import time
from collections import Counter, defaultdict, namedtuple


# ============ 1. 四种数据结构特性总览 ============
def overview():
    """打印四种数据结构的特性对比表"""
    print("===== 1. 四种数据结构特性总览 =====")
    print(f"{'结构':<10}{'可变性':<8}{'有序性':<10}{'重复':<8}{'查找复杂度':<12}{'可哈希':<8}")
    print("-" * 56)
    print(f"{'list':<10}{'可变':<8}{'有序':<10}{'允许':<8}{'O(n)':<12}{'否':<8}")
    print(f"{'tuple':<10}{'不可变':<8}{'有序':<10}{'允许':<8}{'O(n)':<12}{'是':<8}")
    print(f"{'dict':<10}{'可变':<8}{'插入序':<10}{'键不可':<8}{'O(1)':<12}{'键是':<8}")
    print(f"{'set':<10}{'可变':<8}{'无序':<10}{'不重复':<8}{'O(1)':<12}{'否':<8}")
    print(f"{'frozenset':<10}{'不可变':<8}{'无序':<10}{'不重复':<8}{'O(1)':<12}{'是':<8}")


# ============ 2. 同一问题的不同实现：按ID查找商品 ============
def find_product_by_id():
    """同一查询任务，用 list / tuple / dict / set 四种方式实现"""
    print("\n===== 2. 按ID查找商品：四种实现对比 =====")

    # 原始数据
    products_data = [
        (i, f"Product_{i}", i * 10.0, i % 100) for i in range(1, 1001)
    ]

    # 方式1：用 list 存储，线性查找 O(n)
    products_list = list(products_data)

    def find_in_list(pid: int) -> tuple | None:
        for p in products_list:
            if p[0] == pid:
                return p
        return None

    # 方式2：用 tuple 存储（不可变），线性查找 O(n)
    products_tuple = tuple(products_data)

    def find_in_tuple(pid: int) -> tuple | None:
        for p in products_tuple:
            if p[0] == pid:
                return p
        return None

    # 方式3：用 dict 建立 id->product 的映射，O(1)
    products_dict = {p[0]: p for p in products_data}

    def find_in_dict(pid: int) -> tuple | None:
        return products_dict.get(pid)

    # 方式4：用 set 存储 id（仅判断存在性），O(1)
    id_set = {p[0] for p in products_data}

    def exists_in_set(pid: int) -> bool:
        return pid in id_set

    # 性能测试：查找最后一个元素（对 list/tuple 最不利）
    target = 1000
    n_times = 10_000

    start = time.perf_counter()
    for _ in range(n_times):
        find_in_list(target)
    list_t = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(n_times):
        find_in_tuple(target)
    tuple_t = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(n_times):
        find_in_dict(target)
    dict_t = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(n_times):
        exists_in_set(target)
    set_t = time.perf_counter() - start

    print(f"在 1000 个商品中查找 ID={target}，执行 {n_times} 次：")
    print(f"  list   查找: {list_t*1000:.2f} ms  (O(n))")
    print(f"  tuple  查找: {tuple_t*1000:.2f} ms  (O(n))")
    print(f"  dict   查找: {dict_t*1000:.3f} ms  (O(1)) ⭐")
    print(f"  set   存在: {set_t*1000:.3f} ms  (O(1)) ⭐")
    print(f"  dict 比 list 快约 {list_t/dict_t:.0f} 倍")


# ============ 3. 内存占用对比 ============
def memory_comparison():
    """对比不同数据结构的内存占用"""
    print("\n===== 3. 内存占用对比 =====")

    data = list(range(100))

    lst = list(data)
    tup = tuple(data)
    st = set(data)
    dct = {x: x for x in data}

    print(f"存储 0-99 共 100 个整数：")
    print(f"  list  内存: {sys.getsizeof(lst):>6} bytes")
    print(f"  tuple 内存: {sys.getsizeof(tup):>6} bytes")
    print(f"  set   内存: {sys.getsizeof(st):>6} bytes")
    print(f"  dict  内存: {sys.getsizeof(dct):>6} bytes")
    print(f"  → tuple 比 list 省 {sys.getsizeof(lst) - sys.getsizeof(tup)} bytes")
    print(f"  → set/dict 用空间换时间（哈希表）")


# ============ 4. 去重的三种实现 ============
def dedup_comparison():
    """对比去重的不同实现方式"""
    print("\n===== 4. 去重对比 =====")

    # 1000 个含重复的元素
    import random
    random.seed(42)
    data = [random.randint(1, 100) for _ in range(1000)]

    # 方式1：set 去重（不保序）
    start = time.perf_counter()
    unique_set = set(data)
    set_t = time.perf_counter() - start

    # 方式2：dict.fromkeys 去重（保序，3.7+）
    start = time.perf_counter()
    unique_dict = list(dict.fromkeys(data))
    dict_t = time.perf_counter() - start

    # 方式3：手动循环去重（保序，低效）
    start = time.perf_counter()
    seen = set()
    unique_manual = []
    for x in data:
        if x not in seen:
            seen.add(x)
            unique_manual.append(x)
    manual_t = time.perf_counter() - start

    print(f"从 1000 个含重复元素中去重：")
    print(f"  set()             : {set_t*1000:.3f} ms, 结果数 {len(unique_set)}")
    print(f"  dict.fromkeys()   : {dict_t*1000:.3f} ms, 结果数 {len(unique_dict)} (保序)")
    print(f"  手动循环 + set    : {manual_t*1000:.3f} ms, 结果数 {len(unique_manual)} (保序)")


# ============ 5. 分组统计的三种实现 ============
def group_comparison():
    """对比按分类分组的实现方式"""
    print("\n===== 5. 按分类分组对比 =====")

    # 电商场景：按 category 分组商品
    products = [
        {"id": i, "name": f"P{i}", "category": f"cat_{i % 10}", "price": i * 10}
        for i in range(1, 1001)
    ]

    # 方式1：普通 dict 手动判断
    start = time.perf_counter()
    groups1 = {}
    for p in products:
        cat = p["category"]
        if cat not in groups1:
            groups1[cat] = []
        groups1[cat].append(p)
    t1 = time.perf_counter() - start

    # 方式2：defaultdict
    start = time.perf_counter()
    groups2 = defaultdict(list)
    for p in products:
        groups2[p["category"]].append(p)
    t2 = time.perf_counter() - start

    # 方式3：dict.setdefault
    start = time.perf_counter()
    groups3 = {}
    for p in products:
        groups3.setdefault(p["category"], []).append(p)
    t3 = time.perf_counter() - start

    print(f"按分类分组 1000 个商品：")
    print(f"  普通 dict + 判断 : {t1*1000:.3f} ms")
    print(f"  defaultdict(list): {t2*1000:.3f} ms ⭐")
    print(f"  dict.setdefault  : {t3*1000:.3f} ms")
    print(f"  分组数: {len(groups1)}")


# ============ 6. 选择决策表 ============
def decision_table():
    """打印数据结构选择决策表"""
    print("\n===== 6. 数据结构选择决策表 =====")
    print("""
┌──────────────────────────────────────────────────────────────┐
│                    数据结构选择决策表                          │
├──────────────────────────────────────────────────────────────┤
│ Q: 需要 "键 → 值" 映射？                                     │
│   └─ YES → dict (查找 O(1))                                  │
│                                                              │
│ Q: 需要去重 或 集合运算（交集/并集/差集）？                    │
│   └─ YES → set (查找 O(1))                                   │
│                                                              │
│ Q: 数据不可变（作字典键 / 配置 / 多返回值）？                  │
│   └─ YES → tuple 或 frozenset                                │
│                                                              │
│ Q: 需要有序、可增删的序列？                                   │
│   └─ YES → list (最通用)                                     │
│                                                              │
│ Q: 需要计数？                                                │
│   └─ YES → collections.Counter                               │
│                                                              │
│ Q: 分组（一键多值）？                                        │
│   └─ YES → collections.defaultdict(list)                     │
│                                                              │
│ Q: 固定结构记录，字段有名字？                                 │
│   └─ YES → namedtuple 或 dataclass(Day08)                    │
└──────────────────────────────────────────────────────────────┘
""")


# ============ 7. 综合应用：电商数据统计 ============
def ecommerce_stats():
    """综合示例：用多种数据结构完成电商数据统计"""
    print("\n===== 7. 综合应用：电商数据统计 =====")

    # 用 namedtuple 定义商品模型（不可变记录）
    Product = namedtuple("Product", ["id", "name", "price", "category"])

    # 商品列表（list 存储有序数据）
    products = [
        Product(1, "iPhone", 5999, "phone"),
        Product(2, "MacBook", 12999, "laptop"),
        Product(3, "AirPods", 199, "accessory"),
        Product(4, "iPad", 2999, "tablet"),
        Product(5, "Pixel", 4999, "phone"),
        Product(6, "Mouse", 99, "accessory"),
        Product(7, "ThinkPad", 8999, "laptop"),
        Product(8, "Galaxy Tab", 2599, "tablet"),
    ]

    # 1. dict 建立 id -> product 映射（快速查找）
    product_map = {p.id: p for p in products}
    print(f"商品映射 (dict): 查找 ID=3 -> {product_map[3].name}")

    # 2. set 获取所有分类（去重）
    categories = {p.category for p in products}
    print(f"所有分类 (set): {categories}")

    # 3. defaultdict 按 category 分组
    by_category = defaultdict(list)
    for p in products:
        by_category[p.category].append(p.name)
    print("\n按分类分组 (defaultdict):")
    for cat, names in by_category.items():
        print(f"  {cat}: {names}")

    # 4. Counter 统计各分类商品数
    cat_counter = Counter(p.category for p in products)
    print(f"\n分类商品数 (Counter): {dict(cat_counter)}")
    print(f"  最多的分类: {cat_counter.most_common(1)}")

    # 5. 订单数据：用 tuple 存储不可变记录
    orders = [
        (1001, 1, 2),   # (order_id, product_id, qty)
        (1002, 3, 5),
        (1003, 2, 1),
        (1004, 1, 1),
        (1005, 6, 10),
    ]

    # 6. set 统计下过单的商品ID
    ordered_pids = {pid for _, pid, _ in orders}
    print(f"\n下过单的商品ID (set): {ordered_pids}")

    # 7. set 差集找出从未被下单的商品
    all_pids = {p.id for p in products}
    never_ordered = all_pids - ordered_pids
    print(f"从未下单的商品ID (差集): {never_ordered}")
    print(f"  对应商品: {[product_map[pid].name for pid in never_ordered]}")

    # 8. dict 计算各商品销售额
    sales = defaultdict(float)
    for _, pid, qty in orders:
        sales[product_map[pid].name] += product_map[pid].price * qty
    print(f"\n各商品销售额 (defaultdict):")
    for name, amount in sorted(sales.items(), key=lambda x: -x[1]):
        print(f"  {name}: ¥{amount:,.0f}")

    # 9. frozenset 作字典键：按价格区间分组
    def price_tier(price: float) -> frozenset:
        if price < 500:
            return frozenset(["budget"])
        elif price < 3000:
            return frozenset(["mid"])
        else:
            return frozenset(["premium"])

    tier_map = {}
    for p in products:
        tier = price_tier(p.price)
        tier_map.setdefault(tier, []).append(p.name)
    print(f"\n按价格区间分组 (frozenset 作键):")
    for tier, names in tier_map.items():
        print(f"  {set(tier)}: {names}")


if __name__ == "__main__":
    overview()
    find_product_by_id()
    memory_comparison()
    dedup_comparison()
    group_comparison()
    decision_table()
    ecommerce_stats()
    print("\n✅ 数据结构对比练习全部完成")
