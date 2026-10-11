# 文件用途：魔术方法与运算符重载练习，演示 __eq__/__lt__/__hash__/__len__/__getitem__/__contains__/__call__
# 电商场景：Product 实现比较和排序、Order 支持索引访问 items、可调用对象

from functools import total_ordering


# ============ 1. 比较方法与 total_ordering ============
@total_ordering
class Product:
    """商品类：实现比较方法，支持排序

    用 @total_ordering 装饰器：只需定义 __eq__ 和 __lt__，
    自动生成 __le__ / __gt__ / __ge__
    """

    def __init__(self, pid: str, name: str, price: float, stock: int = 0):
        self.id = pid
        self.name = name
        self.price = price
        self.stock = stock

    def __eq__(self, other):
        """相等：id 和 name 都相同"""
        if not isinstance(other, Product):
            return NotImplemented
        return self.id == other.id and self.name == other.name

    def __lt__(self, other):
        """小于：按价格比较"""
        if not isinstance(other, Product):
            return NotImplemented
        return self.price < other.price

    def __hash__(self):
        """可哈希：基于不可变字段，可作字典键/集合元素"""
        return hash((self.id, self.name))

    def __str__(self):
        return f"[{self.id}] {self.name} ¥{self.price}"

    def __repr__(self):
        return f"Product(id={self.id!r}, name={self.name!r}, price={self.price})"


def demo_comparison():
    """演示比较方法"""
    print("===== 1. 比较方法与 total_ordering =====")
    p1 = Product("P001", "AirPods", 199)
    p2 = Product("P002", "iPhone", 5999)
    p3 = Product("P003", "iPad", 2999)
    p4 = Product("P001", "AirPods", 199)   # 与 p1 相等

    # 比较（total_ordering 自动生成 >, >=, <=）
    print(f"{p1.name} < {p2.name}? {p1 < p2}")       # True
    print(f"{p2.name} > {p3.name}? {p2 > p3}")       # True (自动生成)
    print(f"{p1.name} >= {p4.name}? {p1 >= p4}")     # True (自动生成)
    print(f"p1 == p4? {p1 == p4}")                   # True
    print(f"p1 == '字符串'? {p1 == '字符串'}")        # False (NotImplemented 回退)

    # 可哈希：放入集合
    products_set = {p1, p2, p4}    # p1 和 p4 相等，去重
    print(f"集合大小（p1==p4 去重）: {len(products_set)}")

    # 排序
    products = [p2, p1, p3]
    sorted_products = sorted(products)    # 用 __lt__
    print("\n按价格升序:")
    for p in sorted_products:
        print(f"  {p}")


# ============ 2. 容器方法：Order 支持索引访问 ============
class Order:
    """订单类：实现容器方法，像列表一样操作"""

    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items: list[str] = []
        self.status = "pending"

    def add_item(self, item: str) -> None:
        self.items.append(item)

    def __len__(self):
        """len(order) 返回商品数"""
        return len(self.items)

    def __getitem__(self, index):
        """order[i] 索引访问，支持切片"""
        return self.items[index]

    def __setitem__(self, index, value):
        """order[i] = v 索引赋值"""
        self.items[index] = value

    def __delitem__(self, index):
        """del order[i] 索引删除"""
        del self.items[index]

    def __contains__(self, item):
        """item in order 成员判断"""
        return item in self.items

    def __iter__(self):
        """for item in order 迭代"""
        return iter(self.items)

    def __str__(self):
        return f"订单 {self.order_id} ({len(self.items)} 件): {self.items}"

    def __repr__(self):
        return f"Order(order_id={self.order_id!r}, items={self.items})"


def demo_container():
    """演示容器方法"""
    print("\n===== 2. 容器方法（Order 像列表一样操作） =====")
    order = Order("O001", "C001")
    order.add_item("iPhone")
    order.add_item("AirPods")
    order.add_item("iPad")

    # __len__
    print(f"len(order): {len(order)}")

    # __getitem__
    print(f"order[0]: {order[0]}")
    print(f"order[-1]: {order[-1]}")
    print(f"order[0:2] 切片: {order[0:2]}")

    # __contains__
    print(f"'iPhone' in order: {'iPhone' in order}")
    print(f"'MacBook' in order: {'MacBook' in order}")

    # __setitem__
    order[1] = "AirPods Pro"
    print(f"修改后: {order}")

    # __delitem__
    del order[0]
    print(f"删除 [0] 后: {order}")

    # __iter__
    order.add_item("MacBook")
    print("遍历订单:")
    for item in order:
        print(f"  - {item}")


# ============ 3. __call__ 可调用对象 ============
class DiscountCalculator:
    """折扣计算器：实例可像函数一样调用"""

    def __init__(self, customer_type: str = "normal"):
        self.customer_type = customer_type
        self.rates = {
            "normal": 1.0,
            "vip": 0.9,
            "svip": 0.8,
        }
        self.call_count = 0

    def __call__(self, price: float) -> float:
        """让实例可调用：calc(price)"""
        self.call_count += 1
        rate = self.rates.get(self.customer_type, 1.0)
        return round(price * rate, 2)


