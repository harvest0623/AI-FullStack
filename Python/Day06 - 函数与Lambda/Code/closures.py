# 文件用途：闭包练习，演示工厂函数、计数器闭包、nonlocal、带状态的函数
# 电商场景：创建折扣计算器、带状态的限流器

import time


# ============ 1. 闭包基础 ============
def make_greeting(greeting: str):
    """返回一个带固定问候语的函数

    闭包：inner 引用了外层函数的 greeting 变量
    """
    def inner(name: str) -> str:
        return f"{greeting}, {name}!"    # greeting 来自 make_greeting
    return inner


def demo_closure_basics():
    """演示闭包基础"""
    print("===== 1. 闭包基础 =====")

    hello = make_greeting("Hello")
    hi = make_greeting("Hi")
    print(hello("Python"))    # Hello, Python!
    print(hi("Python"))       # Hi, Python!

    # 即使 make_greeting 已返回，greeting 仍被 inner "记住"
    print(f"hello 的闭包变量: {hello.__closure__[0].cell_contents}")
    print(f"hi 的闭包变量: {hi.__closure__[0].cell_contents}")


# ============ 2. 工厂函数 ============
def make_multiplier(n: float):
    """乘法工厂：返回一个把输入乘以 n 的函数"""
    def multiply(x: float) -> float:
        return x * n
    return multiply


def make_power(exponent: int):
    """幂工厂：返回一个把输入求 exponent 次幂的函数"""
    def power(base: float) -> float:
        return base ** exponent
    return power


def demo_factory():
    """演示工厂函数"""
    print("\n===== 2. 工厂函数 =====")

    double = make_multiplier(2)
    triple = make_multiplier(3)
    print(f"double(5) = {double(5)}")     # 10
    print(f"triple(5) = {triple(5)}")     # 15

    square = make_power(2)
    cube = make_power(3)
    print(f"square(4) = {square(4)}")     # 16
    print(f"cube(3) = {cube(3)}")         # 27


# ============ 3. 计数器闭包与 nonlocal ============
def make_counter(start: int = 0):
    """创建一个计数器闭包

    Args:
        start: 初始值

    Returns:
        一个每次调用 +1 并返回当前值的函数
    """
    count = start

    def counter():
        nonlocal count       # 声明修改外层变量（不加会报错或创建局部变量）
        count += 1
        return count

    return counter


def make_counter_with_reset(start: int = 0):
    """带 reset 功能的计数器（返回多个函数）"""
    count = start

    def increment():
        nonlocal count
        count += 1
        return count

    def reset():
        nonlocal count
        count = start
        return count

    def get():
        return count          # 只读，不需要 nonlocal

    return increment, reset, get


def demo_counter():
    """演示计数器闭包与 nonlocal"""
    print("\n===== 3. 计数器闭包与 nonlocal =====")

    c1 = make_counter()
    print(f"c1() = {c1()}")    # 1
    print(f"c1() = {c1()}")    # 2
    print(f"c1() = {c1()}")    # 3

    # 每个闭包独立
    c2 = make_counter(100)
    print(f"c2() = {c2()}")    # 101
    print(f"c2() = {c2()}")    # 102
    print(f"c1() = {c1()}")    # 4（c1 不受 c2 影响）

    # 带重置的计数器
    inc, reset, get = make_counter_with_reset(10)
    print(f"\n带重置的计数器 (start=10):")
    print(f"  inc() = {inc()}")    # 11
    print(f"  inc() = {inc()}")    # 12
    print(f"  get() = {get()}")    # 12
    print(f"  reset() = {reset()}")  # 10
    print(f"  get() = {get()}")    # 10


# ============ 4. nonlocal vs 局部变量陷阱 ============
def demo_nonlocal_trap():
    """演示不加 nonlocal 的陷阱"""
    print("\n===== 4. nonlocal 陷阱 =====")

    # ❌ 不加 nonlocal：内部函数试图修改外层变量会创建新的局部变量
    def bad_counter():
        count = 0
        def inner():
            # count += 1    # ❌ UnboundLocalError: cannot assign to 'count'
            # 因为 += 会被视为创建局部变量，但又先读取了它
            return count    # 只读是允许的
        return inner

    c = bad_counter()
    print(f"  只读外层变量（无需 nonlocal）: {c()}")

    # ✅ 加 nonlocal：可以真正修改外层变量
    def good_counter():
        count = 0
        def inner():
            nonlocal count
            count += 1
            return count
        return inner

    c2 = good_counter()
    print(f"  加 nonlocal 后修改: {c2()}, {c2()}, {c2()}")


# ============ 5. 电商场景：折扣计算器 ============
def make_discount_calculator(customer_type: str):
    """根据客户类型创建折扣计算器

    Args:
        customer_type: 客户类型 'normal' / 'vip' / 'svip'

    Returns:
        计算折后价的函数
    """
    discount_rates = {
        "normal": 1.0,
        "vip": 0.9,
        "svip": 0.8,
    }
    rate = discount_rates.get(customer_type, 1.0)
    total_saved = [0.0]     # 用列表包装，便于在闭包中修改（或用 nonlocal）

    def calc(price: float) -> float:
        discounted = price * rate
        saved = price - discounted
        total_saved[0] += saved
        return round(discounted, 2)

    def get_saved() -> float:
        return round(total_saved[0], 2)

    calc.get_saved = get_saved    # 挂载辅助函数
    return calc


