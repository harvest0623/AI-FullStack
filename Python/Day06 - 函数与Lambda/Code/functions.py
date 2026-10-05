# 文件用途：函数基础练习，演示函数定义、调用、返回值、默认参数、类型注解、docstring
# 电商场景：计算订单总价、折扣计算、格式化商品信息


# ============ 1. 函数定义与调用 ============
def greet(name: str) -> str:
    """返回问候语。

    Args:
        name: 用户名

    Returns:
        问候字符串
    """
    return f"Hello, {name}!"


def demo_basics():
    """演示函数定义与调用"""
    print("===== 1. 函数定义与调用 =====")
    print(greet("Python"))
    print(greet("eshop"))


# ============ 2. 返回值 ============
def square(x: float) -> float:
    """单返回值"""
    return x * x


def min_max(numbers: list[int]) -> tuple[int, int]:
    """多返回值（本质返回元组）"""
    return min(numbers), max(numbers)


def log(message: str) -> None:
    """无返回值（隐式 return None）"""
    print(f"[LOG] {message}")
    # 等价于 return None


def demo_return():
    """演示返回值"""
    print("\n===== 2. 返回值 =====")
    print(f"square(5) = {square(5)}")

    lo, hi = min_max([3, 1, 4, 1, 5, 9, 2, 6])
    print(f"min_max([3,1,4,1,5,9,2,6]) -> min={lo}, max={hi}")

    # 多返回值本质是元组
    result = min_max([10, 20, 5])
    print(f"返回值类型: {type(result).__name__}, 值: {result}")

    ret = log("订单已创建")
    print(f"log 返回值: {ret}")


# ============ 3. 位置参数与关键字参数 ============
def create_product(pid: str, name: str, price: float, stock: int) -> dict:
    """创建商品字典"""
    return {"id": pid, "name": name, "price": price, "stock": stock}


def demo_args():
    """演示位置参数与关键字参数"""
    print("\n===== 3. 位置参数与关键字参数 =====")

    # 位置参数：按顺序对应
    p1 = create_product("P001", "iPhone", 5999, 50)
    print(f"位置参数: {p1}")

    # 关键字参数：可乱序，更清晰
    p2 = create_product(pid="P002", name="iPad", stock=30, price=2999)
    print(f"关键字参数: {p2}")

    # 混合：位置参数必须在关键字参数前
    p3 = create_product("P003", "MacBook", price=12999, stock=10)
    print(f"混合传参: {p3}")


# ============ 4. 默认参数 ============
def format_price(price: float, currency: str = "¥", decimals: int = 2) -> str:
    """格式化价格

    Args:
        price: 价格
        currency: 货币符号，默认 ¥
        decimals: 小数位数，默认 2

    Returns:
        格式化后的价格字符串
    """
    return f"{currency}{price:.{decimals}f}"


def demo_default():
    """演示默认参数"""
    print("\n===== 4. 默认参数 =====")
    print(format_price(5999))                    # ¥5999.00
    print(format_price(5999, currency="$"))      # $5999.00
    print(format_price(5999, decimals=0))        # ¥5999
    print(format_price(5999, "$", 0))            # $5999


# ============ 5. 可变默认值陷阱 ============
def append_item_bad(item, lst=[]):
    """❌ 危险：可变默认值会在多次调用间共享"""
    lst.append(item)
    return lst


def append_item_safe(item, lst=None):
    """✅ 正确：用 None 作哨兵，函数内创建"""
    if lst is None:
        lst = []
    lst.append(item)
    return lst


def demo_mutable_default_trap():
    """演示可变默认值陷阱"""
    print("\n===== 5. 可变默认值陷阱 =====")
    print(f"bad(1) = {append_item_bad(1)}")     # [1]
    print(f"bad(2) = {append_item_bad(2)}")     # [1, 2] —— 不是 [2]！
    print(f"safe(1) = {append_item_safe(1)}")   # [1]
    print(f"safe(2) = {append_item_safe(2)}")   # [2] —— 正确


# ============ 6. 电商场景：计算订单总价 ============
def calc_order_total(items: list[tuple[float, int]], discount: float = 0.0) -> float:
    """计算订单总价。

    Args:
        items: 商品列表，每个元素为 (单价, 数量)
        discount: 折扣率，0.0 表示无折扣，0.1 表示打 9 折

    Returns:
        订单总价（已应用折扣）
    """
    subtotal = sum(price * qty for price, qty in items)
    return subtotal * (1 - discount)


