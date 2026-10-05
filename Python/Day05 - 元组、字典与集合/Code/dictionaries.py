# 文件用途：字典 dict 练习，演示增删改查、遍历、推导式、collections 模块
# 电商场景：商品分类映射、购物车 cart[product_id]=quantity、订单状态统计 Counter、按分类分组 defaultdict

from collections import Counter, OrderedDict, defaultdict


# ============ 1. 字典创建 ============
def demo_create():
    """演示字典的多种创建方式"""
    print("===== 1. 字典创建 =====")

    # 空字典
    d1 = {}
    d2 = dict()
    print(f"空字典: {d1}, 类型: {type(d1).__name__}")

    # 字面量
    prices = {"P001": 5999, "P002": 199, "P003": 49}
    print(f"商品价格表: {prices}")

    # dict() 关键字参数
    config = dict(host="localhost", port=8080, debug=True)
    print(f"配置: {config}")

    # 从键值对列表创建
    pairs = [("a", 1), ("b", 2)]
    d3 = dict(pairs)
    print(f"从列表创建: {d3}")

    # 字典推导式
    squares = {x: x**2 for x in range(5)}
    print(f"平方字典: {squares}")


# ============ 2. 增删改查 ============
def demo_crud():
    """演示字典的增删改查"""
    print("\n===== 2. 增删改查 =====")

    product = {"id": "P001", "name": "iPhone 15", "price": 5999}
    print(f"初始: {product}")

    # 增
    product["stock"] = 50
    product["category"] = "phone"
    print(f"新增字段后: {product}")

    # 改
    product["price"] = 5499
    print(f"修改价格后: {product}")

    # 查——get 更安全
    print(f"get name: {product.get('name')}")
    print(f"get color(不存在): {product.get('color', 'unknown')}")

    # 直接索引不存在会报错
    # product['color']  # KeyError

    # setdefault：存在返回原值，不存在则设置
    color = product.setdefault("color", "black")
    print(f"setdefault color: {color}, 字典: {product}")
    color2 = product.setdefault("color", "white")  # 已存在，返回原值 black
    print(f"再次 setdefault: {color2} (不变)")

    # 删
    del product["stock"]
    print(f"删除 stock 后: {product}")

    removed = product.pop("category")
    print(f"pop category: {removed}, 字典: {product}")

    last = product.popitem()       # 弹出最后插入的键值对
    print(f"popitem: {last}, 字典: {product}")


# ============ 3. 遍历字典 ============
def demo_iterate():
    """演示字典的三种遍历方式"""
    print("\n===== 3. 遍历字典 =====")

    cart = {"P001": 2, "P002": 1, "P003": 5}

    print("遍历 keys:")
    for pid in cart.keys():
        print(f"  商品ID: {pid}")

    print("遍历 values:")
    for qty in cart.values():
        print(f"  数量: {qty}")

    print("遍历 items（最常用）:")
    for pid, qty in cart.items():
        print(f"  {pid} × {qty}")


# ============ 4. 字典推导式 ============
def demo_comprehension():
    """演示字典推导式"""
    print("\n===== 4. 字典推导式 =====")

    prices = {"P001": 5999, "P002": 199, "P003": 49, "P004": 1299}

    # 过滤：只保留高价商品
    expensive = {k: v for k, v in prices.items() if v > 500}
    print(f"高价商品 (>500): {expensive}")

    # 转换：价格打 8 折
    discounted = {k: round(v * 0.8, 2) for k, v in prices.items()}
    print(f"8折后: {discounted}")

    # 反转键值
    price_to_id = {v: k for k, v in prices.items()}
    print(f"反转键值: {price_to_id}")


# ============ 5. 合并字典 ============
def demo_merge():
    """演示字典合并的多种方式"""
    print("\n===== 5. 合并字典 =====")

    base = {"name": "iPhone", "price": 5999}
    extra = {"price": 5499, "stock": 50, "color": "black"}

    # update：原地修改
    d1 = base.copy()
    d1.update(extra)
    print(f"update 合并: {d1}")

    # 解包合并（3.5+）：生成新字典
    merged = {**base, **extra}
    print(f"解包合并: {merged}")

    # | 运算符（3.9+）
    merged2 = base | extra
    print(f"| 运算符合并: {merged2}")

    # 多个字典解包
    a = {"x": 1}
    b = {"y": 2}
    c = {"z": 3}
    print(f"多字典合并: {{**a, **b, **c}} = { {**a, **b, **c} }")


# ============ 6. 嵌套字典 ============
def demo_nested():
    """演示嵌套字典"""
    print("\n===== 6. 嵌套字典 =====")

    # 电商场景：多门店信息
    shops = {
        "beijing": {"staff": 10, "sales": 50000, "products": 200},
        "shanghai": {"staff": 8, "sales": 60000, "products": 180},
        "shenzhen": {"staff": 12, "sales": 55000, "products": 220},
    }

    # 访问嵌套字段
    print(f"北京销售额: {shops['beijing']['sales']}")
    print(f"深圳员工数: {shops['shenzhen']['staff']}")

    # 遍历嵌套字典
    print("各门店汇总:")
    for city, info in shops.items():
        print(f"  {city}: 员工{info['staff']}人, 销售{info['sales']}元, 商品{info['products']}种")

    # 计算总销售额
    total_sales = sum(info["sales"] for info in shops.values())
    print(f"三店总销售额: {total_sales}")


