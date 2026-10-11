# 文件用途：Mixin 模式练习，演示功能混入、多继承组合、MRO 查看
# 电商场景：Product 混入序列化和日志功能

import json
from datetime import datetime


# ============ 1. Mixin 基础 ============
class LogMixin:
    """日志功能混入：提供 log 方法

    Mixin 类小而专注，只提供单一功能，不单独使用
    """

    def log(self, msg: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        cls_name = self.__class__.__name__
        print(f"  [{level}] {timestamp} {cls_name}: {msg}")


class SerializeMixin:
    """序列化功能混入：提供 to_dict / to_json 方法"""

    def to_dict(self) -> dict:
        """转字典（过滤掉私有属性）"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

    def to_json(self) -> str:
        """转 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class ReprMixin:
    """repr 功能混入：自动生成 __repr__"""

    def __repr__(self):
        attrs = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items()
            if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({attrs})"


def demo_mixin_basics():
    """演示 Mixin 基础"""
    print("===== 1. Mixin 基础 =====")

    # 组合多个 Mixin
    class Product(LogMixin, SerializeMixin, ReprMixin):
        def __init__(self, pid: str, name: str, price: float):
            self.id = pid
            self.name = name
            self.price = price

    p = Product("P001", "iPhone", 5999)
    p.log("商品已创建")                # 来自 LogMixin
    print(f"to_dict: {p.to_dict()}")   # 来自 SerializeMixin
    print(f"to_json: {p.to_json()}")   # 来自 SerializeMixin
    print(f"repr: {repr(p)}")          # 来自 ReprMixin


# ============ 2. Mixin 与类属性 ============
class CounterMixin:
    """计数器混入：统计实例数量"""

    _count = 0     # 类属性，所有实例共享

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    # 关键：调用 super 协作链
        CounterMixin._count += 1

    @classmethod
    def get_count(cls) -> int:
        return CounterMixin._count

    @classmethod
    def reset_count(cls) -> None:
        CounterMixin._count = 0


def demo_counter_mixin():
    """演示计数器 Mixin"""
    print("\n===== 2. 计数器 Mixin =====")

    class Customer(CounterMixin):
        def __init__(self, name: str):
            super().__init__()    # 触发 CounterMixin.__init__
            self.name = name

    Customer.reset_count()
    c1 = Customer("Tom")
    c2 = Customer("Jerry")
    c3 = Customer("Lucy")
    print(f"已创建客户数: {Customer.get_count()}")


# ============ 3. MRO 查看与分析 ============
def demo_mro():
    """演示 MRO（方法解析顺序）"""
    print("\n===== 3. MRO 查看 =====")

    class A:
        def hello(self): return "A"

    class B(A):
        def hello(self): return "B"

    class C(A):
        def hello(self): return "C"

    class D(B, C):
        pass

    # 钻石继承：D → B → C → A → object
    print(f"D.__mro__:")
    for cls in D.__mro__:
        print(f"  {cls.__name__}")

    d = D()
    print(f"\nD().hello(): {d.hello()}")    # 'B'，按 MRO 找第一个

    # super() 按 MRO 调用
    class D2(B, C):
        def hello(self):
            return f"D2 → {super().hello()}"

    print(f"D2().hello(): {D2().hello()}")  # super() 调用 B.hello()


# ============ 4. Mixin 在电商中的应用 ============
class LogMixin2:
    """日志混入"""

    def log(self, msg: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  [{level}] {timestamp} {self.__class__.__name__}: {msg}")


class SerializeMixin2:
    """序列化混入"""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建实例（简化版）"""
        return cls(**{k: v for k, v in data.items() if k in cls.__init__.__code__.co_varnames})


class ValidateMixin:
    """验证混入：提供通用验证方法"""

    def validate_positive(self, value, field_name: str) -> None:
        if value < 0:
            raise ValueError(f"{field_name} 不能为负，得到 {value}")

    def validate_not_empty(self, value, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} 不能为空")


# 通过 Mixin 组合出的商品类
class Product(LogMixin2, SerializeMixin2, ValidateMixin):
    """商品类：混入日志、序列化、验证功能"""

    def __init__(self, pid: str, name: str, price: float, stock: int = 0):
        # 使用 ValidateMixin 的方法
        self.validate_positive(price, "price")
        self.validate_positive(stock, "stock")
        self.validate_not_empty(name, "name")

        self.id = pid
        self.name = name
        self.price = price
        self.stock = stock
        self._internal_code = f"INT-{pid}"   # 私有属性，序列化时会被过滤

        # 使用 LogMixin 的方法
        self.log(f"商品 {name} 已创建")

    def sell(self, qty: int) -> None:
        self.validate_positive(qty, "qty")
        if qty > self.stock:
            raise ValueError(f"库存不足：{self.stock} < {qty}")
        self.stock -= qty
        self.log(f"售出 {qty} 件，剩余 {self.stock}")


def demo_ecommerce_mixin():
    """电商场景：Product 混入功能"""
    print("\n===== 4. 电商场景：Product 混入功能 =====")

    # 查看商品类的 MRO
    print("Product 的 MRO:")
    for cls in Product.__mro__:
        print(f"  {cls.__name__}")

    # 创建商品（自动验证 + 日志）
    print("\n创建商品:")
    p = Product("P001", "iPhone 15", 5999.0, 50)

    # 序列化（来自 SerializeMixin）
    print(f"\nto_dict: {p.to_dict()}")      # _internal_code 被过滤
    print(f"to_json: {p.to_json()}")

    # 业务方法（带验证和日志）
    print(f"\n售出操作:")
    p.sell(5)

    # 验证失败
    print(f"\n验证失败:")
    try:
        p.sell(1000)
    except ValueError as e:
        p.log(f"售出失败: {e}", level="ERROR")

    try:
        Product("P002", "", -100)    # 名称空 + 价格负
    except ValueError as e:
        print(f"  ❌ {e}")


# ============ 5. 多个 Mixin 协作（super 链）============
class Base:
    """基类"""

    def process(self) -> str:
        return "Base.process"


class StepOneMixin:
    """第一步处理"""

    def process(self) -> str:
        result = super().process()    # 调用 MRO 中下一个
        return f"StepOne({result})"


class StepTwoMixin:
    """第二步处理"""

    def process(self) -> str:
        result = super().process()
        return f"StepTwo({result})"


class StepThreeMixin:
    """第三步处理"""

    def process(self) -> str:
        result = super().process()
        return f"StepThree({result})"


class Pipeline(StepOneMixin, StepTwoMixin, StepThreeMixin, Base):
    """组合三个步骤的流水线"""
    pass


def demo_mixin_chain():
    """演示 Mixin 通过 super 协作"""
    print("\n===== 5. Mixin 协作链（super 按 MRO 调用） =====")

    print("Pipeline 的 MRO:")
    for cls in Pipeline.__mro__:
        print(f"  {cls.__name__}")

    p = Pipeline()
    # 调用链：StepOne → StepTwo → StepThree → Base
    result = p.process()
    print(f"\n执行结果: {result}")


# ============ 6. Mixin 设计原则 ============
def demo_mixin_principles():
    """演示 Mixin 设计原则"""
    print("\n===== 6. Mixin 设计原则 =====")
    print("""
Mixin 设计原则：
  1. 小而专注：每个 Mixin 只提供单一功能
  2. 不单独使用：Mixin 是"功能调料"，不是主菜
  3. 命名以 Mixin 结尾：明确表示是混入类
  4. 使用 super() 协作：让多个 Mixin 能协作
  5. 避免状态耦合：尽量不依赖其他 Mixin 的属性

典型组合：
  class MyService(LogMixin, SerializeMixin, ValidateMixin):
      ...

优点：
  ✅ 功能可插拔，灵活组合
  ✅ 避免类层次过深（vs 继承）
  ✅ 单一职责，易于测试

缺点：
  ⚠️ 多继承 MRO 复杂
  ⚠️ 调试时需理解 super() 调用链
""")


if __name__ == "__main__":
    demo_mixin_basics()
    demo_counter_mixin()
    demo_mro()
    demo_ecommerce_mixin()
    demo_mixin_chain()
    demo_mixin_principles()
    print("✅ Mixin 模式练习全部完成")
