# 文件用途：元类练习
# 演示内容：type 动态创建类、自定义元类、__init_subclass__
# 电商场景：模型注册元类自动注册所有 Model 子类
# Python 3.10+ 可运行

from dataclasses import dataclass


# ============================================================
# 1. type() 的两面性 - 查看类型与创建类
# ============================================================

def demo_type_two_faces() -> None:
    """演示 type() 的两种用法"""
    print("=" * 60)
    print("示例 1：type() 的两面性")
    print("=" * 60)

    # 用法一：查看类型
    obj = "hello"
    print(f"type('hello') = {type(obj)}")           # <class 'str'>
    print(f"type(42) = {type(42)}")                  # <class 'int'>
    print(f"type(type) = {type(type)}")              # <class 'type'>

    # 用法二：动态创建类
    # type(name, bases, dict)
    DynamicClass = type(
        "DynamicClass",         # 类名
        (object,),              # 父类元组
        {                       # 类属性/方法字典
            "attr": 42,
            "greet": lambda self: f"Hello from {self.__class__.__name__}",
            "__repr__": lambda self: f"DynamicClass(attr={self.attr})",
        },
    )

    # 等价于：
    # class DynamicClass(object):
    #     attr = 42
    #     def greet(self): return f"Hello from {self.__class__.__name__}"
    #     def __repr__(self): return f"DynamicClass(attr={self.attr})"

    instance = DynamicClass()
    print(f"\n动态创建的类: {DynamicClass}")
    print(f"实例: {instance}")
    print(f"属性 attr: {instance.attr}")
    print(f"方法 greet: {instance.greet()}")


# ============================================================
# 2. 动态创建电商模型类
# ============================================================

def create_model_class(class_name: str, fields_dict: dict) -> type:
    """动态创建数据模型类"""
    # 构造 __init__ 方法
    def __init__(self, **kwargs):
        for key, default in fields_dict.items():
            setattr(self, key, kwargs.get(key, default))

    def __repr__(self):
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in fields_dict)
        return f"{class_name}({attrs})"

    return type(class_name, (object,), {
        "__init__": __init__,
        "__repr__": __repr__,
        "_fields": list(fields_dict.keys()),
    })


def demo_dynamic_model() -> None:
    """演示动态创建电商模型"""
    print("\n" + "=" * 60)
    print("示例 2：动态创建电商模型类")
    print("=" * 60)

    # 动态创建 Product 类
    Product = create_model_class("Product", {
        "id": 0,
        "name": "",
        "price": 0.0,
        "stock": 0,
    })

    p = Product(id=1, name="iPhone", price=9999.0, stock=50)
    print(f"动态创建的 Product: {p}")
    print(f"字段列表: {p._fields}")

    # 动态创建 Order 类
    Order = create_model_class("Order", {
        "id": 0,
        "customer_id": 0,
        "total": 0.0,
    })

    o = Order(id=100, customer_id=1001, total=19998.0)
    print(f"\n动态创建的 Order: {o}")


# ============================================================
# 3. 自定义元类 - 模型注册元类
# ============================================================

class ModelRegistryMeta(type):
    """模型注册元类：自动注册所有 Model 子类"""

    registry: dict[str, type] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # 跳过基类 Model 本身（它没有有意义的父类）
        if bases and any(b.__name__ == "Model" for b in bases):
            mcs.registry[name] = cls
            print(f"  [元类] 自动注册模型: {name}")
        return cls

    @classmethod
    def get_model(mcs, name: str) -> type | None:
        """根据类名获取已注册的模型"""
        return mcs.registry.get(name)

    @classmethod
    def all_models(mcs) -> dict[str, type]:
        """获取所有已注册的模型"""
        return dict(mcs.registry)


# 基类，使用元类
class Model(metaclass=ModelRegistryMeta):
    """所有模型的基类"""
    id: int

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={getattr(self, 'id', '?')})"


