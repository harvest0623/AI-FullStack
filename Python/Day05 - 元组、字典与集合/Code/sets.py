# 文件用途：集合 set 练习，演示创建、增删、集合运算、推导式、frozenset、去重
# 电商场景：用户标签集合运算、共同购买商品交集、去重用户ID、差集找未下单用户


# ============ 1. 集合创建 ============
def demo_create():
    """演示集合的创建方式"""
    print("===== 1. 集合创建 =====")

    # 多元素集合
    s1 = {1, 2, 3}
    print(f"字面量: {s1}, 类型: {type(s1).__name__}")

    # 空集合——必须用 set()！
    s2 = set()
    print(f"空集合: {s2}")
    print(f"{{}} 的类型是: {type({}).__name__}  ⚠️ 不是 set！")

    # 从可迭代对象创建（自动去重）
    s3 = set([1, 2, 2, 3, 3, 3])
    print(f"从列表去重: {s3}")

    s4 = set("hello")
    print(f"从字符串: {s4}")

    # 集合元素必须是可哈希的（不可变类型）
    # s5 = {[1, 2]}  # TypeError: unhashable type: 'list'


# ============ 2. 增删元素 ============
def demo_add_remove():
    """演示集合的增删操作"""
    print("\n===== 2. 增删元素 =====")

    tags = {"python", "ai"}
    print(f"初始: {tags}")

    # add 添加
    tags.add("ml")
    tags.add("data")       # 已存在则无效
    tags.add("data")
    print(f"add 后: {tags}")

    # remove：不存在会报错
    tags.remove("ml")
    print(f"remove('ml') 后: {tags}")
    # tags.remove("ml")    # KeyError

    # discard：不存在也不报错（推荐）
    tags.discard("ml")     # 安全，不报错
    print(f"discard('ml') 后: {tags}")

    # pop：随机弹出一个
    popped = tags.pop()
    print(f"pop 出: {popped}, 剩余: {tags}")

    # clear 清空
    tags.clear()
    print(f"clear 后: {tags}")


# ============ 3. 集合运算 ============
def demo_set_operations():
    """演示交集、并集、差集、对称差集"""
    print("\n===== 3. 集合运算 =====")

    # 电商场景：两个用户购买过的商品ID
    user_a_bought = {101, 102, 103, 105, 107}
    user_b_bought = {102, 104, 105, 106, 108}

    print(f"用户A购买: {user_a_bought}")
    print(f"用户B购买: {user_b_bought}")

    # 交集：两人共同购买的商品
    common = user_a_bought & user_b_bought
    print(f"交集（共同购买）: {common}")
    print(f"  intersection(): {user_a_bought.intersection(user_b_bought)}")

    # 并集：两人买过的所有商品
    all_bought = user_a_bought | user_b_bought
    print(f"并集（所有商品）: {all_bought}")
    print(f"  union(): {user_a_bought.union(user_b_bought)}")

    # 差集：A 买了但 B 没买——可推荐给 B
    only_a = user_a_bought - user_b_bought
    print(f"差集 A-B（A独有，可推荐给B）: {only_a}")
    only_b = user_b_bought - user_a_bought
    print(f"差集 B-A（B独有，可推荐给A）: {only_b}")

    # 对称差集：两人各自独有（非共同）
    sym_diff = user_a_bought ^ user_b_bought
    print(f"对称差集（各自独有）: {sym_diff}")


# ============ 4. 子集与超集 ============
def demo_subset():
    """演示子集、超集判断"""
    print("\n===== 4. 子集与超集 =====")

    vip_tags = {"gold", "silver", "bronze"}
    user_tags = {"gold", "silver"}

    print(f"VIP标签: {vip_tags}")
    print(f"用户标签: {user_tags}")

    print(f"user_tags 是 vip_tags 的子集? {user_tags <= vip_tags}")    # True
    print(f"user_tags 是真子集? {user_tags < vip_tags}")              # True
    print(f"vip_tags 是 user_tags 的超集? {vip_tags >= user_tags}")    # True

    # 方法形式
    print(f"issubset(): {user_tags.issubset(vip_tags)}")
    print(f"issuperset(): {vip_tags.issuperset(user_tags)}")

    # 不相交
    print(f"{'gold'} 和 {'platinum'} 不相交? { {'gold'}.isdisjoint({'platinum'}) }")


# ============ 5. 集合推导式 ============
def demo_comprehension():
    """演示集合推导式"""
    print("\n===== 5. 集合推导式 =====")

    # 平方集合（自动去重：-3 和 3 的平方都是 9）
    squares = {x**2 for x in range(-3, 4)}
    print(f"平方集合: {squares}")

    # 电商场景：提取所有商品分类（去重）
    products = [
        {"name": "iPhone", "category": "phone"},
        {"name": "MacBook", "category": "laptop"},
        {"name": "iPad", "category": "tablet"},
        {"name": "Pixel", "category": "phone"},
    ]
    categories = {p["category"] for p in products}
    print(f"所有分类（去重）: {categories}")

    # 过滤
    nums = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    evens = {x for x in nums if x % 2 == 0}
    print(f"偶数集合: {evens}")


