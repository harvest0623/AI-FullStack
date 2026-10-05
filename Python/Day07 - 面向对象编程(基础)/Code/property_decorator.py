# 文件用途：@property 练习，演示 getter/setter/deleter、属性验证、计算属性、@staticmethod/@classmethod
# 电商场景：商品 price 的 setter 验证非负、discount_price 计算属性、from_dict 类方法创建实例


# ============ 1. @property 基础 ============
class Temperature:
    """演示 @property 基础：getter / setter / deleter"""

    def __init__(self, celsius: float):
        # 赋值会触发 setter
        self.celsius = celsius

    @property
    def celsius(self) -> float:
        """getter：读取摄氏度"""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float):
        """setter：设置摄氏度，带验证"""
        if value < -273.15:
            raise ValueError(f"温度不能低于绝对零度 (-273.15)，得到 {value}")
        self._celsius = value

    @celsius.deleter
    def celsius(self):
        """deleter：删除"""
        print(f"  删除温度 {self._celsius}°C")
        del self._celsius


def demo_property_basics():
    """演示 @property 基础"""
    print("===== 1. @property 基础 =====")
    t = Temperature(25)
    print(f"温度: {t.celsius}°C")      # 调用 getter（像属性一样访问）

    t.celsius = 100                    # 调用 setter
    print(f"修改后: {t.celsius}°C")

    # setter 验证
    try:
        t.celsius = -300               # 触发 ValueError
    except ValueError as e:
        print(f"验证失败: {e}")

    # deleter
    del t.celsius
    try:
        t.celsius
    except AttributeError:
        print("  已删除，访问报错 AttributeError")


# ============ 2. 计算属性 ============
class Circle:
    """演示计算属性：派生属性不存储，每次访问时计算"""

    def __init__(self, radius: float):
        self.radius = radius

    @property
    def area(self) -> float:
        """面积：计算属性，不存储"""
        import math
        return math.pi * self.radius ** 2

    @property
    def perimeter(self) -> float:
        """周长：计算属性"""
        import math
        return 2 * math.pi * self.radius


def demo_computed_property():
    """演示计算属性"""
    print("\n===== 2. 计算属性 =====")
    c = Circle(5)
    print(f"半径: {c.radius}")
    print(f"面积: {c.area:.2f}")          # 计算属性，像属性访问
    print(f"周长: {c.perimeter:.2f}")

    # 修改半径后，计算属性自动更新
    c.radius = 10
    print(f"修改半径后面积: {c.area:.2f}")

    # 计算属性是只读的
    # c.area = 100  # AttributeError: can't set attribute


# ============ 3. 电商场景：完整 Product 类（带 @property）============
class Product:
    """完整的商品类：演示 @property 的实战应用

    特性：
    - price 的 setter 验证非负
    - discount_price 计算属性
    - stock 的 getter/setter
    - @staticmethod 工具方法
    - @classmethod 替代构造器
    """

    # 类属性
    count = 0
    currency = "¥"

    def __init__(self, pid: str, name: str, price: float,
                 stock: int = 0, discount_rate: float = 0.0):
        self.id = pid
        self.name = name
        self.price = price             # 触发 setter 验证
        self.stock = stock             # 触发 setter 验证
        self.discount_rate = discount_rate
        Product.count += 1

    # ---------- price 属性 ----------
    @property
    def price(self) -> float:
        """价格（含税前）"""
        return self._price

    @price.setter
    def price(self, value: float):
        """价格 setter：必须为正数"""
        if not isinstance(value, (int, float)):
            raise TypeError("价格必须是数字")
        if value < 0:
            raise ValueError(f"价格不能为负，得到 {value}")
        self._price = float(value)

    # ---------- stock 属性 ----------
    @property
    def stock(self) -> int:
        """库存"""
        return self._stock

    @stock.setter
    def stock(self, value: int):
        """库存 setter：不能为负"""
        if not isinstance(value, int):
            raise TypeError("库存必须是整数")
        if value < 0:
            raise ValueError(f"库存不能为负，得到 {value}")
        self._stock = value

    # ---------- 计算属性 ----------
    @property
    def discount_price(self) -> float:
        """折后价：计算属性"""
        return round(self._price * (1 - self.discount_rate), 2)

    @property
    def in_stock(self) -> bool:
        """是否有库存：计算属性"""
        return self._stock > 0

    @property
    def display_price(self) -> str:
        """展示价格：计算属性"""
        if self.discount_rate > 0:
            return f"{Product.currency}{self.discount_price} (原价 {Product.currency}{self._price})"
        return f"{Product.currency}{self._price}"

    # ---------- 实例方法 ----------
    def apply_discount(self, rate: float) -> None:
        """应用折扣"""
        if not 0 <= rate <= 1:
            raise ValueError("折扣率必须在 0-1 之间")
        self.discount_rate = rate

    def sell(self, qty: int) -> None:
        """售出"""
        if qty > self._stock:
            raise ValueError(f"库存不足：现有 {self._stock}，需要 {qty}")
        self._stock -= qty

    def __str__(self):
        return f"[{self.id}] {self.name} - {self.display_price} (库存 {self._stock})"

    def __repr__(self):
        return f"Product(id={self.id!r}, name={self.name!r}, price={self._price}, stock={self._stock})"

    # ---------- 静态方法 ----------
    @staticmethod
    def is_valid_price(price) -> bool:
        """静态方法：验证价格是否合法（不需要 self/cls）"""
        return isinstance(price, (int, float)) and price >= 0

    @staticmethod
    def format_price(price: float, currency: str = "¥") -> str:
        """静态方法：格式化价格"""
        return f"{currency}{price:.2f}"

    # ---------- 类方法 ----------
    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """类方法：从字典创建实例（替代构造器）

        cls 是当前类，子类继承时 cls 会自动指向子类
        """
        return cls(
            pid=data["id"],
            name=data["name"],
            price=data["price"],
            stock=data.get("stock", 0),
            discount_rate=data.get("discount_rate", 0.0),
        )

    @classmethod
    def from_string(cls, s: str) -> "Product":
        """类方法：从字符串创建实例

        格式：id,name,price,stock
        """
        parts = s.split(",")
        return cls(pid=parts[0], name=parts[1],
                   price=float(parts[2]), stock=int(parts[3]))

    @classmethod
    def get_count(cls) -> int:
        """类方法：获取已创建的商品数"""
        return cls.count


