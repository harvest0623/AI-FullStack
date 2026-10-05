# 文件用途：Lambda 与高阶函数练习，演示 lambda、map/filter/reduce/sorted with key
# 电商场景：商品按价格排序、提取商品名、过滤库存不足、计算总库存

from functools import reduce


# 示例商品数据
PRODUCTS = [
    {"id": "P001", "name": "iPhone 15", "price": 5999, "stock": 50, "category": "phone"},
    {"id": "P002", "name": "MacBook Pro", "price": 12999, "stock": 15, "category": "laptop"},
    {"id": "P003", "name": "AirPods Pro", "price": 199, "stock": 200, "category": "accessory"},
    {"id": "P004", "name": "iPad Air", "price": 4499, "stock": 0, "category": "tablet"},
    {"id": "P005", "name": "Magic Mouse", "price": 99, "stock": 80, "category": "accessory"},
    {"id": "P006", "name": "Pixel 8", "price": 4999, "stock": 30, "category": "phone"},
    {"id": "P007", "name": "ThinkPad X1", "price": 9999, "stock": 8, "category": "laptop"},
]


# ============ 1. Lambda 基础 ============
def demo_lambda_basics():
    """演示 Lambda 匿名函数"""
    print("===== 1. Lambda 基础 =====")

    # 基本形式
    square = lambda x: x ** 2
    print(f"square(5) = {square(5)}")

    # 多参数
    add = lambda a, b: a + b
    print(f"add(3, 4) = {add(3, 4)}")

    # 带默认值
    greet = lambda name, greeting="Hello": f"{greeting}, {name}"
    print(f"greet('Tom') = {greet('Tom')}")
    print(f"greet('Tom', 'Hi') = {greet('Tom', 'Hi')}")

    # 条件表达式
    classify = lambda price: "expensive" if price > 5000 else "cheap"
    print(f"classify(5999) = {classify(5999)}")
    print(f"classify(99) = {classify(99)}")

    # 局限：单表达式，不能有语句
    # bad = lambda x: for i in range(x): print(i)  # ❌ 语法错误


# ============ 2. sorted with key ============
def demo_sorted():
    """演示 sorted 配合 lambda 排序"""
    print("\n===== 2. sorted with key =====")

    # 按价格升序
    by_price = sorted(PRODUCTS, key=lambda p: p["price"])
    print("按价格升序:")
    for p in by_price:
        print(f"  {p['name']:15s} ¥{p['price']:>6}")

    # 按价格降序
    by_price_desc = sorted(PRODUCTS, key=lambda p: p["price"], reverse=True)
    print("\n按价格降序（前3）:")
    for p in by_price_desc[:3]:
        print(f"  {p['name']:15s} ¥{p['price']:>6}")

    # 按库存升序
    by_stock = sorted(PRODUCTS, key=lambda p: p["stock"])
    print("\n按库存升序:")
    for p in by_stock:
        print(f"  {p['name']:15s} 库存{p['stock']:>4}")

    # 多字段排序：先按分类，再按价格
    by_cat_price = sorted(PRODUCTS, key=lambda p: (p["category"], p["price"]))
    print("\n先按分类再按价格:")
    for p in by_cat_price:
        print(f"  [{p['category']:10s}] {p['name']:15s} ¥{p['price']:>6}")


# ============ 3. map 应用 ============
def demo_map():
    """演示 map 对每个元素应用函数"""
    print("\n===== 3. map 应用 =====")

    # 提取所有商品名
    names = list(map(lambda p: p["name"], PRODUCTS))
    print(f"所有商品名: {names}")

    # 价格打 8 折
    discounted = list(map(lambda p: {**p, "price": round(p["price"] * 0.8, 2)}, PRODUCTS))
    print("8折后价格:")
    for p in discounted:
        print(f"  {p['name']:15s} ¥{p['price']:>6.2f}")

    # 字符串转换
    nums = ["1", "2", "3", "4"]
    int_nums = list(map(int, nums))
    print(f"\n字符串转数字: {nums} -> {int_nums}")

    # Pythonic 对比：列表推导式更易读
    names_lc = [p["name"] for p in PRODUCTS]
    print(f"列表推导式等价: {names_lc == names}")


