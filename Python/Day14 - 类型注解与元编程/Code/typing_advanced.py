# 文件用途：高级类型练习
# 演示内容：TypeVar/Generic/Protocol/Callable/Literal/TypedDict
# 电商场景：泛型 Repository[T]、Protocol 定义 Repository 接口、TypedDict 定义 API 响应
# Python 3.10+ 可运行
# mypy 检查命令：mypy typing_advanced.py --strict

from dataclasses import dataclass, field
from typing import (
    TypeVar,
    Generic,
    Protocol,
    Callable,
    Literal,
    TypedDict,
    TypeAlias,
    NewType,
    Any,
)


# ============================================================
# 1. TypeVar 泛型类型变量
# ============================================================

# 无约束 TypeVar
T = TypeVar("T")

# 约束 TypeVar（只能是 int 或 float）
Numeric = TypeVar("Numeric", int, float)

# bound TypeVar（必须是某类或其子类）
class Entity:
    id: int

E = TypeVar("E", bound=Entity)


def first_item(items: list[T]) -> T | None:
    """获取列表第一个元素（输入输出类型一致）"""
    return items[0] if items else None


def max_value(a: Numeric, b: Numeric) -> Numeric:
    """比较两个数值（约束为 int 或 float）"""
    return a if a > b else b


# ============================================================
# 2. Generic 泛型类 - 泛型 Repository[T]
# ============================================================

@dataclass
class Product:
    """商品模型"""
    id: int
    name: str
    price: float
    stock: int = 0


@dataclass
class Order:
    """订单模型"""
    id: int
    customer_id: int
    total: float


class Repository(Generic[T]):
    """泛型仓储基类

    使用方式：
        product_repo: Repository[Product] = Repository()
        product_repo.save(Product(1, "iPhone", 9999.0))
    """

    def __init__(self) -> None:
        self._data: dict[int, T] = {}

    def get(self, id: int) -> T | None:
        """根据 ID 获取"""
        return self._data.get(id)

    def save(self, entity: T) -> None:
        """保存（需要有 id 属性）"""
        # 通过运行时获取 id
        entity_id = getattr(entity, "id", None)
        if entity_id is None:
            raise ValueError("实体必须有 id 属性")
        self._data[entity_id] = entity

    def delete(self, id: int) -> bool:
        """删除"""
        if id in self._data:
            del self._data[id]
            return True
        return False

    def list_all(self) -> list[T]:
        """列出全部"""
        return list(self._data.values())

    def count(self) -> int:
        return len(self._data)


# ============================================================
# 3. Protocol 结构子类型 - 定义 Repository 接口
# ============================================================

class Identifiable(Protocol):
    """有 id 属性的对象（Protocol 定义接口）"""
    id: int


class ReadOnlyRepository(Protocol[T]):
    """只读仓储接口（Protocol 定义）"""
    def get(self, id: int) -> T | None: ...
    def list_all(self) -> list[T]: ...
    def count(self) -> int: ...


def print_entity(repo: ReadOnlyRepository[T], id: int) -> None:
    """打印实体（接受任何符合 ReadOnlyRepository 协议的对象）"""
    entity = repo.get(id)
    if entity:
        print(f"  找到：{entity}")
    else:
        print(f"  ID {id} 不存在")


# ============================================================
# 4. Callable 可调用类型 - 回调函数
# ============================================================

# 定义回调类型
PriceCalculator: TypeAlias = Callable[[Product, int], float]
FilterFunc: TypeAlias = Callable[[Product], bool]
Transformer: TypeAlias = Callable[[Product], str]


def calculate_price(product: Product, qty: int, calc: PriceCalculator) -> float:
    """使用传入的计算函数"""
    return calc(product, qty)


def default_calculator(p: Product, qty: int) -> float:
    return round(p.price * qty, 2)


