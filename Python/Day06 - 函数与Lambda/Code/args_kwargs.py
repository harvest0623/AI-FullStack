# 文件用途：*args / **kwargs 练习，演示可变参数、仅关键字参数、仅位置参数、参数组合
# 电商场景：灵活的日志函数、配置合并函数


# ============ 1. 可变位置参数 *args ============
def sum_all(*args: float) -> float:
    """对任意数量的数值求和

    Args:
        *args: 任意数量的数值，被收集为元组

    Returns:
        求和结果
    """
    print(f"  args 类型: {type(args).__name__}, 值: {args}")
    return sum(args)


def demo_args():
    """演示 *args"""
    print("===== 1. 可变位置参数 *args =====")
    print(f"sum_all(1, 2, 3) = {sum_all(1, 2, 3)}")
    print(f"sum_all(1, 2, 3, 4, 5) = {sum_all(1, 2, 3, 4, 5)}")
    print(f"sum_all() = {sum_all()}")    # 空调用，args=()

    # 解包传参
    nums = [10, 20, 30]
    print(f"sum_all(*nums) = {sum_all(*nums)}")    # 解包列表


# ============ 2. 可变关键字参数 **kwargs ============
def print_config(**kwargs):
    """打印配置项

    Args:
        **kwargs: 任意数量的关键字参数，被收集为字典
    """
    print(f"  kwargs 类型: {type(kwargs).__name__}, 值: {kwargs}")
    for key, value in kwargs.items():
        print(f"  {key} = {value}")


def demo_kwargs():
    """演示 **kwargs"""
    print("\n===== 2. 可变关键字参数 **kwargs =====")
    print_config(host="localhost", port=8080, debug=True)

    # 解包传参
    cfg = {"host": "0.0.0.0", "port": 3000}
    print("\n解包字典传参:")
    print_config(**cfg)


# ============ 3. 仅关键字参数（Keyword-only）============
def create_order(order_id, /, customer_id, *, items, status="pending"):
    """创建订单

    Args:
        order_id: 仅位置参数，订单ID
        customer_id: 普通参数，客户ID
        items: 仅关键字参数，商品列表（强制关键字，避免混淆）
        status: 仅关键字参数，订单状态

    Returns:
        订单字典
    """
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "items": items,
        "status": status,
    }


def demo_keyword_only():
    """演示仅关键字参数"""
    print("\n===== 3. 仅关键字参数 =====")
    # 正确调用
    order = create_order(1001, "C001", items=["iPhone", "AirPods"], status="paid")
    print(f"正确调用: {order}")

    # items 必须用关键字
    # create_order(1001, "C001", ["iPhone"], "paid")  # ❌ TypeError

    # 只用关键字的部分参数
    order2 = create_order(1002, "C002", items=["iPad"])
    print(f"使用默认 status: {order2}")


# ============ 4. 仅位置参数（Positional-only，3.8+）============
def calc_price(price, qty, /, *, discount=0.0):
    """计算价格

    Args:
        price: 仅位置参数，单价
        qty: 仅位置参数，数量
        discount: 仅关键字参数，折扣率

    Returns:
        总价
    """
    return price * qty * (1 - discount)


def demo_positional_only():
    """演示仅位置参数"""
    print("\n===== 4. 仅位置参数 =====")
    print(f"calc_price(99, 3) = {calc_price(99, 3)}")
    print(f"calc_price(99, 3, discount=0.1) = {calc_price(99, 3, discount=0.1)}")

    # price/qty 不能用关键字
    # calc_price(price=99, qty=3)  # ❌ TypeError


# ============ 5. 参数完整组合 ============
def full_params(a, b, /, c, d=10, *args, e, f=20, **kwargs):
    """演示所有参数类型的组合

    参数顺序：仅位置 / 普通 / 默认 / *args / 仅关键字 / **kwargs

    Args:
        a, b: 仅位置参数
        c: 普通参数
        d: 默认参数
        *args: 可变位置参数
        e: 仅关键字参数
        f: 仅关键字默认参数
        **kwargs: 可变关键字参数
    """
    print(f"  a={a}, b={b} (仅位置)")
    print(f"  c={c}, d={d} (普通/默认)")
    print(f"  args={args} (可变位置)")
    print(f"  e={e}, f={f} (仅关键字)")
    print(f"  kwargs={kwargs} (可变关键字)")