def make_discount_with_nonlocal(customer_type: str):
    """用 nonlocal 实现的折扣计算器（更优雅）"""
    rates = {"normal": 1.0, "vip": 0.9, "svip": 0.8}
    rate = rates.get(customer_type, 1.0)
    total_saved = 0.0
    order_count = 0

    def calc(price: float) -> float:
        nonlocal total_saved, order_count
        discounted = price * rate
        total_saved += price - discounted
        order_count += 1
        return round(discounted, 2)

    def stats() -> dict:
        return {
            "customer_type": customer_type,
            "rate": rate,
            "orders": order_count,
            "total_saved": round(total_saved, 2),
        }

    calc.stats = stats
    return calc


def demo_discount_calculator():
    """电商场景：折扣计算器"""
    print("\n===== 5. 折扣计算器 =====")

    # 普通客户
    normal = make_discount_with_nonlocal("normal")
    # VIP 客户
    vip = make_discount_with_nonlocal("vip")
    # SVIP 客户
    svip = make_discount_with_nonlocal("svip")

    prices = [5999, 199, 4499]
    print("不同客户类型的折后价:")
    print(f"{'原价':<10}{'普通':<10}{'VIP':<10}{'SVIP':<10}")
    for p in prices:
        print(f"¥{p:<9}¥{normal(p):<9}¥{vip(p):<9}¥{svip(p):<9}")

    print(f"\nVIP 客户累计节省: ¥{vip.stats()['total_saved']}")
    print(f"VIP 客户订单数: {vip.stats()['orders']}")
    print(f"SVIP 客户累计节省: ¥{svip.stats()['total_saved']}")


# ============ 6. 电商场景：带状态的限流器 ============
def make_rate_limiter(max_calls: int, window_seconds: float):
    """创建带状态的限流器

    在 window_seconds 时间窗口内最多允许 max_calls 次调用

    Args:
        max_calls: 最大调用次数
        window_seconds: 时间窗口（秒）

    Returns:
        allow() 函数：返回 True 表示允许，False 表示被限流
    """
    call_times: list[float] = []    # 记录每次调用的时间戳

    def allow() -> bool:
        now = time.time()
        # 清理过期的时间戳（超出窗口）
        cutoff = now - window_seconds
        # 用列表切片模拟清理（避免在 nonlocal 复杂场景下出错）
        while call_times and call_times[0] < cutoff:
            call_times.pop(0)

        if len(call_times) < max_calls:
            call_times.append(now)
            return True
        return False

    def status() -> dict:
        now = time.time()
        cutoff = now - window_seconds
        active = sum(1 for t in call_times if t >= cutoff)
        return {
            "max_calls": max_calls,
            "window": window_seconds,
            "active_calls": active,
            "remaining": max_calls - active,
        }

    allow.status = status
    return allow


def demo_rate_limiter():
    """电商场景：带状态的限流器"""
    print("\n===== 6. 带状态的限流器 =====")

    # 创建限流器：3秒内最多3次
    limiter = make_rate_limiter(max_calls=3, window_seconds=3.0)

    print("限流器配置: 3秒内最多 3 次调用")
    print(f"初始状态: {limiter.status()}")

    results = []
    for i in range(5):
        ok = limiter()           # limiter 本身就是 allow 函数
        results.append(ok)
        print(f"  第 {i+1} 次调用: {'✅ 允许' if ok else '❌ 限流'}")

    print(f"当前状态: {limiter.status()}")

    print("\n等待 3.2 秒后重置窗口...")
    time.sleep(3.2)
    ok = limiter()
    print(f"  再次调用: {'✅ 允许' if ok else '❌ 限流'}")
    print(f"  状态: {limiter.status()}")


# ============ 7. 电商场景：购物车累加器 ============
def make_cart_accumulator():
    """创建购物车累加器闭包

    Returns:
        add(pid, price, qty) 函数：添加商品并返回当前总价
        total() 函数：返回当前总价
        items() 函数：返回购物车内容
    """
    cart = {}       # product_id -> [name, price, qty]
    grand_total = 0.0

    def add(pid: str, name: str, price: float, qty: int) -> float:
        nonlocal grand_total
        if pid in cart:
            cart[pid][2] += qty
        else:
            cart[pid] = [name, price, qty]
        grand_total += price * qty
        return grand_total

    def total() -> float:
        return grand_total

    def get_items() -> dict:
        return dict(cart)

    def clear():
        nonlocal grand_total
        cart.clear()
        grand_total = 0.0

    add.total = total
    add.items = get_items
    add.clear = clear
    return add


def demo_cart_accumulator():
    """电商场景：购物车累加器"""
    print("\n===== 7. 购物车累加器 =====")

    cart = make_cart_accumulator()

    print(f"添加 iPhone ×1: ¥{cart('P001', 'iPhone', 5999, 1):.2f}")
    print(f"添加 AirPods ×2: ¥{cart('P002', 'AirPods', 199, 2):.2f}")
    print(f"再次添加 iPhone ×1: ¥{cart('P001', 'iPhone', 5999, 1):.2f}")
    print(f"添加 iPad ×1: ¥{cart('P003', 'iPad', 2999, 1):.2f}")

    print(f"\n当前总价: ¥{cart.total():.2f}")
    print(f"购物车内容:")
    for pid, info in cart.items().items():
        name, price, qty = info
        print(f"  {pid} {name} × {qty} = ¥{price * qty}")

    cart.clear()
    print(f"\n清空后总价: ¥{cart.total():.2f}")


if __name__ == "__main__":
    demo_closure_basics()
    demo_factory()
    demo_counter()
    demo_nonlocal_trap()
    demo_discount_calculator()
    demo_rate_limiter()
    demo_cart_accumulator()
    print("\n✅ 闭包练习全部完成")
