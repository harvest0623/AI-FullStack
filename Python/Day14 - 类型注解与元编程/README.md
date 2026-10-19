# Day14 - 类型注解与元编程

类型注解让 Python 兼具动态灵活与静态安全，元编程打开底层魔法之门。一边是 `typing` 模块与 `mypy` 让你在编写时就能发现类型错误、获得 IDE 智能提示；另一边是元类、描述符、`type()` 动态创建类等元编程能力，让你能够操控类的创建过程、实现 ORM、插件注册、属性验证等高级模式。本章将系统讲解 Python 类型注解体系与元编程核心技术，为后续 FastAPI、Pydantic、SQLAlchemy 等框架学习打下坚实基础。

## 学习目标

完成本章后，你应能：

- 熟练使用类型注解（基本类型、复合类型、Optional、Union、Callable）
- 掌握 typing 高级特性（TypeVar、Generic、Protocol、Literal、TypedDict）
- 使用 mypy 进行静态类型检查
- 理解 `type()` 的两面性与动态创建类
- 掌握元类 Metaclass 与 `__init_subclass__` 钩子
- 理解描述符协议并自定义描述符
- 深入 dataclasses 的高级用法

## 理论知识讲解

### 一、类型注解

#### 1.1 为什么需要类型注解

动态类型语言 Python 的灵活性的代价：

| 问题 | 后果 | 类型注解如何解决 |
|------|------|----------------|
| 运行时才发现错误 | 排查成本高 | 编写时 mypy 即可发现 |
| IDE 智能提示弱 | 开发效率低 | 类型注解提供精确补全 |
| 重构不安全 | 改一处可能影响多处 | mypy 全项目检查 |
| 函数签名不清晰 | 需读文档才知道参数类型 | 注解即文档 |

```python
# 没有类型注解：参数类型不明确
def calculate_total(items, discount):
    return sum(i['price'] for i in items) * (1 - discount)

# 有类型注解：一目了然
def calculate_total(items: list[dict[str, float]], discount: float) -> float:
    return sum(i['price'] for i in items) * (1 - discount)
```

#### 1.2 typing 模块基础

##### 基本注解

```python
name: str = "iPhone"
price: float = 999.99
stock: int = 100
active: bool = True
nothing: None = None
```

##### 函数注解

```python
def greet(name: str, times: int = 1) -> str:
    return f"Hello {name}! " * times

# 参数注解：name: str, times: int = 1
# 返回值注解：-> str
```

##### 复合类型（3.9+ 内置泛型，无需 typing）

```python
# 列表
prices: list[int] = [10, 20, 30]
names: list[str] = ["A", "B", "C"]

# 字典
stock: dict[str, int] = {"iPhone": 10, "MacBook": 5}
nested: dict[str, list[int]] = {"a": [1, 2], "b": [3, 4]}

# 元组
point: tuple[int, str] = (1, "A")           # 固定长度
many: tuple[int, ...] = (1, 2, 3, 4)        # 可变长度

# 集合
tags: set[str] = {"python", "web"}
```

##### Optional / Union（3.10+ 用 `|` 语法）

```python
from typing import Optional, Union

# 以下三种写法等价
def find(id: int) -> Optional[str]: ...
def find(id: int) -> Union[str, None]: ...
def find(id: int) -> str | None: ...   # 3.10+ 推荐

# Union 等价
def parse(value: Union[str, int]) -> str: ...
def parse(value: str | int) -> str: ...  # 3.10+ 推荐
```

##### Callable

```python
from typing import Callable

# Callable[[参数类型列表], 返回类型]
def apply(fn: Callable[[int, str], bool], x: int, y: str) -> bool:
    return fn(x, y)

# 不带参数的 Callable
Handler = Callable[[], None]
```

##### TypeVar 泛型

```python
from typing import TypeVar

T = TypeVar('T')  # 任意类型

def first(items: list[T]) -> T:  # 输入输出类型一致
    return items[0]

# TypeVar 约束
T = TypeVar('T', int, float)  # 只能是 int 或 float
T = TypeVar('T', bound=str)   # 必须是 str 或其子类
```