def discount_calculator(p: Product, qty: int) -> float:
    """团购折扣计算"""
    base = p.price * qty
    if qty >= 10:
        return round(base * 0.8, 2)  # 8 折
    elif qty >= 5:
        return round(base * 0.9, 2)  # 9 折
    return round(base, 2)


def filter_products(products: list[Product], predicate: FilterFunc) -> list[Product]:
    """用谓词函数过滤商品"""
    return [p for p in products if predicate(p)]


def transform_products(products: list[Product], transformer: Transformer) -> list[str]:
    """转换商品列表"""
    return [transformer(p) for p in products]


# ============================================================
# 5. TypedDict 类型化字典 - API 响应
# ============================================================

class ProductResponse(TypedDict):
    """商品 API 响应"""
    id: int
    name: str
    price: float
    stock: int
    category: str


class OrderItemResponse(TypedDict):
    """订单项 API 响应"""
    product_id: int
    product_name: str
    price: float
    qty: int
    subtotal: float


class OrderResponse(TypedDict):
    """订单 API 响应"""
    id: int
    customer_id: int
    items: list[OrderItemResponse]
    total: float
    status: Literal["pending", "paid", "shipped", "delivered", "cancelled"]


class PaginatedResponse(TypedDict):
    """分页响应"""
    data: list[ProductResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


def create_product_response(product: Product) -> ProductResponse:
    """创建商品 API 响应"""
    return ProductResponse(
        id=product.id,
        name=product.name,
        price=product.price,
        stock=product.stock,
        category="未分类",
    )


def create_paginated_response(
    products: list[Product],
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """创建分页响应"""
    start = (page - 1) * page_size
    end = start + page_size
    page_data = products[start:end]
    return PaginatedResponse(
        data=[create_product_response(p) for p in page_data],
        total=len(products),
        page=page,
        page_size=page_size,
        has_next=end < len(products),
    )


# ============================================================
# 6. NewType 新类型 - 防止混淆
# ============================================================

# 不同语义的 ID 用 NewType 区分
ProductId = NewType("ProductId", int)
CustomerId = NewType("CustomerId", int)
OrderId = NewType("OrderId", int)


def get_product(pid: ProductId) -> Product | None:
    """获取商品（参数必须是 ProductId 类型）"""
    products = {1: Product(1, "iPhone", 9999.0, 50)}
    return products.get(pid)


def get_customer_orders(cid: CustomerId) -> list[Order]:
    """获取客户订单（参数必须是 CustomerId 类型）"""
    return [Order(1, cid, 199.0)]


# ============================================================
# 7. Any 类型 - 谨慎使用
# ============================================================

def log_data(data: Any) -> None:
    """记录任意类型数据（谨慎使用 Any）"""
    print(f"  [LOG] {type(data).__name__}: {data}")


# ============================================================
# 演示主函数
# ============================================================

def demo_typevar() -> None:
    """演示 TypeVar"""
    print("=" * 60)
    print("示例 1：TypeVar 泛型类型变量")
    print("=" * 60)

    print(f"first_item([1,2,3]) = {first_item([1, 2, 3])}")
    print(f"first_item(['a','b']) = {first_item(['a', 'b'])}")
    print(f"first_item([]) = {first_item([])}")

    print(f"max_value(3, 5) = {max_value(3, 5)}")
    print(f"max_value(3.14, 2.71) = {max_value(3.14, 2.71)}")


def demo_generic_repository() -> None:
    """演示 Generic 泛型 Repository"""
    print("\n" + "=" * 60)
    print("示例 2：Generic 泛型 Repository[T]")
    print("=" * 60)

    # 商品仓储
    product_repo: Repository[Product] = Repository()
    product_repo.save(Product(1, "iPhone", 9999.0, 50))
    product_repo.save(Product(2, "MacBook", 8999.0, 30))
    product_repo.save(Product(3, "AirPods", 1999.0, 100))

    print("所有商品：")
    for p in product_repo.list_all():
        print(f"  {p}")

    found = product_repo.get(2)
    print(f"\n查找 ID=2: {found}")

    deleted = product_repo.delete(1)
    print(f"删除 ID=1: {deleted}, 剩余 {product_repo.count()} 个")

    # 订单仓储（同一个类，不同类型参数）
    order_repo: Repository[Order] = Repository()
    order_repo.save(Order(100, 1001, 199.0))
    print(f"\n订单仓储: {order_repo.list_all()}")


def demo_protocol() -> None:
    """演示 Protocol 结构子类型"""
    print("\n" + "=" * 60)
    print("示例 3：Protocol 结构子类型")
    print("=" * 60)

    # Repository 实现了 ReadOnlyRepository 协议（有 get/list_all/count 方法）
    # 无需显式继承，结构匹配即可
    repo: Repository[Product] = Repository()
    repo.save(Product(1, "iPhone", 9999.0, 50))

    print_entity(repo, 1)
    print_entity(repo, 999)


def demo_callable() -> None:
    """演示 Callable 可调用类型"""
    print("\n" + "=" * 60)
    print("示例 4：Callable 可调用类型")
    print("=" * 60)

    p = Product(1, "iPhone", 9999.0, 50)

    # 使用不同计算函数
    default_price = calculate_price(p, 3, default_calculator)
    print(f"默认计算 3 件: {default_price}")

    discount_price = calculate_price(p, 10, discount_calculator)
    print(f"团购 10 件: {discount_price}")

    # 过滤商品
    products = [
        Product(1, "iPhone", 9999.0, 50),
        Product(2, "AirPods", 1999.0, 100),
        Product(3, "MacBook", 8999.0, 30),
        Product(4, "iPad", 3999.0, 0),
    ]
    in_stock = filter_products(products, lambda p: p.stock > 0)
    print(f"\n有库存商品: {[p.name for p in in_stock]}")

    cheap = filter_products(products, lambda p: p.price < 5000)
    print(f"5000 以下商品: {[p.name for p in cheap]}")

    # 转换商品
    names = transform_products(products, lambda p: f"【{p.name}】{p.price}元")
    print(f"转换结果: {names[:2]}")


def demo_typeddict() -> None:
    """演示 TypedDict API 响应"""
    print("\n" + "=" * 60)
    print("示例 5：TypedDict API 响应")
    print("=" * 60)

    products = [
        Product(1, "iPhone", 9999.0, 50),
        Product(2, "MacBook", 8999.0, 30),
        Product(3, "AirPods", 1999.0, 100),
        Product(4, "iPad", 3999.0, 20),
    ]

    # 单个商品响应
    resp = create_product_response(products[0])
    print(f"单商品响应: {resp}")

    # 分页响应
    page1 = create_paginated_response(products, page=1, page_size=2)
    print(f"\n第 1 页: total={page1['total']}, has_next={page1['has_next']}")
    for item in page1["data"]:
        print(f"  {item}")

    page2 = create_paginated_response(products, page=2, page_size=2)
    print(f"\n第 2 页: has_next={page2['has_next']}")
    for item in page2["data"]:
        print(f"  {item}")


def demo_newtype() -> None:
    """演示 NewType 新类型"""
    print("\n" + "=" * 60)
    print("示例 6：NewType 新类型（防止 ID 混淆）")
    print("=" * 60)

    pid = ProductId(1)
    cid = CustomerId(1001)

    product = get_product(pid)
    print(f"商品: {product}")

    orders = get_customer_orders(cid)
    print(f"客户订单: {orders}")

    print("\nNewType 在运行时仍是 int，但类型检查器视为不同类型")
    print("这样能防止把 ProductId 误传给需要 CustomerId 的函数")


def main() -> None:
    """主函数"""
    demo_typevar()
    demo_generic_repository()
    demo_protocol()
    demo_callable()
    demo_typeddict()
    demo_newtype()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("提示：运行 mypy typing_advanced.py --strict 进行类型检查")
    print("=" * 60)


if __name__ == "__main__":
    main()