# ============ 7. defaultdict 应用 ============
def demo_defaultdict():
    """演示 defaultdict 按分类分组"""
    print("\n===== 7. defaultdict =====")

    # 电商场景：商品列表，按 category 分组
    products = [
        {"id": "P001", "name": "iPhone", "category": "phone"},
        {"id": "P002", "name": "MacBook", "category": "laptop"},
        {"id": "P003", "name": "iPad", "category": "tablet"},
        {"id": "P004", "name": "Pixel", "category": "phone"},
        {"id": "P005", "name": "ThinkPad", "category": "laptop"},
    ]

    # 用普通 dict 需要判断键是否存在
    groups_normal = {}
    for p in products:
        if p["category"] not in groups_normal:
            groups_normal[p["category"]] = []
        groups_normal[p["category"]].append(p["name"])

    # 用 defaultdict(list) 更简洁
    groups = defaultdict(list)
    for p in products:
        groups[p["category"]].append(p["name"])

    print("按分类分组:")
    for cat, names in groups.items():
        print(f"  {cat}: {names}")

    # defaultdict(int) 计数
    word_counts = defaultdict(int)
    for p in products:
        word_counts[p["category"]] += 1
    print(f"分类计数: {dict(word_counts)}")


# ============ 8. Counter 计数器 ============
def demo_counter():
    """演示 Counter 统计订单状态"""
    print("\n===== 8. Counter =====")

    # 电商场景：订单状态列表
    orders = [
        ("O001", "paid"),
        ("O002", "shipped"),
        ("O003", "done"),
        ("O004", "paid"),
        ("O005", "cancelled"),
        ("O006", "paid"),
        ("O007", "shipped"),
        ("O008", "done"),
        ("O009", "paid"),
    ]

    # 统计各状态数量
    status_counter = Counter(status for _, status in orders)
    print(f"订单状态统计: {dict(status_counter)}")
    print(f"paid 订单数: {status_counter['paid']}")
    print(f"most_common(2): {status_counter.most_common(2)}")

    # Counter 运算
    c1 = Counter(a=3, b=1)
    c2 = Counter(a=1, b=2)
    print(f"\nc1={dict(c1)}, c2={dict(c2)}")
    print(f"c1 + c2: {dict(c1 + c2)}")      # 相加
    print(f"c1 - c2: {dict(c1 - c2)}")      # 相减（只保留正数）

    # update 增量计数
    status_counter.update(["paid", "shipped"])
    print(f"更新后 paid: {status_counter['paid']}, shipped: {status_counter['shipped']}")


# ============ 9. OrderedDict ============
def demo_ordered_dict():
    """演示 OrderedDict 的独有功能"""
    print("\n===== 9. OrderedDict =====")

    # 3.7+ 普通 dict 已有序，但 OrderedDict 有 move_to_end 等独有方法
    od = OrderedDict()
    od["P001"] = 5999
    od["P002"] = 199
    od["P003"] = 49
    print(f"初始: {list(od.keys())}")

    od.move_to_end("P001")          # 把 P001 移到末尾
    print(f"move_to_end('P001') 后: {list(od.keys())}")

    od.move_to_end("P003", last=False)  # 移到开头
    print(f"move_to_end('P003', last=False) 后: {list(od.keys())}")

    # popitem(last=False) 弹出最早插入的，可实现 FIFO 队列
    first_item = od.popitem(last=False)
    print(f"popitem(last=False): {first_item}, 剩余: {list(od.keys())}")


# ============ 10. 购物车综合示例 ============
def demo_shopping_cart():
    """综合示例：用字典实现购物车"""
    print("\n===== 10. 购物车综合示例 =====")

    # 商品价格表
    catalog = {
        "P001": {"name": "iPhone 15", "price": 5999},
        "P002": {"name": "AirPods", "price": 199},
        "P003": {"name": "iPad", "price": 2999},
        "P004": {"name": "MacBook", "price": 12999},
    }

    # 购物车：product_id -> quantity
    cart = {}

    def add_to_cart(pid: str, qty: int = 1):
        """添加商品到购物车"""
        if pid not in catalog:
            print(f"  商品 {pid} 不存在")
            return
        cart[pid] = cart.get(pid, 0) + qty

    def remove_from_cart(pid: str):
        """从购物车移除"""
        if pid in cart:
            qty = cart.pop(pid)
            print(f"  移除 {catalog[pid]['name']} × {qty}")

    def show_cart():
        """展示购物车"""
        if not cart:
            print("  购物车为空")
            return
        print("  购物车内容:")
        total = 0
        for pid, qty in cart.items():
            info = catalog[pid]
            subtotal = info["price"] * qty
            total += subtotal
            print(f"    {info['name']} × {qty} = ¥{subtotal}")
        print(f"  总计: ¥{total}")

    # 操作演示
    add_to_cart("P001", 1)
    add_to_cart("P002", 2)
    add_to_cart("P003", 1)
    add_to_cart("P001", 1)     # 再次添加，数量累加
    add_to_cart("P999", 1)     # 不存在的商品
    show_cart()

    remove_from_cart("P002")
    show_cart()


if __name__ == "__main__":
    demo_create()
    demo_crud()
    demo_iterate()
    demo_comprehension()
    demo_merge()
    demo_nested()
    demo_defaultdict()
    demo_counter()
    demo_ordered_dict()
    demo_shopping_cart()
    print("\n✅ 字典练习全部完成")
