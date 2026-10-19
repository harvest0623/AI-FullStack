# 文件用途：类型注解基础练习
# 演示内容：基本注解/函数注解/复合类型/Optional/Union
# 电商场景：Product/Order 模型类型注解、函数签名注解、mypy 检查演示
# Python 3.10+ 可运行
# mypy 检查命令：mypy type_hints.py --strict

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


# ============================================================
# 1. 基本类型注解
# ============================================================

# 变量注解
product_name: str = "iPhone 15 Pro"
product_price: float = 9999.0
stock_count: int = 100
is_available: bool = True
description: None = None


# ============================================================
# 2. 复合类型注解（3.9+ 内置泛型）
# ============================================================

# 列表
prices: list[float] = [99.0, 199.0, 299.0]
product_ids: list[int] = [1, 2, 3, 4, 5]

# 字典
stock: dict[str, int] = {"iPhone": 10, "MacBook": 5}
product_catalog: dict[int, str] = {1: "iPhone", 2: "MacBook"}

# 嵌套复合类型
order_items_map: dict[str, list[int]] = {
    "ORD-001": [1, 2, 3],
    "ORD-002": [4, 5],
}

# 元组
point: tuple[int, str] = (1, "商品A")
coordinates: tuple[float, float, float] = (1.0, 2.0, 3.0)
variable_length: tuple[int, ...] = (1, 2, 3, 4, 5)

# 集合
tags: set[str] = {"电子产品", "手机", "苹果"}


# ============================================================
# 3. 枚举与 Literal 字面量类型
# ============================================================

class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# Literal 限定字面量值
StatusLiteral = Literal["pending", "paid", "shipped", "delivered", "cancelled"]
HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


def update_status(order_id: int, status: StatusLiteral) -> bool:
    """更新订单状态（Literal 限制参数取值）"""
    print(f"订单 {order_id} 状态更新为 {status}")
    return True


def make_request(url: str, method: HttpMethod = "GET") -> str:
    """模拟 HTTP 请求（Literal 限制 method）"""
    return f"{method} {url}"


# ============================================================
# 4. Optional 与 Union（3.10+ 用 | 语法）
# ============================================================

def find_product(product_id: int) -> dict[str, object] | None:
    """查找商品，可能返回 None"""
    if product_id in (1, 2, 3):
        return {"id": product_id, "name": f"商品-{product_id}"}
    return None


def parse_id(value: str | int) -> int:
    """Union 类型：参数可以是 str 或 int"""
    if isinstance(value, str):
        return int(value)
    return value


def get_discount(member_level: str | None = None) -> float:
    """Optional 参数"""
    if member_level is None:
        return 1.0
    discounts = {"gold": 0.8, "silver": 0.9, "bronze": 0.95}
    return discounts.get(member_level, 1.0)


# ============================================================
# 5. 函数注解完整示例
# ============================================================

def calculate_order_total(
    items: list[dict[str, float | int | str]],
    discount: float = 1.0,
    tax_rate: float = 0.13,
) -> float:
    """
    计算订单总金额

    Args:
        items: 商品列表，每个商品是 dict
        discount: 折扣（1.0 表示无折扣）
        tax_rate: 税率

    Returns:
        含税总金额
    """
    subtotal = sum(item["price"] * item["qty"] for item in items)  # type: ignore
    discounted = subtotal * discount
    return round(discounted * (1 + tax_rate), 2)


def batch_update_prices(
    updates: dict[int, float],
    notify: bool = True,
) -> dict[int, bool]:
    """批量更新价格"""
    results: dict[int, bool] = {}
    for pid, new_price in updates.items():
        if new_price < 0:
            results[pid] = False
            continue
        # 模拟更新
        results[pid] = True
        if notify:
            print(f"  商品 {pid} 价格更新为 {new_price}")
    return results


# ============================================================
# 6. 电商数据模型（dataclass + 类型注解）
# ============================================================

