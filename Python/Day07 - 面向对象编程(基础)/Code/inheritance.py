# 文件用途：继承练习，演示单继承、super()、方法重写、isinstance/issubclass
# 电商场景：Product 基类 → DigitalProduct / PhysicalProduct 继承，Order 继承体系


# ============ 1. 继承基础 ============
class Animal:
    """基类：动物"""

    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        return f"{self.name} 发出声音"

    def __str__(self):
        return f"Animal({self.name})"


class Dog(Animal):
    """子类：狗，继承 Animal"""

    def speak(self) -> str:
        return f"{self.name} 汪汪叫"


class Cat(Animal):
    """子类：猫，继承 Animal"""

    def speak(self) -> str:
        return f"{self.name} 喵喵叫"


def demo_basic_inheritance():
    """演示基础继承"""
    print("===== 1. 继承基础 =====")
    dog = Dog("旺财")
    cat = Cat("咪咪")

    print(dog.speak())       # 重写的方法
    print(cat.speak())
    print(dog)               # 继承的 __str__


# ============ 2. super() 调用父类 ============
class Vehicle:
    """基类：交通工具"""

    def __init__(self, brand: str, speed: int):
        self.brand = brand
        self.speed = speed

    def info(self) -> str:
        return f"{self.brand} 速度 {self.speed}km/h"


class Car(Vehicle):
    """子类：汽车"""

    def __init__(self, brand: str, speed: int, wheels: int):
        super().__init__(brand, speed)    # 调用父类 __init__
        self.wheels = wheels

    def info(self) -> str:
        parent_info = super().info()      # 调用父类方法
        return f"{parent_info}，{self.wheels} 轮"


def demo_super():
    """演示 super()"""
    print("\n===== 2. super() =====")
    car = Car("Toyota", 120, 4)
    print(car.info())


# ============ 3. isinstance / issubclass ============
def demo_isinstance():
    """演示 isinstance / issubclass"""
    print("\n===== 3. isinstance / issubclass =====")
    dog = Dog("旺财")

    print(f"dog 是 Dog? {isinstance(dog, Dog)}")         # True
    print(f"dog 是 Animal? {isinstance(dog, Animal)}")   # True（子类实例也是父类实例）
    print(f"dog 是 Cat? {isinstance(dog, Cat)}")         # False
    print(f"dog 是 object? {isinstance(dog, object)}")   # True（所有类继承 object）

    print(f"\nDog 是 Animal 子类? {issubclass(Dog, Animal)}")    # True
    print(f"Dog 是 Cat 子类? {issubclass(Dog, Cat)}")            # False
    print(f"Animal 是 object 子类? {issubclass(Animal, object)}")  # True

    # isinstance 也支持元组
    print(f"\ndog 是 (Dog, Cat) 之一? {isinstance(dog, (Dog, Cat))}")  # True


# ============ 4. 电商场景：Product 继承体系 ============
class Product:
    """商品基类"""

    def __init__(self, pid: str, name: str, price: float, category: str = "general"):
        self.id = pid
        self.name = name
        self.price = price
        self.category = category

    def display(self) -> str:
        return f"[{self.id}] {self.name} - ¥{self.price}"

    def ship(self) -> str:
        """发货方式"""
        return f"正在发货 {self.name}"


class DigitalProduct(Product):
    """数字商品：电子书、软件、音乐等"""

    def __init__(self, pid: str, name: str, price: float, download_url: str, file_size: str):
        super().__init__(pid, name, price, category="digital")
        self.download_url = download_url
        self.file_size = file_size

    def display(self) -> str:
        # 调用父类 display 并扩展
        base = super().display()
        return f"{base} [数字商品, {self.file_size}]"

    def ship(self) -> str:
        # 重写：数字商品不需要物流发货
        return f"{self.name} 已发送下载链接: {self.download_url}"


class PhysicalProduct(Product):
    """实体商品：需要物流配送"""

    def __init__(self, pid: str, name: str, price: float, weight: float, stock: int):
        super().__init__(pid, name, price, category="physical")
        self.weight = weight      # 重量 kg
        self.stock = stock

    def display(self) -> str:
        base = super().display()
        return f"{base} [实体商品, {self.weight}kg, 库存 {self.stock}]"

    def ship(self) -> str:
        # 重写：实体商品走物流
        return f"{self.name} 已打包 ({self.weight}kg)，等待快递揽收"

    def calculate_shipping(self) -> float:
        """计算运费：基础价 10 元 + 每公斤 2 元"""
        return 10.0 + self.weight * 2.0