# 电商模型子类 - 会自动注册
class Product(Model):
    def __init__(self, id: int, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price


class Order(Model):
    def __init__(self, id: int, customer_id: int):
        self.id = id
        self.customer_id = customer_id


class Customer(Model):
    def __init__(self, id: int, email: str):
        self.id = id
        self.email = email


def demo_model_registry_meta() -> None:
    """演示模型注册元类"""
    print("\n" + "=" * 60)
    print("示例 3：模型注册元类（自动注册所有 Model 子类）")
    print("=" * 60)

    print("\n已注册的模型：")
    for name, cls in ModelRegistryMeta.all_models().items():
        print(f"  {name}: {cls}")

    # 根据类名动态获取模型类
    model_cls = ModelRegistryMeta.get_model("Product")
    if model_cls:
        p = model_cls(1, "iPhone", 9999.0)
        print(f"\n通过注册表创建 Product: {p}")

    model_cls = ModelRegistryMeta.get_model("Order")
    if model_cls:
        o = model_cls(100, 1001)
        print(f"通过注册表创建 Order: {o}")


# ============================================================
# 4. 元类方法调用顺序
# ============================================================

class TracingMeta(type):
    """追踪元类方法调用的元类"""

    def __new__(mcs, name, bases, namespace):
        print(f"  1. TracingMeta.__new__ 创建类对象: {name}")
        cls = super().__new__(mcs, name, bases, namespace)
        print(f"  2. 类对象 {name} 已创建")
        return cls

    def __init__(cls, name, bases, namespace):
        print(f"  3. TracingMeta.__init__ 初始化类对象: {name}")
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        print(f"  4. TracingMeta.__call__ 创建实例: {cls.__name__}()")
        # 调用默认的 __new__ 和 __init__
        instance = super().__call__(*args, **kwargs)
        print(f"  7. 实例 {cls.__name__} 创建完成")
        return instance


class TracedClass(metaclass=TracingMeta):
    def __init__(self):
        print(f"  5. TracedClass.__init__ 初始化实例")
        self.value = 42

    def __new__(cls):
        print(f"  6. TracedClass.__new__ 创建实例对象")
        return super().__new__(cls)


def demo_metaclass_call_order() -> None:
    """演示元类方法调用顺序"""
    print("\n" + "=" * 60)
    print("示例 4：元类方法调用顺序")
    print("=" * 60)

    print("\n创建 TracedClass 实例：")
    obj = TracedClass()
    print(f"\n实例值: {obj.value}")


# ============================================================
# 5. __init_subclass__ 替代元类
# ============================================================

class PluginBase:
    """用 __init_subclass__ 实现插件注册"""
    _plugins: list[type] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        PluginBase._plugins.append(cls)
        print(f"  [init_subclass] 注册插件: {cls.__name__}")


class PaymentPlugin(PluginBase):
    name = "payment"

    def process(self, amount: float) -> bool:
        print(f"  支付 {amount} 元")
        return True


class EmailPlugin(PluginBase):
    name = "email"

    def process(self, message: str) -> bool:
        print(f"  发送邮件: {message}")
        return True


class SMSPlugin(PluginBase):
    name = "sms"

    def process(self, phone: str, message: str) -> bool:
        print(f"  发送短信到 {phone}: {message}")
        return True


def demo_init_subclass() -> None:
    """演示 __init_subclass__ 替代元类"""
    print("\n" + "=" * 60)
    print("示例 5：__init_subclass__ 替代元类")
    print("=" * 60)

    print(f"\n已注册插件: {[p.__name__ for p in PluginBase._plugins]}")

    # 实例化并使用插件
    for plugin_cls in PluginBase._plugins:
        plugin = plugin_cls()
        if plugin.name == "payment":
            plugin.process(99.9)
        elif plugin.name == "email":
            plugin.process("订单已确认")
        elif plugin.name == "sms":
            plugin.process("13800138000", "验证码 1234")


# ============================================================
# 6. __class_getitem__ 类参数化
# ============================================================

class QuerySet:
    """模拟 Django QuerySet，支持类型参数化"""

    def __init__(self, items: list | None = None):
        self._items = items or []

    def __class_getitem__(cls, item):
        """支持 QuerySet[Product] 语法"""
        return type(f"QuerySet[{item.__name__}]", (cls,), {"_model": item})

    def filter(self, **kwargs):
        """简单过滤"""
        result = []
        for item in self._items:
            if all(getattr(item, k, None) == v for k, v in kwargs.items()):
                result.append(item)
        return QuerySet(result)

    def first(self):
        return self._items[0] if self._items else None

    def __repr__(self):
        return f"QuerySet({self._items})"


@dataclass
class Product:
    id: int
    name: str
    price: float


def demo_class_getitem() -> None:
    """演示 __class_getitem__"""
    print("\n" + "=" * 60)
    print("示例 6：__class_getitem__ 类参数化")
    print("=" * 60)

    # 类型参数化
    TypedQuerySet = QuerySet[Product]
    print(f"参数化类型: {TypedQuerySet}")

    products = [
        Product(1, "iPhone", 9999.0),
        Product(2, "MacBook", 8999.0),
        Product(3, "AirPods", 1999.0),
    ]

    qs = TypedQuerySet(products)
    print(f"全部: {qs}")

    filtered = qs.filter(name="iPhone")
    print(f"过滤 name=iPhone: {filtered}")


def main() -> None:
    """主函数"""
    demo_type_two_faces()
    demo_dynamic_model()
    demo_model_registry_meta()
    demo_metaclass_call_order()
    demo_init_subclass()
    demo_class_getitem()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