@dataclass
class Product:
    """商品模型"""
    id: int
    name: str
    price: float
    stock: int = 0
    category: str = "未分类"
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError("价格不能为负")
        if self.stock < 0:
            raise ValueError("库存不能为负")


@dataclass
class OrderItem:
    """订单项"""
    product_id: int
    product_name: str
    price: float
    qty: int

    @property
    def subtotal(self) -> float:
        return round(self.price * self.qty, 2)


@dataclass
class Order:
    """订单模型"""
    id: int
    customer_id: int
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)


# ============================================================
# 7. 演示主函数
# ============================================================

def demo_basic_annotations() -> None:
    """演示基本类型注解"""
    print("=" * 60)
    print("示例 1：基本类型注解")
    print("=" * 60)
    print(f"商品名: {product_name}")
    print(f"价格: {product_price}")
    print(f"库存: {stock_count}")
    print(f"标签: {tags}")


def demo_compound_types() -> None:
    """演示复合类型注解"""
    print("\n" + "=" * 60)
    print("示例 2：复合类型注解")
    print("=" * 60)
    print(f"价格列表: {prices}")
    print(f"库存字典: {stock}")
    print(f"订单映射: {order_items_map}")
    print(f"变长元组: {variable_length}")


def demo_optional_union() -> None:
    """演示 Optional 与 Union"""
    print("\n" + "=" * 60)
    print("示例 3：Optional 与 Union")
    print("=" * 60)

    result = find_product(1)
    print(f"查找商品 1: {result}")
    print(f"查找商品 999: {find_product(999)}")

    print(f"parse_id('123') = {parse_id('123')}")
    print(f"parse_id(456) = {parse_id(456)}")

    print(f"金牌会员折扣: {get_discount('gold')}")
    print(f"无会员折扣: {get_discount()}")


def demo_literal() -> None:
    """演示 Literal 字面量类型"""
    print("\n" + "=" * 60)
    print("示例 4：Literal 字面量类型")
    print("=" * 60)

    update_status(1, "paid")
    update_status(2, "shipped")

    print(make_request("/api/products"))
    print(make_request("/api/orders", "POST"))


def demo_dataclass_models() -> None:
    """演示 dataclass 电商模型"""
    print("\n" + "=" * 60)
    print("示例 5：dataclass 电商数据模型")
    print("=" * 60)

    # 创建商品
    p1 = Product(
        id=1,
        name="iPhone 15 Pro",
        price=9999.0,
        stock=50,
        category="手机",
        tags=["苹果", "旗舰"],
    )
    p2 = Product(
        id=2,
        name="MacBook Air M3",
        price=8999.0,
        stock=30,
        category="笔记本",
        tags=["苹果", "轻薄本"],
    )
    print(f"商品 1: {p1}")
    print(f"商品 2: {p2}")

    # 创建订单
    order = Order(id=1, customer_id=1001)
    order.add_item(OrderItem(1, "iPhone 15 Pro", 9999.0, 1))
    order.add_item(OrderItem(2, "AirPods Pro", 1999.0, 2))
    print(f"\n订单: {order}")
    print(f"订单总金额: {order.total}")
    print(f"订单状态: {order.status.value}")


def demo_function_annotations() -> None:
    """演示带注解的函数"""
    print("\n" + "=" * 60)
    print("示例 6：函数签名注解")
    print("=" * 60)

    items = [
        {"name": "iPhone", "price": 9999.0, "qty": 1},
        {"name": "AirPods", "price": 1999.0, "qty": 2},
    ]
    total = calculate_order_total(items, discount=0.9)
    print(f"订单总金额（9 折 + 13% 税）: {total}")

    results = batch_update_prices({1: 8999.0, 2: -100.0, 3: 1299.0})
    print(f"批量更新结果: {results}")


def main() -> None:
    """主函数"""
    demo_basic_annotations()
    demo_compound_types()
    demo_optional_union()
    demo_literal()
    demo_dataclass_models()
    demo_function_annotations()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("提示：运行 mypy type_hints.py --strict 进行类型检查")
    print("=" * 60)


if __name__ == "__main__":
    main()