# ============ 4. filter 过滤 ============
def demo_filter():
    """演示 filter 过滤元素"""
    print("\n===== 4. filter 过滤 =====")

    # 过滤库存大于 0 的商品
    in_stock = list(filter(lambda p: p["stock"] > 0, PRODUCTS))
    print(f"库存>0 的商品 ({len(in_stock)}/{len(PRODUCTS)}):")
    for p in in_stock:
        print(f"  {p['name']:15s} 库存{p['stock']}")

    # 过滤高价商品
    expensive = list(filter(lambda p: p["price"] > 5000, PRODUCTS))
    print(f"\n价格>5000 的商品:")
    for p in expensive:
        print(f"  {p['name']:15s} ¥{p['price']}")

    # 过滤手机分类
    phones = list(filter(lambda p: p["category"] == "phone", PRODUCTS))
    print(f"\n手机分类:")
    for p in phones:
        print(f"  {p['name']}")

    # Pythonic 对比
    in_stock_lc = [p for p in PRODUCTS if p["stock"] > 0]
    print(f"\n列表推导式等价: {in_stock_lc == in_stock}")


# ============ 5. reduce 累积 ============
def demo_reduce():
    """演示 reduce 累积运算"""
    print("\n===== 5. reduce 累积 =====")

    # 计算总库存
    total_stock = reduce(lambda acc, p: acc + p["stock"], PRODUCTS, 0)
    print(f"总库存: {total_stock}")

    # 计算总价值（price * stock 之和）
    total_value = reduce(lambda acc, p: acc + p["price"] * p["stock"], PRODUCTS, 0)
    print(f"总库存价值: ¥{total_value:,}")

    # 求最大价格的商品
    most_expensive = reduce(lambda a, b: a if a["price"] > b["price"] else b, PRODUCTS)
    print(f"最贵的商品: {most_expensive['name']} (¥{most_expensive['price']})")

    # 累乘
    nums = [1, 2, 3, 4, 5]
    product = reduce(lambda a, b: a * b, nums)
    print(f"\n{nums} 的累乘: {product}")

    # 带初始值
    total_with_init = reduce(lambda a, b: a + b, [1, 2, 3], 100)
    print(f"带初始值 100: {total_with_init}")


# ============ 6. any / all 布尔判断 ============
def demo_any_all():
    """演示 any / all"""
    print("\n===== 6. any / all =====")

    # 是否有缺货商品
    has_out_of_stock = any(p["stock"] == 0 for p in PRODUCTS)
    print(f"是否有缺货商品: {has_out_of_stock}")

    # 是否所有商品都有库存
    all_in_stock = all(p["stock"] > 0 for p in PRODUCTS)
    print(f"是否全部有库存: {all_in_stock}")

    # 是否有价格超过 10000 的商品
    has_premium = any(p["price"] > 10000 for p in PRODUCTS)
    print(f"是否有万元商品: {has_premium}")

    # 是否所有商品价格都大于 0
    all_positive = all(p["price"] > 0 for p in PRODUCTS)
    print(f"价格是否全为正: {all_positive}")


# ============ 7. 电商场景：商品数据处理流水线 ============
def demo_pipeline():
    """综合示例：商品数据处理流水线"""
    print("\n===== 7. 数据处理流水线 =====")

    # 任务：找出库存>0的商品，9折，按价格升序，提取名称
    result = (
        sorted(
            map(lambda p: {**p, "price": round(p["price"] * 0.9, 2)},
                filter(lambda p: p["stock"] > 0, PRODUCTS)),
            key=lambda p: p["price"]
        )
    )
    names = list(map(lambda p: p["name"], result))

    print("库存>0 → 9折 → 按价格升序:")
    for p in result:
        print(f"  {p['name']:15s} ¥{p['price']:>6.2f} (原价¥{p['price']/0.9:.0f})")

    # Pythonic 版本：列表推导式更清晰
    result_lc = sorted(
        [{**p, "price": round(p["price"] * 0.9, 2)} for p in PRODUCTS if p["stock"] > 0],
        key=lambda p: p["price"]
    )
    print(f"\n列表推导式版本结果一致: {[p['name'] for p in result_lc] == names}")


# ============ 8. 函数作为字典值（策略模式雏形）============
def demo_strategy():
    """电商场景：用函数字典实现多种排序策略"""
    print("\n===== 8. 排序策略 =====")

    strategies = {
        "price_asc": lambda p: p["price"],
        "price_desc": lambda p: -p["price"],
        "stock_asc": lambda p: p["stock"],
        "name_asc": lambda p: p["name"],
    }

    for name, key_func in strategies.items():
        sorted_products = sorted(PRODUCTS, key=key_func)
        top = sorted_products[0]
        print(f"  {name:12s} → 首个: {top['name']:15s} (¥{top['price']}, 库存{top['stock']})")


if __name__ == "__main__":
    demo_lambda_basics()
    demo_sorted()
    demo_map()
    demo_filter()
    demo_reduce()
    demo_any_all()
    demo_pipeline()
    demo_strategy()
    print("\n✅ Lambda 与高阶函数练习全部完成")