def demo_order_total():
    """电商场景：计算订单总价"""
    print("\n===== 6. 计算订单总价 =====")
    cart = [(5999.0, 1), (199.0, 2), (49.0, 5)]
    print(f"购物车: {cart}")
    print(f"无折扣总价: ¥{calc_order_total(cart):.2f}")
    print(f"9折后总价: ¥{calc_order_total(cart, discount=0.1):.2f}")


# ============ 7. 电商场景：折扣计算函数 ============
def apply_discount(price: float, discount_type: str = "none") -> float:
    """根据折扣类型计算折后价。

    Args:
        price: 原价
        discount_type: 折扣类型，可选 'none' / 'vip' / 'promo' / 'clearance'

    Returns:
        折后价格
    """
    discount_map = {
        "none": 1.0,
        "vip": 0.85,        # VIP 85折
        "promo": 0.9,       # 促销 9折
        "clearance": 0.5,   # 清仓 5折
    }
    rate = discount_map.get(discount_type, 1.0)
    return round(price * rate, 2)


def demo_discount():
    """电商场景：折扣计算"""
    print("\n===== 7. 折扣计算 =====")
    price = 5999.0
    print(f"原价: ¥{price}")
    for dtype in ["none", "vip", "promo", "clearance"]:
        print(f"  {dtype:10s}: ¥{apply_discount(price, dtype)}")


# ============ 8. 电商场景：格式化商品信息 ============
def format_product(product: dict, show_stock: bool = True, prefix: str = "•") -> str:
    """格式化商品信息为字符串。

    Args:
        product: 商品字典，含 name/price/stock 等字段
        show_stock: 是否显示库存
        prefix: 每行前缀

    Returns:
        格式化后的多行字符串
    """
    lines = [
        f"{prefix} 商品ID: {product.get('id', 'N/A')}",
        f"{prefix} 名称: {product.get('name', 'N/A')}",
        f"{prefix} 价格: {format_price(product.get('price', 0))}",
    ]
    if show_stock:
        lines.append(f"{prefix} 库存: {product.get('stock', 0)}")
    return "\n".join(lines)


def demo_format():
    """电商场景：格式化商品信息"""
    print("\n===== 8. 格式化商品信息 =====")
    product = {"id": "P001", "name": "iPhone 15", "price": 5999.0, "stock": 50}
    print(format_product(product))
    print("---")
    print(format_product(product, show_stock=False, prefix=">"))


# ============ 9. docstring 查看 ============
def demo_docstring():
    """演示 docstring 的查看方式"""
    print("\n===== 9. docstring 查看 =====")
    print("calc_order_total 的文档:")
    print(calc_order_total.__doc__)
    print("\napply_discount 的第一行:")
    print(apply_discount.__doc__.split('\n')[0])


# ============ 10. 函数是一等公民 ============
def demo_first_class():
    """演示函数作为一等公民"""
    print("\n===== 10. 函数是一等公民 =====")

    # 1. 赋值给变量
    f = format_price
    print(f"赋值给变量: f(99.5) = {f(99.5)}")

    # 2. 存入数据结构
    operations = {
        "total": lambda items: sum(p * q for p, q in items),
        "count": lambda items: sum(q for _, q in items),
        "max_price": lambda items: max(p for p, _ in items),
    }
    cart = [(5999.0, 1), (199.0, 2), (49.0, 5)]
    print(f"存入字典 - 总价: ¥{operations['total'](cart):.2f}")
    print(f"存入字典 - 总数: {operations['count'](cart)}")
    print(f"存入字典 - 最高单价: ¥{operations['max_price'](cart):.2f}")

    # 3. 作为参数传递
    def apply_to_cart(cart, func):
        return func(cart)

    print(f"作为参数 - 总价: ¥{apply_to_cart(cart, operations['total']):.2f}")


if __name__ == "__main__":
    demo_basics()
    demo_return()
    demo_args()
    demo_default()
    demo_mutable_default_trap()
    demo_order_total()
    demo_discount()
    demo_format()
    demo_docstring()
    demo_first_class()
    print("\n✅ 函数基础练习全部完成")