# ============ 6. frozenset 不可变集合 ============
def demo_frozenset():
    """演示 frozenset 的不可变性与可哈希性"""
    print("\n===== 6. frozenset =====")

    fs = frozenset([1, 2, 3])
    print(f"frozenset: {fs}, 类型: {type(fs).__name__}")

    # 不可变
    # fs.add(4)     # AttributeError
    # fs.remove(1)  # AttributeError

    # 可哈希——可作字典键
    d = {frozenset(["a", "b"]): "组合AB", frozenset(["c"]): "组合C"}
    print(f"以 frozenset 为键的字典: {d}")

    # 查询
    key = frozenset(["a", "b"])
    print(f"查询 {key}: {d[key]}")

    # 集合元素必须是可哈希的，所以集合的元素也可以是 frozenset（嵌套集合）
    set_of_sets = {frozenset([1, 2]), frozenset([3, 4]), frozenset([1, 2])}
    print(f"嵌套集合（自动去重）: {set_of_sets}")


# ============ 7. 去重应用 ============
def demo_dedup():
    """演示集合的去重应用"""
    print("\n===== 7. 去重应用 =====")

    # 电商场景：订单中的用户ID有重复，需要去重
    order_user_ids = [101, 102, 101, 103, 102, 104, 101, 105]
    print(f"原始用户ID列表（有重复）: {order_user_ids}")

    # 方法1：set 去重
    unique_ids = set(order_user_ids)
    print(f"去重后集合: {unique_ids}")
    print(f"去重后列表: {list(unique_ids)}")

    # 方法2：保持顺序去重（dict.fromkeys，3.7+ dict 有序）
    unique_ordered = list(dict.fromkeys(order_user_ids))
    print(f"保持顺序去重: {unique_ordered}")

    # 统计独立用户数
    print(f"独立用户数: {len(unique_ids)}")


# ============ 8. 成员判断性能对比 ============
def demo_membership_performance():
    """演示集合 vs 列表的成员判断性能"""
    print("\n===== 8. 成员判断性能 =====")

    import time

    n = 1_000_000
    big_list = list(range(n))
    big_set = set(big_list)
    target = n - 1   # 查找最后一个元素

    # 列表查找 O(n)
    start = time.perf_counter()
    _ = target in big_list
    list_time = time.perf_counter() - start

    # 集合查找 O(1)
    start = time.perf_counter()
    _ = target in big_set
    set_time = time.perf_counter() - start

    print(f"在 {n} 个元素中查找 {target}:")
    print(f"  列表耗时: {list_time*1000:.3f} ms")
    print(f"  集合耗时: {set_time*1000:.6f} ms")
    print(f"  集合快约 {list_time/set_time:.0f} 倍")


# ============ 9. 用户标签综合示例 ============
def demo_user_tags():
    """综合示例：用户标签集合运算"""
    print("\n===== 9. 用户标签综合示例 =====")

    # 三个用户的兴趣标签
    user1_tags = {"python", "ml", "data", "web"}
    user2_tags = {"python", "web", "frontend", "react"}
    user3_tags = {"ml", "data", "ai", "nlp"}

    print(f"用户1标签: {user1_tags}")
    print(f"用户2标签: {user2_tags}")
    print(f"用户3标签: {user3_tags}")

    # 找出所有出现过的标签
    all_tags = user1_tags | user2_tags | user3_tags
    print(f"\n所有标签: {all_tags}")

    # 三人共同标签
    common_all = user1_tags & user2_tags & user3_tags
    print(f"三人共同标签: {common_all}")

    # 用户1和用户2的共同标签（推荐关注彼此）
    common_12 = user1_tags & user2_tags
    print(f"用户1&2共同标签: {common_12}")

    # 用户1有但用户2没有的标签
    only_1 = user1_tags - user2_tags
    print(f"用户1独有（vs用户2）: {only_1}")

    # 三个人的"独特"标签（只属于一个人）
    only_1_unique = user1_tags - user2_tags - user3_tags
    only_2_unique = user2_tags - user1_tags - user3_tags
    only_3_unique = user3_tags - user1_tags - user2_tags
    print(f"用户1独有（vs全部）: {only_1_unique}")
    print(f"用户2独有（vs全部）: {only_2_unique}")
    print(f"用户3独有（vs全部）: {only_3_unique}")

    # 至少两人共有的标签
    from collections import Counter
    tag_counter = Counter()
    for tags in [user1_tags, user2_tags, user3_tags]:
        tag_counter.update(tags)
    shared_by_2plus = {tag for tag, cnt in tag_counter.items() if cnt >= 2}
    print(f"至少两人共有的标签: {shared_by_2plus}")


# ============ 10. 找未下单用户 ============
def demo_find_inactive_users():
    """电商场景：用差集找出未下单的用户"""
    print("\n===== 10. 找未下单用户 =====")

    # 所有注册用户
    all_users = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    # 下过单的用户（从订单记录中提取）
    ordered_users = {2, 3, 5, 7, 8}

    # 差集：注册但未下单的用户
    inactive = all_users - ordered_users
    print(f"所有用户: {all_users}")
    print(f"已下单用户: {ordered_users}")
    print(f"未下单用户（差集）: {inactive}")

    # 活跃用户
    active = all_users & ordered_users
    print(f"活跃用户（交集）: {active}")

    # 转化率
    rate = len(active) / len(all_users) * 100
    print(f"下单转化率: {rate:.1f}%")


if __name__ == "__main__":
    demo_create()
    demo_add_remove()
    demo_set_operations()
    demo_subset()
    demo_comprehension()
    demo_frozenset()
    demo_dedup()
    demo_membership_performance()
    demo_user_tags()
    demo_find_inactive_users()
    print("\n✅ 集合练习全部完成")