def demo_product_inheritance():
    """电商场景：Product 继承体系"""
    print("\n===== 4. 电商场景：Product 继承体系 =====")

    products = [
        DigitalProduct("D001", "Python 进阶电子书", 59.9,
                       "https://example.com/download/python-book",
                       "15MB"),
        PhysicalProduct("P001", "iPhone 15", 5999.0, 0.2, 50),
        PhysicalProduct("P002", "MacBook Pro", 12999.0, 2.1, 15),
    ]

    for p in products:
        print(p.display())
        print(f"  发货: {p.ship()}")
        # 多态：不同类型调用不同实现
        if isinstance(p, PhysicalProduct):
            print(f"  运费: ¥{p.calculate_shipping():.2f}")
        print()


# ============ 5. 电商场景：Order 继承体系 ============
class Order:
    """订单基类"""

    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items: list[str] = []
        self.status = "pending"

    def add_item(self, item: str) -> None:
        self.items.append(item)

    def total_items(self) -> int:
        return len(self.items)

    def __str__(self):
        return f"订单 {self.order_id} (客户 {self.customer_id}, {self.total_items()} 件, 状态: {self.status})"


class OnlineOrder(Order):
    """线上订单"""

    def __init__(self, order_id: str, customer_id: str, shipping_address: str):
        super().__init__(order_id, customer_id)
        self.shipping_address = shipping_address
        self.tracking_number: str | None = None

    def ship(self, tracking: str) -> None:
        self.status = "shipped"
        self.tracking_number = tracking

    def __str__(self):
        base = super().__str__()
        tracking_info = f", 快递单号: {self.tracking_number}" if self.tracking_number else ""
        return f"{base}{tracking_info}\n  收货地址: {self.shipping_address}"


class PickupOrder(Order):
    """自提订单"""

    def __init__(self, order_id: str, customer_id: str, store_location: str):
        super().__init__(order_id, customer_id)
        self.store_location = store_location
        self.pickup_code: str | None = None

    def ready_for_pickup(self, code: str) -> None:
        self.status = "ready"
        self.pickup_code = code

    def __str__(self):
        base = super().__str__()
        code_info = f", 取货码: {self.pickup_code}" if self.pickup_code else ""
        return f"{base}{code_info}\n  自提门店: {self.store_location}"


def demo_order_inheritance():
    """电商场景：Order 继承体系"""
    print("===== 5. 电商场景：Order 继承体系 =====")

    # 线上订单
    online = OnlineOrder("O001", "C001", "北京市朝阳区xx路")
    online.add_item("iPhone 15")
    online.add_item("AirPods Pro")
    online.ship("SF1234567890")
    print(online)

    print()

    # 自提订单
    pickup = PickupOrder("O002", "C002", "上海浦东店")
    pickup.add_item("MacBook Pro")
    pickup.ready_for_pickup("PICKUP-2024-001")
    print(pickup)

    # 多态：统一调用 total_items
    print(f"\n线上订单商品数: {online.total_items()}")
    print(f"自提订单商品数: {pickup.total_items()}")

    # 类型判断
    print(f"\nonline 是 OnlineOrder? {isinstance(online, OnlineOrder)}")
    print(f"online 是 Order? {isinstance(online, Order)}")
    print(f"pickup 是 OnlineOrder? {isinstance(pickup, OnlineOrder)}")


# ============ 6. 方法重写与多态 ============
def demo_polymorphism():
    """演示方法重写实现多态"""
    print("\n===== 6. 多态演示 =====")

    products: list[Product] = [
        DigitalProduct("D001", "电子书", 59.9, "url", "5MB"),
        PhysicalProduct("P001", "iPhone", 5999, 0.2, 50),
        Product("G001", "礼品卡", 100),       # 基类
    ]

    # 同一个 ship() 调用，不同类型有不同行为——多态
    print("统一调用 ship() 方法（多态）:")
    for p in products:
        print(f"  {p.name}: {p.ship()}")


if __name__ == "__main__":
    demo_basic_inheritance()
    demo_super()
    demo_isinstance()
    demo_product_inheritance()
    demo_order_inheritance()
    demo_polymorphism()
    print("\n✅ 继承练习全部完成")
