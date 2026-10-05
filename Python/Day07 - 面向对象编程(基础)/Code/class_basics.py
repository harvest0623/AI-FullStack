# 文件用途：类基础练习，演示 class 定义、__init__/self、实例属性与类属性、__str__/__repr__
# 电商场景：完整的商品 Product 类


# ============ 1. 最简单的类 ============
class ProductBasic:
    """最简单的商品类"""
    pass


def demo_simplest():
    """演示最简单的类"""
    print("===== 1. 最简单的类 =====")
    p1 = ProductBasic()
    p2 = ProductBasic()
    print(f"p1 is p2: {p1 is p2}")     # False，两个不同对象
    print(f"p1 类型: {type(p1).__name__}")

    # 动态添加属性（不推荐，仅演示）
    p1.name = "iPhone"
    print(f"p1.name = {p1.name}")
    # print(p2.name)  # AttributeError，p2 没有 name


# ============ 2. __init__ 与 self ============
class ProductWithInit:
    """带构造器的商品类"""

    def __init__(self, pid: str, name: str, price: float, stock: int = 0):
        # self 指向当前正在创建的实例
        self.id = pid
        self.name = name
        self.price = price
        self.stock = stock
        # 等价于：ProductWithInit.__init__(p, pid, name, price, stock)


def demo_init():
    """演示 __init__ 与 self"""
    print("\n===== 2. __init__ 与 self =====")
    p = ProductWithInit("P001", "iPhone 15", 5999.0, 50)
    print(f"商品ID: {p.id}")
    print(f"名称: {p.name}")
    print(f"价格: {p.price}")
    print(f"库存: {p.stock}")

    # 默认参数
    p2 = ProductWithInit("P002", "AirPods", 199.0)
    print(f"\n使用默认库存: {p2.name} 库存={p2.stock}")


# ============ 3. 实例属性 vs 类属性 ============
class Product:
    """完整的商品类：演示实例属性与类属性"""

    # 类属性：所有实例共享
    tax_rate = 0.13
    count = 0

    def __init__(self, pid: str, name: str, price: float, stock: int = 0, category: str = "general"):
        # 实例属性：每个实例独立
        self.id = pid
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category

        # 修改类属性（通过类名）
        Product.count += 1

    def get_tax(self) -> float:
        """计算税费"""
        return self.price * Product.tax_rate

    def final_price(self) -> float:
        """含税价"""
        return self.price + self.get_tax()


def demo_attributes():
    """演示实例属性 vs 类属性"""
    print("\n===== 3. 实例属性 vs 类属性 =====")

    p1 = Product("P001", "iPhone", 5999, 50, "phone")
    p2 = Product("P002", "MacBook", 12999, 15, "laptop")

    # 实例属性：各自独立
    print(f"p1.name = {p1.name}, p2.name = {p2.name}")

    # 类属性：通过类名或实例都能访问
    print(f"税率 (类名访问): {Product.tax_rate}")
    print(f"税率 (实例访问): {p1.tax_rate}")
    print(f"创建商品数: {Product.count}")

    # 访问优先级：实例属性 > 类属性
    # 通过实例赋值会创建实例属性，遮蔽类属性
    p1.tax_rate = 0.1          # 创建 p1 的实例属性，不修改类属性
    print(f"\np1.tax_rate = {p1.tax_rate} (实例属性)")
    print(f"p2.tax_rate = {p2.tax_rate} (仍用类属性)")
    print(f"Product.tax_rate = {Product.tax_rate} (类属性不变)")

    # 修改类属性（通过类名）会影响所有未遮蔽的实例
    Product.tax_rate = 0.15
    print(f"\n修改类属性后:")
    print(f"  p1.tax_rate = {p1.tax_rate} (实例属性遮蔽，不变)")
    print(f"  p2.tax_rate = {p2.tax_rate} (跟随类属性变化)")

    # 查看实例的所有属性
    print(f"\np1 的实例字典: {p1.__dict__}")


# ============ 4. __str__ 与 __repr__ ============
class ProductRepr:
    """演示 __str__ 与 __repr__"""

    def __init__(self, pid: str, name: str, price: float):
        self.id = pid
        self.name = name
        self.price = price

    def __str__(self):
        """面向用户：print() / str() 调用"""
        return f"{self.name} (¥{self.price:.2f})"

    def __repr__(self):
        """面向开发者：repr() / 调试 / 列表中显示"""
        return f"ProductRepr(id={self.id!r}, name={self.name!r}, price={self.price})"


