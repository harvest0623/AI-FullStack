# 文件用途：自定义异常练习
# 定义电商异常体系：EshopError 基类及 4 个子类、raise from 异常链
# 电商场景：完整的异常处理体系
# 运行方式：python custom_exceptions.py

import json
from pathlib import Path


# ====== 自定义异常体系 ======
class EshopError(Exception):
    """电商业务异常基类

    所有电商业务相关异常都继承此类，
    上层只需捕获 EshopError 即可统一处理。
    """

    def __init__(self, message: str, code: str = 'ESHOP_ERROR'):
        self.code = code
        super().__init__(message)


class ProductNotFoundError(EshopError):
    """商品不存在"""

    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(
            f'商品 {product_id} 不存在',
            code='PRODUCT_NOT_FOUND',
        )


class InvalidPriceError(EshopError):
    """价格非法（负数或非数字）"""

    def __init__(self, price, reason: str = ''):
        self.price = price
        super().__init__(
            f'价格非法: {price!r} ({reason})' if reason else f'价格非法: {price!r}',
            code='INVALID_PRICE',
        )


class InsufficientStockError(EshopError):
    """库存不足"""

    def __init__(self, product_id: int, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f'商品 {product_id} 库存不足: 需要 {requested}，仅剩 {available}',
            code='INSUFFICIENT_STOCK',
        )


class OrderError(EshopError):
    """订单相关错误"""

    def __init__(self, message: str, order_id: int | None = None):
        self.order_id = order_id
        super().__init__(message, code='ORDER_ERROR')


# ====== 模拟电商数据 ======
PRODUCTS = {
    1: {'name': '手机', 'price': 2999.0, 'stock': 100},
    2: {'name': '耳机', 'price': 399.0, 'stock': 50},
    3: {'name': '键盘', 'price': 599.0, 'stock': 30},
}


# ====== 业务函数 ======
def get_product(product_id: int) -> dict:
    """获取商品，不存在抛 ProductNotFoundError"""
    if product_id not in PRODUCTS:
        raise ProductNotFoundError(product_id)
    return PRODUCTS[product_id]


def set_price(product_id: int, price) -> None:
    """设置价格，校验合法性"""
    product = get_product(product_id)  # 可能抛 ProductNotFoundError
    if not isinstance(price, (int, float)):
        raise InvalidPriceError(price, f'必须是数字，收到 {type(price).__name__}')
    if price < 0:
        raise InvalidPriceError(price, '价格不能为负')
    if price == 0:
        raise InvalidPriceError(price, '价格不能为零')
    product['price'] = price


def place_order(product_id: int, qty: int) -> dict:
    """下单，校验库存"""
    product = get_product(product_id)
    if qty <= 0:
        raise OrderError(f'下单数量必须为正，收到 {qty}')
    if qty > product['stock']:
        raise InsufficientStockError(product_id, qty, product['stock'])
    product['stock'] -= qty
    return {
        'product_id': product_id,
        'name': product['name'],
        'qty': qty,
        'total': round(product['price'] * qty, 2),
    }


def load_products_from_json(path: Path) -> dict:
    """从 JSON 加载商品，异常链包装"""
    try:
        text = path.read_text(encoding='utf-8')
        data = json.loads(text)
    except FileNotFoundError as e:
        # raise from 保留原始异常因果链
        raise EshopError(f'商品数据文件不存在: {path}', code='DATA_FILE_MISSING') from e
    except json.JSONDecodeError as e:
        raise EshopError(f'商品数据 JSON 格式错误: {path}', code='DATA_FORMAT_ERROR') from e
    except Exception as e:
        # 兜底，把未知异常包装成业务异常
        raise EshopError(f'加载商品数据时发生未知错误: {e}', code='UNKNOWN') from e

    # 校验数据结构
    if not isinstance(data, dict):
        raise EshopError('商品数据必须是字典结构', code='DATA_STRUCTURE_ERROR')
    return data


# ====== 演示场景 ======
def demo_basic_custom_exception() -> None:
    """基本自定义异常：商品不存在"""
    print('=== 自定义异常：商品不存在 ===')
    try:
        get_product(999)
    except ProductNotFoundError as e:
        print(f'捕获: {type(e).__name__}: {e}')
        print(f'  code={e.code}, product_id={e.product_id}')
        print(f'  是 EshopError 子类: {isinstance(e, EshopError)}')
        print(f'  是 Exception 子类: {isinstance(e, Exception)}')


def demo_invalid_price() -> None:
    """价格校验异常"""
    print('=== 价格校验异常 ===')
    test_cases = [
        (1, -100),       # 负数
        (1, 0),          # 零
        (1, 'abc'),      # 非数字
        (1, 1999.0),     # 正常
        (999, 100),      # 商品不存在
    ]
    for pid, price in test_cases:
        try:
            set_price(pid, price)
            print(f'  商品{pid} 价格设为 {price} ✓')
        except InvalidPriceError as e:
            print(f'  商品{pid} 价格{price!r} ✗ {e} (code={e.code})')
        except ProductNotFoundError as e:
            print(f'  商品{pid} ✗ {e} (code={e.code})')


def demo_insufficient_stock() -> None:
    """库存不足异常"""
    print('=== 库存不足异常 ===')
    # 先重置库存（前面可能改过）
    PRODUCTS[1]['stock'] = 100
    orders = [
        (1, 2),     # 正常
        (1, 200),   # 超库存
        (1, -5),    # 负数
        (3, 30),    # 刚好够
    ]
    for pid, qty in orders:
        try:
            result = place_order(pid, qty)
            print(f'  下单成功: {result}')
        except InsufficientStockError as e:
            print(f'  下单失败: {e} (code={e.code})')
            print(f'    需要 {e.requested}, 仅剩 {e.available}')
        except OrderError as e:
            print(f'  下单失败: {e} (code={e.code})')
        except ProductNotFoundError as e:
            print(f'  下单失败: {e} (code={e.code})')


def demo_exception_chain() -> None:
    """异常链：raise from 保留原始异常"""
    print('=== 异常链 ===')
    # 文件不存在的场景
    path = Path('data') / 'missing_products_chain.json'
    try:
        load_products_from_json(path)
    except EshopError as e:
        print(f'业务异常: {e}')
        print(f'  code: {e.code}')
        print(f'  原始异常 __cause__: {e.__cause__}')
        print(f'  原始异常类型: {type(e.__cause__).__name__}')
        print(f'  原始异常信息: {e.__cause__}')

    print()
    # JSON 格式错误的场景
    bad_path = Path('data') / 'bad_chain.json'
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_text('{invalid json', encoding='utf-8')
    try:
        load_products_from_json(bad_path)
    except EshopError as e:
        print(f'业务异常: {e}')
        print(f'  code: {e.code}')
        print(f'  原始异常: {type(e.__cause__).__name__}: {e.__cause__}')


def demo_unified_catch() -> None:
    """统一捕获：上层只捕获 EshopError 基类"""
    print('=== 统一捕获 EshopError ===')
    operations = [
        ('查询商品', lambda: get_product(999)),
        ('设置价格', lambda: set_price(1, -50)),
        ('下单', lambda: place_order(2, 9999)),
        ('下单负数', lambda: place_order(1, -1)),
    ]
    for name, op in operations:
        try:
            op()
            print(f'  {name}: 成功')
        except EshopError as e:
            # 一个 except 捕获所有业务异常
            print(f'  {name}: 失败 [{e.code}] {e}')


def main() -> None:
    demos = [
        demo_basic_custom_exception,
        demo_invalid_price,
        demo_insufficient_stock,
        demo_exception_chain,
        demo_unified_catch,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