def demo_callable():
    """演示 __call__"""
    print("\n===== 3. __call__ 可调用对象 =====")

    calc = DiscountCalculator("vip")
    # 像函数一样调用实例
    print(f"calc(5999) = ¥{calc(5999)}")
    print(f"calc(199) = ¥{calc(199)}")
    print(f"调用次数: {calc.call_count}")

    # 普通客户
    normal_calc = DiscountCalculator("normal")
    print(f"normal_calc(5999) = ¥{normal_calc(5999)}")

    # 判断是否可调用
    print(f"calc 是否可调用: {callable(calc)}")
    print(f"普通对象是否可调用: {callable(object())}")


# ============ 4. 运算符重载 ============
class Money:
    """金额类：演示运算符重载"""

    def __init__(self, amount: float, currency: str = "¥"):
        self.amount = round(amount, 2)
        self.currency = currency

    def __add__(self, other):
        """+ 加法"""
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("货币不同，无法相加")
            return Money(self.amount + other.amount, self.currency)
        elif isinstance(other, (int, float)):
            return Money(self.amount + other, self.currency)
        return NotImplemented

    def __sub__(self, other):
        """- 减法"""
        if isinstance(other, Money):
            return Money(self.amount - other.amount, self.currency)
        elif isinstance(other, (int, float)):
            return Money(self.amount - other, self.currency)
        return NotImplemented

    def __mul__(self, other):
        """* 乘法（乘以数量）"""
        if isinstance(other, (int, float)):
            return Money(self.amount * other, self.currency)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        return NotImplemented

    def __str__(self):
        return f"{self.currency}{self.amount:.2f}"

    def __repr__(self):
        return f"Money({self.amount}, {self.currency!r})"


def demo_operators():
    """演示运算符重载"""
    print("\n===== 4. 运算符重载 =====")
    price1 = Money(5999)
    price2 = Money(199)

    # 加法
    total = price1 + price2
    print(f"{price1} + {price2} = {total}")

    # 乘法（数量）
    subtotal = price1 * 2
    print(f"{price1} × 2 = {subtotal}")

    # 减法
    diff = price1 - price2
    print(f"{price1} - {price2} = {diff}")

    # 与数字运算
    with_tax = price1 + 599.9
    print(f"{price1} + 599.9 (税) = {with_tax}")

    # 相等比较
    print(f"{price1} == Money(5999)? {price1 == Money(5999)}")

    # 复合运算
    cart = [Money(5999), Money(199), Money(2999)]
    # 用 __add__ 累加（注意起始值）
    from functools import reduce
    grand_total = reduce(lambda a, b: a + b, cart, Money(0))
    print(f"\n购物车总价: {grand_total}")


# ============ 5. __bool__ 真值测试 ============
class Stock:
    """库存类：演示 __bool__ 和 __len__"""

    def __init__(self, qty: int):
        self.qty = qty

    def __bool__(self):
        """bool(stock) 判断是否有库存"""
        return self.qty > 0

    def __len__(self):
        return self.qty

    def __str__(self):
        return f"库存 {self.qty}"


def demo_bool():
    """演示 __bool__"""
    print("\n===== 5. __bool__ 真值测试 =====")
    in_stock = Stock(50)
    out_stock = Stock(0)

    # if 语句会调用 __bool__
    if in_stock:
        print(f"{in_stock} → 有货 ✅")
    if not out_stock:
        print(f"{out_stock} → 缺货 ❌")

    # bool() 显式调用
    print(f"bool(Stock(50)): {bool(Stock(50))}")
    print(f"bool(Stock(0)): {bool(Stock(0))}")


# ============ 6. 综合示例：可比较可排序的订单 ============
@total_ordering
class OrderItem:
    """订单项：可比较、可排序"""

    def __init__(self, name: str, price: float, qty: int):
        self.name = name
        self.price = price
        self.qty = qty

    @property
    def subtotal(self) -> float:
        return round(self.price * self.qty, 2)

    def __eq__(self, other):
        if not isinstance(other, OrderItem):
            return NotImplemented
        return self.subtotal == other.subtotal

    def __lt__(self, other):
        return self.subtotal < other.subtotal

    def __str__(self):
        return f"{self.name} × {self.qty} = ¥{self.subtotal}"

    def __repr__(self):
        return f"OrderItem({self.name!r}, {self.price}, {self.qty})"


def demo_comprehensive():
    """综合示例"""
    print("\n===== 6. 综合示例：可排序的订单项 =====")
    items = [
        OrderItem("iPhone", 5999, 1),
        OrderItem("AirPods", 199, 2),
        OrderItem("iPad", 2999, 1),
        OrderItem("Mouse", 99, 3),
    ]

    print("按小计金额排序:")
    for item in sorted(items):
        print(f"  {item}")

    total = sum(item.subtotal for item in items)
    print(f"订单总价: ¥{total}")

    # 找最大最小
    print(f"最大项: {max(items)}")
    print(f"最小项: {min(items)}")


if __name__ == "__main__":
    demo_comparison()
    demo_container()
    demo_callable()
    demo_operators()
    demo_bool()
    demo_comprehensive()
    print("\n✅ 魔术方法与运算符重载练习全部完成")
