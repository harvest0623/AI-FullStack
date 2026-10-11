# 文件用途：@dataclass 与 Enum 练习，演示数据类、field、frozen、枚举
# 电商场景：完整的数据模型 Product/Order 定义 + OrderStatus 枚举

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Any


# ============ 1. @dataclass 基础 ============
@dataclass
class ProductBasic:
    """基础数据类：自动生成 __init__/__repr__/__eq__"""
    id: int
    name: str
    price: float
    stock: int = 0


def demo_dataclass_basics():
    """演示 @dataclass 基础"""
    print("===== 1. @dataclass 基础 =====")
    p1 = ProductBasic(1, "iPhone", 5999.0, 50)
    p2 = ProductBasic(2, "AirPods", 199.0, 200)
    p3 = ProductBasic(1, "iPhone", 5999.0, 50)    # 与 p1 相等

    print(f"p1: {p1}")                # __repr__ 自动生成
    print(f"p2: {p2}")
    print(f"p1 == p3: {p1 == p3}")    # __eq__ 自动生成（比较所有字段）
    print(f"p1 == p2: {p1 == p2}")


# ============ 2. field 与可变默认值 ============
@dataclass
class OrderBasic:
    """演示 field(default_factory=...) 处理可变默认值"""
    id: int
    customer_id: str
    # ❌ 错误：items: list = []  →  ValueError: mutable default not allowed
    items: list = field(default_factory=list)         # ✅ 正确
    metadata: dict = field(default_factory=dict)      # ✅ 正确

    def add_item(self, item: str) -> None:
        self.items.append(item)


def demo_field():
    """演示 field 与可变默认值"""
    print("\n===== 2. field 与可变默认值 =====")
    o1 = OrderBasic(1, "C001")
    o2 = OrderBasic(2, "C002")

    # 每个实例的 items 独立（不会共享）
    o1.add_item("iPhone")
    o2.add_item("iPad")
    print(f"o1.items: {o1.items}")
    print(f"o2.items: {o2.items}")

    # 带 metadata
    o3 = OrderBasic(3, "C003", items=["Mouse"], metadata={"source": "web"})
    print(f"o3: {o3}")


# ============ 3. frozen=True 不可变数据类 ============
@dataclass(frozen=True)
class Point:
    """不可变数据类：可哈希，可作字典键"""
    x: float
    y: float


@dataclass(frozen=True)
class Customer:
    """不可变客户类"""
    id: int
    name: str
    email: str


def demo_frozen():
    """演示 frozen=True"""
    print("\n===== 3. frozen=True 不可变数据类 =====")
    p = Point(3.0, 4.0)
    print(f"Point: {p}")

    # 不可变：不能修改属性
    try:
        p.x = 5.0       # FrozenInstanceError
    except Exception as e:
        print(f"修改失败: {type(e).__name__}")

    # 可哈希：可作字典键/集合元素
    points = {Point(0, 0), Point(1, 1), Point(0, 0)}
    print(f"集合去重: {len(points)} 个点")

    d = {Point(1, 1): "原点"}
    print(f"作字典键: {d[Point(1, 1)]}")

    # 客户对象也可哈希
    c = Customer(1, "Tom", "tom@example.com")
    print(f"Customer 可哈希: {hash(c) is not None}")


# ============ 4. order=True 支持排序 ============
@dataclass(order=True)
class Priority:
    """可排序数据类：按字段排序"""
    # 注意：compare=False 的字段不参与比较
    priority: int
    name: str = field(compare=False)    # name 不参与比较
    description: str = field(default="", compare=False)


def demo_order():
    """演示 order=True"""
    print("\n===== 4. order=True 支持排序 =====")
    tasks = [
        Priority(3, "低优先级任务"),
        Priority(1, "高优先级任务"),
        Priority(2, "中优先级任务"),
        Priority(1, "另一个高优先级"),
    ]

    # 按 priority 排序（name 不影响）
    for task in sorted(tasks):
        print(f"  {task.priority} - {task.name}")

    # 比较运算
    p1 = Priority(1, "A")
    p2 = Priority(2, "B")
    print(f"\n{p1} < {p2}: {p1 < p2}")


# ============ 5. Enum 枚举基础 ============
class OrderStatus(Enum):
    """订单状态枚举：用有意义的名字替代魔法数字"""
    PENDING = 1
    PAID = 2
    SHIPPED = 3
    DELIVERED = 4
    CANCELLED = 5