def demo_product_property():
    """电商场景：完整 Product 类"""
    print("\n===== 3. 电商场景：Product 类（带 @property） =====")

    # 创建商品（setter 验证）
    p = Product("P001", "iPhone 15", 5999.0, 50)
    print(p)

    # 价格验证
    print("\n价格验证:")
    try:
        p.price = -100        # 触发 ValueError
    except ValueError as e:
        print(f"  ❌ {e}")

    try:
        p.price = "abc"       # 触发 TypeError
    except TypeError as e:
        print(f"  ❌ {e}")

    p.price = 5499            # 合法修改
    print(f"  ✅ 修改后价格: ¥{p.price}")

    # 库存验证
    print("\n库存验证:")
    try:
        p.stock = -5
    except ValueError as e:
        print(f"  ❌ {e}")
    try:
        p.stock = 10.5        # 必须是整数
    except TypeError as e:
        print(f"  ❌ {e}")

    # 计算属性
    print("\n计算属性:")
    print(f"  原价: ¥{p.price}")
    p.apply_discount(0.1)     # 9折
    print(f"  折后价: ¥{p.discount_price}")
    print(f"  展示: {p.display_price}")
    print(f"  有库存: {p.in_stock}")


def demo_static_class_methods():
    """演示 @staticmethod 和 @classmethod"""
    print("\n===== 4. @staticmethod / @classmethod =====")

    # 静态方法：通过类名或实例调用
    print("静态方法:")
    print(f"  Product.is_valid_price(99): {Product.is_valid_price(99)}")
    print(f"  Product.is_valid_price(-1): {Product.is_valid_price(-1)}")
    print(f"  Product.is_valid_price('abc'): {Product.is_valid_price('abc')}")
    print(f"  Product.format_price(5999): {Product.format_price(5999)}")

    # 实例也能调用静态方法
    p = Product("P002", "iPad", 2999, 30)
    print(f"  实例调用: {p.is_valid_price(p.price)}")

    # 类方法：替代构造器
    print("\n类方法（替代构造器）:")
    data = {
        "id": "P003",
        "name": "MacBook Pro",
        "price": 12999.0,
        "stock": 15,
        "discount_rate": 0.05,
    }
    p_from_dict = Product.from_dict(data)
    print(f"  from_dict: {p_from_dict}")
    print(f"  折后价: ¥{p_from_dict.discount_price}")

    p_from_str = Product.from_string("P004,AirPods,199.0,100")
    print(f"  from_string: {p_from_str}")

    # 类方法操作类属性
    print(f"\n  已创建商品数: {Product.get_count()}")


# ============ 4. 类方法在继承中的多态 ============
class PremiumProduct(Product):
    """高级商品：演示类方法在继承中的行为"""

    def __init__(self, pid: str, name: str, price: float,
                 stock: int = 0, discount_rate: float = 0.0,
                 warranty: int = 12):
        super().__init__(pid, name, price, stock, discount_rate)
        self.warranty = warranty     # 保修期（月）

    def __str__(self):
        base = super().__str__()
        return f"{base} [保修 {self.warranty} 月]"


def demo_classmethod_inheritance():
    """演示类方法在继承中的多态"""
    print("\n===== 5. 类方法在继承中的多态 =====")

    # from_dict 继承自父类，但 cls 会指向 PremiumProduct
    data = {"id": "PR001", "name": "iPhone 15 Pro Max", "price": 9999, "stock": 20}
    p = PremiumProduct.from_dict(data)     # cls = PremiumProduct
    print(f"类型: {type(p).__name__}")    # PremiumProduct
    print(p)


if __name__ == "__main__":
    demo_property_basics()
    demo_computed_property()
    demo_product_property()
    demo_static_class_methods()
    demo_classmethod_inheritance()
    print("\n✅ @property 练习全部完成")