##### Generic 泛型类

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

# 使用时指定类型
stack: Stack[int] = Stack()
stack.push(1)
```

##### Protocol（结构子类型 / 鸭子类型升级版）

```python
from typing import Protocol

class SupportsClose(Protocol):
    def close(self) -> None: ...

# 任何有 close() 方法的对象都符合，无需继承
class FileResource:
    def close(self) -> None:
        print("关闭文件")

def close_resource(r: SupportsClose) -> None:
    r.close()  # FileResource 实例可以直接传入
```

##### TypeAlias / NewType

```python
from typing import TypeAlias, NewType

# 类型别名
UserId: TypeAlias = int
UserName: TypeAlias = str

# NewType 创建新类型（运行时仍是原类型，但类型检查器视为不同）
Email = NewType('Email', str)
def send(email: Email) -> None: ...

# 必须 Email("...") 显式构造
send(Email("user@example.com"))
```

##### Any / NoReturn / Never

```python
from typing import Any, NoReturn, Never

def log(msg: Any) -> None: ...      # 任意类型
def fatal() -> NoReturn: ...       # 永不返回（抛异常/退出）
# Never（3.11+）：表示不可能有值
```

##### Literal 字面量类型

```python
from typing import Literal

def request(method: Literal["GET", "POST"]) -> str: ...
request("GET")    # ✅
request("PUT")    # ❌ mypy 报错

# 布尔字面量
Mode = Literal["r", "w", "a", "rb", "wb"]
```

##### TypedDict 类型化字典

```python
from typing import TypedDict

class ProductDict(TypedDict):
    id: int
    name: str
    price: float
    tags: list[str]

# 字典有了结构化的类型约束
p: ProductDict = {"id": 1, "name": "iPhone", "price": 999.0, "tags": ["phone"]}
```

#### 1.3 mypy 静态类型检查

```bash
# 安装
pip install mypy

# 基本用法
mypy script.py

# 严格模式
mypy --strict script.py

# 配置在 pyproject.toml
# [tool.mypy]
# strict = true
```

```python
# mypy 能发现的错误
def add(a: int, b: int) -> int:
    return a + b

add(1, 2)        # ✅
add("1", "2")    # ❌ mypy: Argument 1 has incompatible type "str"
```

#### 1.4 pydantic 数据验证简介（v2）

```python
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int = 0

# 自动类型转换与校验
p = Product(id="1", name="iPhone", price="999.99")  # 字符串自动转
print(p)  # id=1 name='iPhone' price=999.99 stock=0

# JSON 序列化/反序列化
json_data = p.model_dump_json()
p2 = Product.model_validate_json(json_data)
```

#### 1.5 类型注解最佳实践

| 原则 | 说明 |
|------|------|
| 公开 API 必须注解 | 函数签名、类属性 |
| 内部局部变量可省略 | mypy 能推断 |
| 复杂类型用别名 | 提高可读性 |
| 避免 Any | 除非必要（如 FFI） |
| mypy CI 集成 | 提交前检查 |

### 二、元编程

#### 2.1 一切皆对象

在 Python 中，**类也是对象**。类可以被赋值、传参、返回，而创建这些"类对象"的东西就是**元类**（metaclass），Python 中所有元类的根基是 `type`。

```python
class MyClass:
    pass

print(type(MyClass))     # <class 'type'>
print(type(MyClass()))  # <class '__main__.MyClass'>
```

#### 2.2 type() 的两面性

```python
# 用法一：查看对象类型
print(type(obj))

# 用法二：动态创建类
MyClass = type('MyClass', (object,), {'attr': 1, 'method': lambda self: ...})
# 等价于：
# class MyClass(object):
#     attr = 1
#     def method(self): ...
```

`type(name, bases, dict)` 三个参数：
- `name`：类名
- `bases`：父类元组
- `dict`：类属性/方法的字典

#### 2.3 动态创建类

```python
def greet(self):
    return f"Hello, I'm {self.name}"

