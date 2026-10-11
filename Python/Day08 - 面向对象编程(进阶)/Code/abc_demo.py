# 文件用途：抽象基类 ABC 练习，演示 ABC、@abstractmethod、子类实现
# 电商场景：BaseRepository ABC → ProductRepository / OrderRepository 子类实现

from abc import ABC, abstractmethod
from typing import Any


# ============ 1. ABC 基础 ============
class Animal(ABC):
    """抽象基类：动物

    不能直接实例化，子类必须实现所有抽象方法
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def speak(self) -> str:
        """抽象方法：子类必须实现"""
        ...

    @abstractmethod
    def move(self) -> str:
        """抽象方法"""
        ...

    # 具体方法：子类直接继承
    def describe(self) -> str:
        """具体方法：所有子类共享"""
        return f"{self.__class__.__name__}({self.name}): {self.speak()}"


class Dog(Animal):
    """子类：实现所有抽象方法"""

    def speak(self) -> str:
        return f"{self.name} 汪汪叫"

    def move(self) -> str:
        return f"{self.name} 跑"


class Cat(Animal):
    """子类：实现所有抽象方法"""

    def speak(self) -> str:
        return f"{self.name} 喵喵叫"

    def move(self) -> str:
        return f"{self.name} 走"


def demo_abc_basics():
    """演示 ABC 基础"""
    print("===== 1. ABC 基础 =====")

    # 抽象类不能实例化
    try:
        animal = Animal("test")    # TypeError
    except TypeError as e:
        print(f"不能实例化抽象类: {e}")

    # 子类实现所有抽象方法后可实例化
    dog = Dog("旺财")
    cat = Cat("咪咪")
    print(dog.speak())
    print(cat.speak())
    print(dog.move())
    print(cat.describe())      # 继承的具体方法


# ============ 2. 不完整的子类 ============
class Bird(Animal):
    """只实现部分抽象方法——仍然不能实例化"""

    def speak(self) -> str:
        return f"{self.name} 叽叽喳喳"

    # 没有实现 move()


def demo_incomplete_subclass():
    """演示不完整的子类仍不能实例化"""
    print("\n===== 2. 不完整的子类 =====")
    try:
        bird = Bird("小鸟")    # 仍然抽象，没实现 move
    except TypeError as e:
        print(f"Bird 未实现 move，不能实例化: {e}")

    # 完整实现后才行
    class Sparrow(Bird):
        def move(self) -> str:
            return f"{self.name} 飞"

    sparrow = Sparrow("小麻雀")
    print(f"sparrow.speak(): {sparrow.speak()}")
    print(f"sparrow.move(): {sparrow.move()}")


# ============ 3. @abstractmethod + @property ============
class Shape(ABC):
    """抽象基类：图形"""

    @property
    @abstractmethod
    def area(self) -> float:
        """抽象属性：子类必须实现"""
        ...

    @property
    @abstractmethod
    def perimeter(self) -> float:
        """抽象属性"""
        ...


class Rectangle(Shape):
    """矩形：实现抽象属性"""

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Circle(Shape):
    """圆形：实现抽象属性"""

    def __init__(self, radius: float):
        self.radius = radius

    @property
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

    @property
    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius


def demo_abstract_property():
    """演示 @abstractmethod + @property"""
    print("\n===== 3. @abstractmethod + @property =====")

    shapes: list[Shape] = [
        Rectangle(4, 5),
        Circle(3),
    ]

    # 多态：统一接口
    for s in shapes:
        print(f"{s.__class__.__name__}: 面积={s.area:.2f}, 周长={s.perimeter:.2f}")


# ============ 4. 电商场景：BaseRepository ABC ============
class BaseRepository(ABC):
    """抽象基类：数据仓库接口

    定义所有 Repository 必须实现的 CRUD 接口
    """

    def __init__(self):
        self._data: dict[int, Any] = {}
        self._next_id = 1

    @abstractmethod
    def find(self, id: int) -> Any | None:
        """根据 ID 查找"""
        ...

    @abstractmethod
    def save(self, obj: Any) -> Any:
        """保存（新增或更新）"""
        ...

    @abstractmethod
    def delete(self, id: int) -> bool:
        """删除"""
        ...

    @abstractmethod
    def list_all(self) -> list[Any]:
        """列出所有"""
        ...

    # 具体方法：所有子类共享
    def count(self) -> int:
        """统计数量"""
        return len(self._data)

    def exists(self, id: int) -> bool:
        """是否存在"""
        return id in self._data

    def __str__(self):
        return f"{self.__class__.__name__}({self.count()} 条记录)"


class ProductRepository(BaseRepository):
    """商品仓库：实现 BaseRepository 接口"""

    def find(self, id: int) -> dict | None:
        return self._data.get(id)

    def save(self, obj: dict) -> dict:
        if "id" not in obj or obj["id"] is None:
            obj["id"] = self._next_id
            self._next_id += 1
        self._data[obj["id"]] = obj
        return obj

    def delete(self, id: int) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False

    def list_all(self) -> list[dict]:
        return list(self._data.values())

    # 扩展方法
    def find_by_category(self, category: str) -> list[dict]:
        """按分类查找"""
        return [p for p in self._data.values() if p.get("category") == category]

    def find_in_stock(self) -> list[dict]:
        """查找有库存的商品"""
        return [p for p in self._data.values() if p.get("stock", 0) > 0]


class OrderRepository(BaseRepository):
    """订单仓库：实现 BaseRepository 接口"""

    def find(self, id: int) -> dict | None:
        return self._data.get(id)

    def save(self, obj: dict) -> dict:
        if "id" not in obj or obj["id"] is None:
            obj["id"] = self._next_id
            self._next_id += 1
        self._data[obj["id"]] = obj
        return obj

    def delete(self, id: int) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False

    def list_all(self) -> list[dict]:
        return list(self._data.values())

    # 扩展方法
    def find_by_customer(self, customer_id: str) -> list[dict]:
        """按客户查找订单"""
        return [o for o in self._data.values() if o.get("customer_id") == customer_id]

    def find_by_status(self, status: str) -> list[dict]:
        """按状态查找"""
        return [o for o in self._data.values() if o.get("status") == status]


def demo_repository():
    """电商场景：BaseRepository 与子类"""
    print("\n===== 4. 电商场景：BaseRepository ABC =====")

    # 抽象类不能实例化
    try:
        repo = BaseRepository()
    except TypeError as e:
        print(f"不能实例化抽象类: {e}")

    # 使用 ProductRepository
    product_repo = ProductRepository()

    # 保存商品
    product_repo.save({"id": None, "name": "iPhone", "price": 5999, "stock": 50, "category": "phone"})
    product_repo.save({"id": None, "name": "iPad", "price": 2999, "stock": 30, "category": "tablet"})
    product_repo.save({"id": None, "name": "AirPods", "price": 199, "stock": 0, "category": "phone"})

    print(f"\n{product_repo}")
    print(f"所有商品:")
    for p in product_repo.list_all():
        print(f"  {p}")

    # 查找
    p = product_repo.find(1)
    print(f"\nfind(1): {p}")

    # 按分类查找
    phones = product_repo.find_by_category("phone")
    print(f"手机分类: {[p['name'] for p in phones]}")

    # 有库存的
    in_stock = product_repo.find_in_stock()
    print(f"有库存: {[p['name'] for p in in_stock]}")

    # 删除
    product_repo.delete(2)
    print(f"删除 ID=2 后: {product_repo}")

    # 使用 OrderRepository
    print(f"\n--- OrderRepository ---")
    order_repo = OrderRepository()
    order_repo.save({"id": None, "customer_id": "C001", "status": "paid", "total": 5999})
    order_repo.save({"id": None, "customer_id": "C001", "status": "shipped", "total": 2999})
    order_repo.save({"id": None, "customer_id": "C002", "status": "paid", "total": 199})

    print(f"{order_repo}")
    c001_orders = order_repo.find_by_customer("C001")
    print(f"C001 的订单: {len(c001_orders)} 个")
    paid_orders = order_repo.find_by_status("paid")
    print(f"已支付订单: {len(paid_orders)} 个")

    # 共享的具体方法
    print(f"\n共享方法:")
    print(f"  product_repo.count(): {product_repo.count()}")
    print(f"  product_repo.exists(1): {product_repo.exists(1)}")
    print(f"  order_repo.exists(99): {order_repo.exists(99)}")


# ============ 5. 抽象类作为类型约束 ============
def print_all(repo: BaseRepository) -> None:
    """函数参数类型为抽象基类，接受任何子类"""
    print(f"  {repo}: {repo.list_all()}")


def demo_type_constraint():
    """演示抽象类作为类型约束"""
    print("\n===== 5. 抽象类作为类型约束 =====")
    product_repo = ProductRepository()
    product_repo.save({"id": None, "name": "Test", "price": 100})

    order_repo = OrderRepository()
    order_repo.save({"id": None, "customer_id": "CX", "status": "pending"})

    # 同一个函数处理不同子类——多态
    print("ProductRepository:")
    print_all(product_repo)
    print("OrderRepository:")
    print_all(order_repo)


if __name__ == "__main__":
    demo_abc_basics()
    demo_incomplete_subclass()
    demo_abstract_property()
    demo_repository()
    demo_type_constraint()
    print("\n✅ 抽象基类练习全部完成")
