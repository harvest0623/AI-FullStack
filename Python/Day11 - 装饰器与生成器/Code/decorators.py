# 文件用途：装饰器基础练习
# 演示无参装饰器、functools.wraps、类装饰器、装饰器堆叠
# 电商场景：@timer 计时函数、@log 记录调用日志
# 运行方式：python decorators.py

import functools
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger('eshop')


# ====== 无参装饰器 ======
def timer(func):
    """计时装饰器：测量函数执行时间"""
    @functools.wraps(func)   # 保留原函数元信息
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)       # 调用原函数
        elapsed = time.perf_counter() - start
        print(f'[timer] {func.__name__} 耗时 {elapsed*1000:.2f} ms')
        return result
    return wrapper


def log(func):
    """日志装饰器：记录函数调用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 记录调用信息
        args_str = ', '.join(
            [repr(a) for a in args] +
            [f'{k}={v!r}' for k, v in kwargs.items()]
        )
        logger.info(f'调用 {func.__name__}({args_str})')
        try:
            result = func(*args, **kwargs)
            logger.info(f'{func.__name__} 返回 {result!r}')
            return result
        except Exception as e:
            logger.error(f'{func.__name__} 抛出 {type(e).__name__}: {e}')
            raise
    return wrapper


# ====== 应用装饰器 ======
@timer
def calculate_total(prices: list[float]) -> float:
    """计算订单总额"""
    # 模拟耗时计算
    time.sleep(0.01)
    return sum(prices)


@log
def find_product(product_id: int, products: dict) -> dict:
    """查找商品"""
    if product_id not in products:
        raise KeyError(f'商品 {product_id} 不存在')
    return products[product_id]


# ====== 装饰器堆叠：从下往上应用，从上往下执行 ======
@timer      # 后应用，外层
@log        # 先应用，内层
def process_order(order_id: int, amount: float) -> str:
    """处理订单（堆叠装饰器）"""
    time.sleep(0.005)
    return f'订单{order_id}处理完成，金额{amount}'


# ====== 类装饰器：可保存状态 ======
class CountCalls:
    """类装饰器：统计函数调用次数"""

    def __init__(self, func):
        self.func = func
        self.count = 0
        functools.update_wrapper(self, func)   # 保留元信息

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f'[CountCalls] 第 {self.count} 次调用 {self.func.__name__}')
        return self.func(*args, **kwargs)


@CountCalls
def sync_stock(product_id: int):
    """同步库存"""
    return f'商品{product_id}库存已同步'


# ====== 演示函数 ======
def demo_basic_decorator() -> None:
    """基本无参装饰器"""
    print('=== 基本装饰器 @timer ===')
    total = calculate_total([99.5, 199.0, 49.9, 2999.0])
    print(f'订单总额: ¥{total:.2f}')
    # 验证 wraps 保留的元信息
    print(f'函数名: {calculate_total.__name__}')     # calculate_total（不是 wrapper）
    print(f'文档: {calculate_total.__doc__}')


def demo_log_decorator() -> None:
    """日志装饰器"""
    print('=== 日志装饰器 @log ===')
    products = {1: {'name': '手机', 'price': 2999.0}}
    # 正常调用
    p = find_product(1, products)
    print(f'找到: {p}')
    # 异常调用
    try:
        find_product(999, products)
    except KeyError:
        print('（异常已被重新抛出）')


def demo_stacked_decorators() -> None:
    """装饰器堆叠"""
    print('=== 装饰器堆叠 ===')
    print('应用顺序：log 先（内层），timer 后（外层）')
    print('执行顺序：timer 前置 → log 前置 → 原函数 → log 后置 → timer 后置')
    print('-' * 50)
    result = process_order(1001, 5998.0)
    print(f'结果: {result}')


def demo_class_decorator() -> None:
    """类装饰器：保存状态"""
    print('=== 类装饰器（统计调用次数） ===')
    for _ in range(3):
        sync_stock(1)
    print(f'总调用次数: {sync_stock.count}')
    # 类装饰器也能保留元信息
    print(f'函数名: {sync_stock.__name__}')


def demo_wraps_importance() -> None:
    """演示 functools.wraps 的重要性"""
    print('=== functools.wraps 的作用 ===')

    # 不加 wraps 的装饰器
    def bad_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    @bad_decorator
    def original():
        """原始文档"""
        return 'original'

    print(f'不加 wraps: __name__={original.__name__}, __doc__={original.__doc__}')
    # __name__ 是 'wrapper'，__doc__ 是 None → 元信息丢失！

    print(f'加了 wraps: __name__={calculate_total.__name__}, __doc__={calculate_total.__doc__}')


def demo_eshop_scenario() -> None:
    """电商场景：组合使用装饰器"""
    print('=== 电商场景：带日志和计时的库存计算 ===')

    @timer
    @log
    def calc_inventory_value(products: dict) -> float:
        """计算库存总价值"""
        time.sleep(0.01)
        return sum(p['price'] * p['stock'] for p in products.values())

    products = {
        1: {'name': '手机', 'price': 2999.0, 'stock': 100},
        2: {'name': '耳机', 'price': 399.0, 'stock': 50},
        3: {'name': '键盘', 'price': 599.0, 'stock': 30},
    }
    value = calc_inventory_value(products)
    print(f'库存总价值: ¥{value:.2f}')


def main() -> None:
    demos = [
        demo_basic_decorator,
        demo_log_decorator,
        demo_stacked_decorators,
        demo_class_decorator,
        demo_wraps_importance,
        demo_eshop_scenario,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