# 动态创建类
Product = type('Product', (object,), {
    'name': 'default',
    'greet': greet,
})

p = Product()
print(p.greet())  # Hello, I'm default
```

#### 2.4 元类 Metaclass

元类是"创建类的类"。普通类创建实例，元类创建类。

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        # 在类创建前可以修改 namespace
        print(f"创建类 {name}")
        return super().__new__(mcs, name, bases, namespace)

class MyClass(metaclass=Meta):
    pass
# 输出：创建类 MyClass
```

##### 元类中的方法调用顺序

```
class MyClass(metaclass=Meta) 触发：
  1. Meta.__call__     ← 创建实例时调用（my_obj = MyClass()）
  2. Meta.__new__      ← 创建类对象
  3. Meta.__init__     ← 初始化类对象

实例化 my_obj = MyClass() 触发：
  1. Meta.__call__（由元类控制）
     → 调用 MyClass.__new__ 创建实例
     → 调用 MyClass.__init__ 初始化实例
```

##### 元类应用场景

- **ORM**：Django ORM、SQLAlchemy 用元类自动映射数据库表
- **API 注册**：自动注册所有子类到全局注册表
- **插件系统**：扫描并加载插件类

```python
# 元类应用：自动注册所有子类
class ModelMeta(type):
    registry: dict = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # 跳过基类本身
            mcs.registry[name] = cls
        return cls

class Model(metaclass=ModelMeta):
    pass

class Product(Model): pass
class Order(Model): pass

print(ModelMeta.registry)  # {'Product': ..., 'Order': ...}
```

#### 2.5 __init_subclass__（3.6+）

更简单的类创建钩子，适用于不需要完整元类的场景。

```python
class Plugin:
    _plugins: list = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin._plugins.append(cls)
        print(f"注册插件：{cls.__name__}")

class PaymentPlugin(Plugin): pass
# 输出：注册插件：PaymentPlugin
```

#### 2.6 __class_getitem__

支持类参数化语法 `MyClass[int]`，用于泛型支持。

```python
class Container:
    def __class_getitem__(cls, item):
        return f"Container[{item.__name__}]"

print(Container[int])   # Container[int]
print(Container[str])   # Container[str]
```

#### 2.7 描述符协议 Descriptor

描述符是一个实现了 `__get__`、`__set__`、`__delete__` 中至少一个的类。

```python
class ValidatedField:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        if value < 0:
            raise ValueError(f"{self.name} 不能为负数")
        obj.__dict__[self.name] = value
```

| 描述符类型 | 实现方法 | 优先级 |
|----------|---------|--------|
| 数据描述符 | `__get__` + `__set__` | 高于实例字典 |
| 非数据描述符 | 只有 `__get__` | 低于实例字典 |

```python
# property 就是描述符
class Product:
    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("价格不能为负")
        self._price = value
```

#### 2.8 dataclasses 深入

```python
from dataclasses import dataclass, field

@dataclass
class Product:
    name: str
    price: float
    stock: int = 0
    tags: list[str] = field(default_factory=list)  # 可变默认值必须用 default_factory
    _internal: str = field(init=False, repr=False, compare=False)  # 不参与 init/repr/compare

    def __post_init__(self):
        # 初始化后钩子
        self._internal = f"{self.name}-{self.price}"

# frozen=True：不可变数据类
@dataclass(frozen=True)
class Point:
    x: int
    y: int

# slots=True（3.10+）：节省内存、禁止动态属性
@dataclass(slots=True)
class Order:
    id: int
    total: float

# kw_only=True（3.10+）：强制关键字参数
@dataclass(kw_only=True)
class Config:
    host: str
    port: int
```

## 关键知识点总结

### 类型注解语法速查表