def demo_str_repr():
    """演示 __str__ 与 __repr__"""
    print("\n===== 4. __str__ 与 __repr__ =====")
    p = ProductRepr("P001", "iPhone 15", 5999.0)

    print(f"print(p): {p}")               # __str__
    print(f"str(p): {str(p)}")            # __str__
    print(f"repr(p): {repr(p)}")          # __repr__

    # 列表中用 __repr__
    products = [ProductRepr("P001", "iPhone", 5999), ProductRepr("P002", "iPad", 2999)]
    print(f"列表中的商品: {products}")

    # 只定义 __repr__ 时，__str__ 会回退到 __repr__
    class OnlyRepr:
        def __init__(self, x):
            self.x = x
        def __repr__(self):
            return f"OnlyRepr({self.x})"

    obj = OnlyRepr(42)
    print(f"\n只定义 __repr__ 时:")
    print(f"  print(obj): {obj}")         # 回退用 __repr__
    print(f"  repr(obj): {repr(obj)}")


# ============ 5. 访问控制约定 ============
class ProductAccess:
    """演示访问控制约定 public / protected / private"""

    def __init__(self, name: str, cost: float, secret_key: str):
        self.name = name              # public：公开 API
        self._cost = cost             # protected：约定内部用
        self.__secret = secret_key    # private：名称重整

    def get_cost(self) -> float:
        """公开方法访问 protected 属性"""
        return self._cost

    def get_secret(self) -> str:
        """公开方法访问 private 属性"""
        return self.__secret


def demo_access_control():
    """演示访问控制约定"""
    print("\n===== 5. 访问控制约定 =====")
    p = ProductAccess("iPhone", 4000.0, "API_KEY_123")

    # public：正常访问
    print(f"public name: {p.name}")

    # protected：能访问，但约定不要在外部用
    print(f"protected _cost: {p._cost}  (能访问但不推荐)")

    # private：直接访问会报错
    # print(p.__secret)   # AttributeError
    print(f"private __secret 通过方法: {p.get_secret()}")

    # 名称重整：__secret 被改名为 _ProductAccess__secret
    print(f"名称重整后访问: {p._ProductAccess__secret}  (能访问但极不推荐)")

    # 查看所有属性
    print(f"实例属性字典: {p.__dict__}")


# ============ 6. 完整的 Product 类 ============
class FullProduct:
    """完整的商品类：综合演示

    类属性 + 实例属性 + 方法 + __str__/__repr__
    """

    # 类属性
    count = 0
    currency = "¥"

    def __init__(self, pid: str, name: str, price: float, stock: int, category: str = "general"):
        self.id = pid
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category
        FullProduct.count += 1

    def apply_discount(self, rate: float) -> float:
        """应用折扣，返回折后价"""
        return round(self.price * (1 - rate), 2)

    def in_stock(self) -> bool:
        """是否有库存"""
        return self.stock > 0

    def restock(self, qty: int) -> None:
        """补货"""
        if qty <= 0:
            raise ValueError("补货数量必须为正")
        self.stock += qty

    def sell(self, qty: int) -> None:
        """售出"""
        if qty > self.stock:
            raise ValueError(f"库存不足：现有 {self.stock}，需要 {qty}")
        self.stock -= qty

    def __str__(self):
        return f"[{self.id}] {self.name} - {FullProduct.currency}{self.price} (库存 {self.stock})"

    def __repr__(self):
        return f"FullProduct(id={self.id!r}, name={self.name!r}, price={self.price}, stock={self.stock})"


def demo_full_product():
    """演示完整的商品类"""
    print("\n===== 6. 完整的 Product 类 =====")

    p1 = FullProduct("P001", "iPhone 15", 5999.0, 50, "phone")
    p2 = FullProduct("P002", "AirPods Pro", 199.0, 200, "accessory")

    print(p1)                # __str__
    print(p2)
    print(f"已创建商品数: {FullProduct.count}")

    # 业务方法
    print(f"\n{p1.name} 9折后: ¥{p1.apply_discount(0.1)}")
    print(f"{p1.name} 有库存? {p1.in_stock()}")

    # 售出与补货
    p1.sell(10)
    print(f"售出10件后: {p1}")
    p1.restock(5)
    print(f"补货5件后: {p1}")

    # 异常情况
    try:
        p1.sell(1000)
    except ValueError as e:
        print(f"售出异常: {e}")

    # repr 用于调试
    print(f"\n调试信息: {repr(p1)}")
    print(f"列表: {[p1, p2]}")


if __name__ == "__main__":
    demo_simplest()
    demo_init()
    demo_attributes()
    demo_str_repr()
    demo_access_control()
    demo_full_product()
    print("\n✅ 类基础练习全部完成")