def demo_enum_basics():
    """演示 Enum 基础"""
    print("\n===== 5. Enum 枚举基础 =====")
    status = OrderStatus.PAID

    # 属性
    print(f"status: {status}")
    print(f"status.name: {status.name}")      # 'PAID'
    print(f"status.value: {status.value}")    # 2

    # 通过名称访问
    s = OrderStatus["SHIPPED"]
    print(f"OrderStatus['SHIPPED']: {s}")

    # 通过值访问
    s = OrderStatus(3)
    print(f"OrderStatus(3): {s}")

    # 比较
    print(f"\nPAID == PAID: {OrderStatus.PAID == OrderStatus.PAID}")
    print(f"PAID is PAID: {OrderStatus.PAID is OrderStatus.PAID}")

    # 遍历所有成员
    print("\n所有订单状态:")
    for s in OrderStatus:
        print(f"  {s.name} = {s.value}")

    # 成员判断
    print(f"\nPAID in OrderStatus: {OrderStatus.PAID in OrderStatus}")


# ============ 6. auto() 自动赋值 ============
class ProductStatus(Enum):
    """商品状态：用 auto() 自动赋值"""
    DRAFT = auto()
    ACTIVE = auto()
    DISCONTINUED = auto()
    OUT_OF_STOCK = auto()


def demo_auto():
    """演示 auto()"""
    print("\n===== 6. auto() 自动赋值 =====")
    for s in ProductStatus:
        print(f"  {s.name} = {s.value}")


# ============ 7. IntEnum ============
class Priority2(IntEnum):
    """IntEnum：可与整数比较"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


def demo_intenum():
    """演示 IntEnum"""
    print("\n===== 7. IntEnum =====")
    p = Priority2.HIGH
    print(f"Priority2.HIGH: {p}, value: {int(p)}")

    # 可与整数比较
    print(f"HIGH > 2: {p > 2}")
    print(f"HIGH == 3: {p == 3}")

    # 可用于需要 int 的场景
    priorities = [Priority2.LOW, Priority2.HIGH, Priority2.MEDIUM]
    print(f"排序: {[p.name for p in sorted(priorities)]}")


# ============ 8. 电商场景：完整数据模型 ============
class OrderStatusEnum(Enum):
    """订单状态枚举"""
    PENDING = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


@dataclass
class Product:
    """商品数据模型"""
    id: int
    name: str
    price: float
    stock: int = 0
    category: str = "general"
    tags: list = field(default_factory=list)

    def __post_init__(self):
        """dataclass 初始化后调用的钩子，用于数据校验"""
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
    """订单数据模型"""
    id: int
    customer_id: str
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatusEnum = OrderStatusEnum.PENDING
    created_at: str = ""

    def add_item(self, product: Product, qty: int = 1) -> None:
        item = OrderItem(product.id, product.name, product.price, qty)
        self.items.append(item)

    @property
    def total(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    def can_cancel(self) -> bool:
        """只有待支付状态可以取消"""
        return self.status == OrderStatusEnum.PENDING

    def pay(self) -> None:
        if self.status != OrderStatusEnum.PENDING:
            raise ValueError(f"当前状态 {self.status.name} 不能支付")
        self.status = OrderStatusEnum.PAID

    def ship(self) -> None:
        if self.status != OrderStatusEnum.PAID:
            raise ValueError(f"当前状态 {self.status.name} 不能发货")
        self.status = OrderStatusEnum.SHIPPED


def demo_ecommerce_models():
    """电商场景：完整数据模型"""
    print("\n===== 8. 电商场景：完整数据模型 =====")

    # 创建商品
    products = [
        Product(1, "iPhone 15", 5999.0, 50, "phone", ["new", "popular"]),
        Product(2, "AirPods Pro", 199.0, 200, "accessory", ["hot"]),
        Product(3, "iPad Air", 4499.0, 30, "tablet"),
    ]
    print("商品列表:")
    for p in products:
        print(f"  {p}")

    # 校验演示
    print("\n数据校验:")
    try:
        bad = Product(99, "Test", -100)
    except ValueError as e:
        print(f"  ❌ {e}")

    # 创建订单
    order = Order(1001, "C001", created_at="2024-01-15")
    order.add_item(products[0], 1)
    order.add_item(products[1], 2)
    order.add_item(products[2], 1)

    print(f"\n订单: {order}")
    print(f"订单项数: {len(order.items)}")
    print(f"订单总价: ¥{order.total}")
    print(f"订单状态: {order.status.name}")

    # 状态转换
    print("\n状态转换:")
    print(f"  初始: {order.status.name}")
    order.pay()
    print(f"  支付后: {order.status.name}")
    order.ship()
    print(f"  发货后: {order.status.name}")

    # 非法转换
    try:
        order.pay()    # 已发货不能再次支付
    except ValueError as e:
        print(f"  ❌ {e}")

    # 取消订单校验
    order2 = Order(1002, "C002")
    print(f"\n新订单可取消? {order2.can_cancel()}")
    order2.pay()
    print(f"支付后可取消? {order2.can_cancel()}")


if __name__ == "__main__":
    demo_dataclass_basics()
    demo_field()
    demo_frozen()
    demo_order()
    demo_enum_basics()
    demo_auto()
    demo_intenum()
    demo_ecommerce_models()
    print("\n✅ @dataclass 与 Enum 练习全部完成")