| 注解 | 含义 | 示例 |
|------|------|------|
| `x: int` | 整型变量 | `x: int = 10` |
| `def f() -> str` | 返回字符串 | `def greet() -> str:` |
| `list[int]` | 整型列表 | `prices: list[int]` |
| `dict[str, int]` | 字符串到整型字典 | `stock: dict[str, int]` |
| `tuple[int, str]` | 固定长度元组 | `point: tuple[int, str]` |
| `int \| None` | 可空整型（3.10+） | `def find() -> int \| None` |
| `Callable[[int], str]` | 可调用对象 | `fn: Callable[[int], str]` |
| `Literal["A", "B"]` | 字面量类型 | `mode: Literal["r", "w"]` |

### typing 常用类型速查

| 类型 | 用途 | 版本 |
|------|------|------|
| `Optional[T]` | 等价于 `T \| None` | 3.5+ |
| `Union[A, B]` | 联合类型 | 3.5+ |
| `Callable` | 可调用对象 | 3.5+ |
| `TypeVar` | 类型变量 | 3.5+ |
| `Generic` | 泛型基类 | 3.5+ |
| `Protocol` | 结构子类型 | 3.8+ |
| `TypedDict` | 类型化字典 | 3.8+ |
| `Literal` | 字面量类型 | 3.8+ |
| `TypeAlias` | 类型别名 | 3.10+ |
| `NewType` | 新类型 | 3.5+ |
| `Never` | 不可能有值 | 3.11+ |

### 元类方法调用顺序图

```
定义 class MyClass(metaclass=Meta):
    │
    ▼
Meta.__new__(mcs, name, bases, namespace)  ← 创建类对象
    │
    ▼
Meta.__init__(cls, name, bases, namespace) ← 初始化类对象
    │
    ▼
（类 MyClass 创建完成）

实例化 obj = MyClass():
    │
    ▼
Meta.__call__(cls, *args, **kwargs)        ← 元类控制实例化
    │
    ├──→ MyClass.__new__(cls, *args)      ← 创建实例
    │
    └──→ MyClass.__init__(self, *args)     ← 初始化实例
```

### 描述符协议图

```
属性访问 obj.attr:
    │
    ▼
查找顺序：
    1. 数据描述符（__get__ + __set__）
    2. 实例字典 obj.__dict__['attr']
    3. 非数据描述符（只有 __get__）
    4. 类字典
    5. __getattr__（兜底）

property = 数据描述符
```

### 并发模型选型表（复习）

| 场景 | 推荐模型 |
|------|---------|
| IO 密集型 + 高并发 | asyncio |
| IO 密集型 + 简单 | threading |
| CPU 密集型 | multiprocessing |
| 混合型 | concurrent.futures |

## 实战练习

### 练习 1：类型化电商数据模型

用类型注解完善 `eshop` 数据模型：
- 定义 `Product`、`Order`、`OrderItem` 的 TypedDict
- 定义对应的 `@dataclass` 类
- 用 `Literal` 限定订单状态（`"pending" | "paid" | "shipped" | "delivered"`）
- 编写带类型注解的函数：`calculate_total(items: list[OrderItem]) -> float`
- 用 mypy 检查代码

### 练习 2：泛型 Repository 模式

实现一个泛型 `Repository[T]`：
- 用 `TypeVar` 和 `Generic` 定义泛型类
- 用 `Protocol` 定义 `Identifiable` 接口（必须有 `id` 属性）
- 用 `Protocol` 定义 `Repository` 接口（`get` / `save` / `delete` 方法）
- 实现 `InMemoryRepository[T]` 并约束 T 必须是 Identifiable

### 练习 3：模型注册元类 + 描述符验证

结合元类与描述符：
- 用元类实现模型自动注册（所有继承 `Model` 的子类自动加入注册表）
- 用描述符实现 `ValidatedField`：验证商品价格非负、库存非负
- 用描述符实现 `CachedField`：缓存计算结果（如订单总金额）
- 用 `__init_subclass__` 替代元类实现同样的注册功能，对比两者差异
