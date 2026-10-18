# 文件用途：高级装饰器练习
# 演示带参装饰器、@retry 重试、@lru_cache 缓存、权限校验
# 电商场景：API 调用重试、商品查询缓存、管理员权限校验
# 运行方式：python advanced_decorators.py

import functools
import time
import random
from functools import lru_cache


# ====== 带参装饰器：三层嵌套 ======
def repeat(n: int):
    """带参装饰器：重复执行 n 次"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def retry(times: int = 3, delay: float = 0.1):
    """带参重试装饰器：失败自动重试

    Args:
        times: 最大重试次数（含首次）
        delay: 每次重试间隔秒数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f'  [retry] {func.__name__} 第 {attempt}/{times} 次失败: {e}')
                    if attempt < times:
                        time.sleep(delay)
            # 全部失败，抛出最后一次异常
            raise last_exception
        return wrapper
    return decorator


def require_admin(func):
    """权限校验装饰器：要求当前用户是管理员"""
    @functools.wraps(func)
    def wrapper(user: dict, *args, **kwargs):
        if not user.get('is_admin'):
            raise PermissionError(
                f'用户 {user.get("name", "?")} 无管理员权限'
            )
        return func(user, *args, **kwargs)
    return wrapper


def validate_args(**validators):
    """参数验证装饰器：用 validators 校验关键字参数

    示例: @validate_args(price=lambda x: x >= 0)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for arg_name, validator in validators.items():
                if arg_name in kwargs:
                    value = kwargs[arg_name]
                    if not validator(value):
                        raise ValueError(f'参数 {arg_name}={value!r} 校验失败')
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ====== lru_cache 缓存演示 ======
@lru_cache(maxsize=128)
def get_product_cached(product_id: int) -> dict:
    """商品查询（带缓存）"""
    # 模拟耗时查询
    time.sleep(0.05)
    PRODUCTS = {
        1: {'name': '手机', 'price': 2999.0},
        2: {'name': '耳机', 'price': 399.0},
        3: {'name': '键盘', 'price': 599.0},
    }
    return PRODUCTS.get(product_id, {'name': '未知', 'price': 0})


# ====== 演示函数 ======
def demo_param_decorator() -> None:
    """带参装饰器"""
    print('=== 带参装饰器 @repeat ===')

    @repeat(3)
    def announce(msg: str) -> None:
        print(f'  公告: {msg}')

    announce('闪购开始！')


def demo_retry() -> None:
    """重试装饰器：API 调用重试"""
    print('=== 重试装饰器 @retry ===')

    # 模拟不稳定的 API 调用
    call_count = {'n': 0}

    @retry(times=4, delay=0.05)
    def fetch_order_api(order_id: int) -> dict:
        call_count['n'] += 1
        # 模拟 70% 概率失败
        if random.random() < 0.7:
            raise ConnectionError(f'API 超时（第 {call_count["n"]} 次）')
        return {'order_id': order_id, 'status': 'success'}

    random.seed(10)   # 固定种子便于复现
    try:
        result = fetch_order_api(1001)
        print(f'  成功: {result}，共调用 {call_count["n"]} 次')
    except ConnectionError as e:
        print(f'  最终失败: {e}，共调用 {call_count["n"]} 次')


def demo_lru_cache() -> None:
    """lru_cache 缓存：商品查询"""
    print('=== lru_cache 缓存 ===')
    get_product_cached.cache_clear()   # 清空缓存

    # 第一次查询：慢（未命中）
    start = time.perf_counter()
    p1 = get_product_cached(1)
    t1 = (time.perf_counter() - start) * 1000
    print(f'  第一次查询 商品1: {p1["name"]} ({t1:.1f} ms)')

    # 第二次查询：快（命中缓存）
    start = time.perf_counter()
    p2 = get_product_cached(1)
    t2 = (time.perf_counter() - start) * 1000
    print(f'  第二次查询 商品1: {p2["name"]} ({t2:.1f} ms) ← 命中缓存')

    # 查询其他商品
    get_product_cached(2)
    get_product_cached(3)
    get_product_cached(1)   # 再次命中

    # 查看缓存统计
    info = get_product_cached.cache_info()
    print(f'  缓存统计: hits={info.hits}, misses={info.misses}, '
          f'maxsize={info.maxsize}, currsize={info.currsize}')


def demo_permission() -> None:
    """权限校验装饰器"""
    print('=== 权限校验 @require_admin ===')

    @require_admin
    def delete_product(user: dict, product_id: int) -> str:
        return f'商品 {product_id} 已被 {user["name"]} 删除'

    admin = {'name': '张管理员', 'is_admin': True}
    customer = {'name': '李顾客', 'is_admin': False}

    # 管理员可执行
    result = delete_product(admin, 999)
    print(f'  {result}')

    # 普通用户被拒绝
    try:
        delete_product(customer, 999)
    except PermissionError as e:
        print(f'  拒绝: {e}')


def demo_validate_args() -> None:
    """参数验证装饰器"""
    print('=== 参数验证 @validate_args ===')

    @validate_args(
        price=lambda x: isinstance(x, (int, float)) and x > 0,
        stock=lambda x: isinstance(x, int) and x >= 0,
    )
    def create_product(name: str, *, price: float, stock: int) -> dict:
        return {'name': name, 'price': price, 'stock': stock}

    # 合法参数
    p = create_product('手机', price=2999.0, stock=100)
    print(f'  创建成功: {p}')

    # 非法价格
    try:
        create_product('测试', price=-100, stock=10)
    except ValueError as e:
        print(f'  校验失败: {e}')

    # 非法库存
    try:
        create_product('测试', price=100, stock=-5)
    except ValueError as e:
        print(f'  校验失败: {e}')


def demo_combined() -> None:
    """电商场景：组合装饰器"""
    print('=== 电商场景：缓存 + 重试 ===')

    api_calls = {'n': 0}

    @lru_cache(maxsize=32)
    @retry(times=3, delay=0.01)
    def fetch_product_price(product_id: int) -> float:
        api_calls['n'] += 1
        time.sleep(0.02)
        # 模拟偶尔失败
        if random.random() < 0.3:
            raise ConnectionError('查询失败')
        PRICES = {1: 2999.0, 2: 399.0, 3: 599.0}
        return PRICES.get(product_id, 0.0)

    random.seed(5)
    for pid in [1, 1, 2, 1, 3]:   # 商品1 查 3 次（后两次走缓存）
        try:
            price = fetch_product_price(pid)
            print(f'  商品{pid} 价格 ¥{price}')
        except Exception as e:
            print(f'  商品{pid} 查询失败: {e}')

    info = fetch_product_price.cache_info()
    print(f'  API 实际调用 {api_calls["n"]} 次，缓存命中 {info.hits} 次')


def main() -> None:
    demos = [
        demo_param_decorator,
        demo_retry,
        demo_lru_cache,
        demo_permission,
        demo_validate_args,
        demo_combined,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