def demo_full_params():
    """演示完整参数组合"""
    print("\n===== 5. 完整参数组合 =====")
    print("调用 full_params(1, 2, 3, 4, 5, 6, e=7, g=9, h=10):")
    full_params(1, 2, 3, 4, 5, 6, e=7, g=9, h=10)


# ============ 6. 电商场景：灵活的日志函数 ============
def log_event(event: str, *tags, level: str = "INFO", **metadata):
    """灵活的日志函数

    Args:
        event: 事件名称
        *tags: 任意数量的标签
        level: 日志级别（仅关键字）
        **metadata: 任意元数据

    Returns:
        日志字符串
    """
    parts = [f"[{level}] {event}"]

    if tags:
        parts.append(f"tags={list(tags)}")

    if metadata:
        kv_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
        parts.append(kv_str)

    log_line = " | ".join(parts)
    print(f"  {log_line}")
    return log_line


def demo_log_function():
    """电商场景：灵活的日志函数"""
    print("\n===== 6. 灵活的日志函数 =====")
    log_event("order_created")
    log_event("order_created", "vip", "rush", level="INFO")
    log_event("order_paid", "vip", level="INFO",
              order_id=1001, amount=5999, method="alipay")
    log_event("stock_warning", "critical", level="ERROR",
              product="iPhone", stock=2)


# ============ 7. 电商场景：配置合并函数 ============
def merge_config(base: dict, /, *, overrides: dict | None = None, **extra) -> dict:
    """合并配置字典

    Args:
        base: 基础配置（仅位置）
        overrides: 覆盖配置（仅关键字）
        **extra: 额外的单键值配置

    Returns:
        合并后的新字典（不修改原字典）
    """
    merged = dict(base)         # 浅拷贝
    if overrides:
        merged.update(overrides)
    merged.update(extra)        # extra 优先级最高
    return merged


def demo_config_merge():
    """电商场景：配置合并函数"""
    print("\n===== 7. 配置合并函数 =====")

    default_config = {
        "host": "localhost",
        "port": 8080,
        "debug": False,
        "timeout": 30,
    }
    print(f"默认配置: {default_config}")

    # 覆盖部分配置
    prod_config = merge_config(default_config, overrides={"host": "0.0.0.0", "debug": False})
    print(f"生产配置: {prod_config}")

    # 用额外关键字覆盖
    custom_config = merge_config(default_config, port=9000, debug=True, log_level="DEBUG")
    print(f"自定义配置: {custom_config}")

    # 原字典不被修改
    print(f"原配置不变: {default_config}")


# ============ 8. 电商场景：灵活的订单创建 ============
def create_order_flexible(customer_id, *items, status="pending", **options):
    """灵活创建订单

    Args:
        customer_id: 客户ID
        *items: 任意数量的商品（每个是 (product_id, qty) 元组）
        status: 订单状态
        **options: 额外选项（shipping_address, payment_method, discount 等）

    Returns:
        订单字典
    """
    order = {
        "customer_id": customer_id,
        "items": list(items),
        "status": status,
        "options": options,
        "total_items": sum(qty for _, qty in items),
    }
    return order


def demo_flexible_order():
    """电商场景：灵活的订单创建"""
    print("\n===== 8. 灵活的订单创建 =====")

    # 简单订单
    order1 = create_order_flexible("C001", ("P001", 1), ("P002", 2))
    print(f"简单订单: {order1}")

    # 带选项的订单
    order2 = create_order_flexible(
        "C002",
        ("P001", 1),
        status="paid",
        shipping_address="北京市朝阳区",
        payment_method="alipay",
        discount=0.1,
    )
    print(f"带选项订单: {order2}")


if __name__ == "__main__":
    demo_args()
    demo_kwargs()
    demo_keyword_only()
    demo_positional_only()
    demo_full_params()
    demo_log_function()
    demo_config_merge()
    demo_flexible_order()
    print("\n✅ *args/**kwargs 练习全部完成")
