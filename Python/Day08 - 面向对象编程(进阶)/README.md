# Day08 - 面向对象编程（进阶）

> 魔术方法、`@dataclass`、枚举和抽象类让 Python OOP 更加强大和优雅——掌握它们，你就能写出既 Pythonic 又具备工程严谨性的数据模型。

Day07 打下了 OOP 的地基：类、属性、继承。真实的工程中，我们还需要：让对象支持比较与运算（魔术方法）、用最少代码定义数据类（`@dataclass`）、用枚举约束取值范围（`Enum`）、用抽象基类定义接口契约（ABC）、用 Mixin 灵活组合功能。本章把这些进阶武器一一展开，让电商数据模型 `Product` / `Order` / `Customer` 真正具备生产级的表达力。

---

## 学习目标

- 理解多继承与 MRO（方法解析顺序），能分析钻石继承
- 掌握常用魔术方法：比较（`__eq__`/`__lt__`/`__hash__`）、容器（`__len__`/`__getitem__`/`__contains__`）、调用（`__call__`）、运算符重载
- 掌握 `@dataclass` 的用法：`field(default_factory)`、`frozen=True`、`order=True`
- 掌握 `Enum` 枚举的定义与使用，能用它替代魔法字符串
- 掌握抽象基类 ABC 与 `@abstractmethod`，能设计接口契约
- 理解 Mixin 模式，能用小而专注的类组合功能
- 了解元类 `type`、`__slots__` 与对象拷贝（浅拷贝 / 深拷贝）

---

## 理论知识讲解

### 一、多继承与 MRO

#### 1.1 多继承

Python 支持多继承，一个类可以继承多个父类：

```python
class A:
    def hello(self):
        return "A"

class B:
    def hello(self):
        return "B"

class C(A, B):     # 多继承
    pass

c = C()
c.hello()          # 'A'，按 MRO 顺序找
```

#### 1.2 MRO（Method Resolution Order）

方法解析顺序决定属性/方法的查找顺序。Python 3 用 **C3 线性化**算法：

```python
print(C.__mro__)
# (<class 'C'>, <class 'A'>, <class 'B'>, <class 'object'>)
```

#### 1.3 钻石继承

```
       A
      / \
     B   C
      \ /
       D
```

```python
class A:
    def greet(self): return "A"

class B(A):
    def greet(self): return "B"

class C(A):
    def greet(self): return "C"

class D(B, C):
    pass

D().greet()        # 'B'，MRO: D → B → C → A
print(D.__mro__)   # (D, B, C, A, object)
```

`super()` 在多继承中按 MRO 顺序调用，不是简单的"父类"。

---

### 二、Mixin 模式

Mixin 是小而专注的类，提供单一功能，通过多继承组合：

```python
class LogMixin:
    """日志功能混入"""
    def log(self, msg):
        print(f"[LOG] {self.__class__.__name__}: {msg}")

class SerializeMixin:
    """序列化功能混入"""
    def to_dict(self):
        return self.__dict__.copy()

class Product(LogMixin, SerializeMixin):   # 组合两个 Mixin
    def __init__(self, name, price):
        self.name = name
        self.price = price

p = Product("iPhone", 5999)
p.log("created")      # 来自 LogMixin
p.to_dict()           # 来自 SerializeMixin
```

> **命名约定**：Mixin 类通常以 `Mixin` 结尾，表示它是功能混入而非独立基类。

---

### 三、魔术方法（Magic Methods）

#### 3.1 比较方法

| 方法 | 运算符 | 用途 |
|------|--------|------|
| `__eq__` | `==` | 相等 |
| `__ne__` | `!=` | 不等 |
| `__lt__` | `<` | 小于 |
| `__le__` | `<=` | 小于等于 |
| `__gt__` | `>` | 大于 |
| `__ge__` | `>=` | 大于等于 |
| `__hash__` | `hash()` | 哈希（作字典键/集合元素） |

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __eq__(self, other):
        if not isinstance(other, Product):
            return NotImplemented
        return self.name == other.name and self.price == other.price

    def __lt__(self, other):
        return self.price < other.price

    def __hash__(self):
        return hash((self.name, self.price))
```

**functools.total_ordering**：只定义 `__eq__` 和 `__lt__`，自动生成其余比较方法：

```python
from functools import total_ordering

@total_ordering
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __eq__(self, other):
        return isinstance(other, Product) and self.price == other.price

    def __lt__(self, other):
        return self.price < other.price
```

#### 3.2 容器方法

| 方法 | 触发 | 用途 |
|------|------|------|
| `__len__` | `len(obj)` | 长度 |
| `__getitem__` | `obj[key]` | 索引访问 |
| `__setitem__` | `obj[key] = v` | 索引赋值 |
| `__delitem__` | `del obj[key]` | 索引删除 |
| `__contains__` | `x in obj` | 成员判断 |
| `__iter__` | `for x in obj` | 迭代 |

```python
class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.items = []

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __contains__(self, item):
        return item in self.items
```

#### 3.3 调用方法 `__call__`

让实例像函数一样可调用：

```python
class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, x):
        return x * self.factor

double = Multiplier(2)
double(5)      # 10，像函数一样调用
```

#### 3.4 运算符重载

| 方法 | 运算符 |
|------|--------|
| `__add__` | `+` |
| `__sub__` | `-` |
| `__mul__` | `*` |
| `__truediv__` | `/` |

```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
```

---

### 四、`@dataclass`（3.7+）

自动生成 `__init__` / `__repr__` / `__eq__` 等样板代码：

```python
from dataclasses import dataclass, field

@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int = 0
    tags: list = field(default_factory=list)   # 可变默认值必须用 default_factory
```

#### 关键参数

| 参数 | 作用 | 默认 |
|------|------|------|
| `init` | 生成 `__init__` | True |
| `repr` | 生成 `__repr__` | True |
| `eq` | 生成 `__eq__` | True |
| `order` | 生成 `__lt__`/`__le__` 等 | False |
| `frozen` | 不可变（可哈希） | False |
| `slots` | 生成 `__slots__`（3.10+） | False |

```python
@dataclass(frozen=True)            # 不可变数据类，可哈希
class Point:
    x: float
    y: float

@dataclass(order=True)             # 支持排序
class Priority:
    priority: int
    name: str = field(compare=False)   # compare=False 不参与比较
```

> **何时用 dataclass**：主要用来存数据的类（DTO/模型/配置），用 dataclass 省去样板代码。

---

### 五、Enum 枚举

用枚举替代魔法字符串/数字，让代码更安全可读：

```python
from enum import Enum, auto

class OrderStatus(Enum):
    PENDING = 1
    PAID = 2
    SHIPPED = 3
    DELIVERED = 4
    CANCELLED = 5

status = OrderStatus.PAID
status.name       # 'PAID'
status.value      # 2
```

**IntEnum / StrEnum**（3.11+）：

```python
from enum import IntEnum

class Color(IntEnum):
    RED = 1
    GREEN = 2

Color.RED == 1       # True，可与 int 比较
```

**auto() 自动赋值**：

```python
class Status(Enum):
    DRAFT = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()
```

**遍历与访问**：

```python
for s in OrderStatus:        # 遍历所有成员
    print(s)

OrderStatus['PAID']         # 通过名称访问 → OrderStatus.PAID
OrderStatus(2)              # 通过值访问 → OrderStatus.PAID
```

---

### 六、抽象基类 ABC

定义接口契约，强制子类实现特定方法：

```python
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    """抽象基类：数据仓库接口"""

    @abstractmethod
    def find(self, id: int):
        """子类必须实现"""
        ...

    @abstractmethod
    def save(self, obj):
        ...

    @abstractmethod
    def delete(self, id: int):
        ...

# 不能实例化抽象类
# repo = BaseRepository()    # TypeError

class ProductRepository(BaseRepository):
    def find(self, id):
        return f"找到商品 {id}"
    def save(self, obj):
        return f"保存 {obj}"
    def delete(self, id):
        return f"删除 {id}"

repo = ProductRepository()    # 子类实现所有抽象方法后可实例化
```

**@abstractmethod + @property**：

```python
class Shape(ABC):
    @property
    @abstractmethod
    def area(self):
        """子类必须实现该属性"""
        ...
```

> **意义**：ABC 提供"接口约定"，让代码契约清晰，配合类型注解提升安全性。

---

### 七、元类 type 简介

`type` 是所有类的元类（创建类的类）：

```python
# 普通方式定义类
class MyClass:
    x = 1

# 等价的动态创建
MyClass = type('MyClass', (), {'x': 1})
```

```python
# 自定义元类（了解即可）
class MyMeta(type):
    def __new__(mcs, name, bases, namespace):
        print(f"创建类 {name}")
        return super().__new__(mcs, name, bases, namespace)

class Foo(metaclass=MyMeta):
    pass
```

---

### 八、`__slots__`

固定实例属性列表，禁止动态添加，节省内存：

```python
class Product:
    __slots__ = ['id', 'name', 'price']    # 只允许这三个属性

    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price

p = Product(1, "iPhone", 5999)
# p.stock = 50          # AttributeError，不能添加 slots 外的属性
# p.__dict__             # AttributeError，slots 类没有 __dict__
```

> **适用场景**：大量实例（百万级）时节省内存。代价是失去动态添加属性的灵活性。

---

### 九、对象拷贝

```python
import copy

# 浅拷贝：复制对象本身，但内部引用仍共享
new_list = copy.copy(original)

# 深拷贝：递归复制所有内部对象
new_list = copy.deepcopy(original)
```

```python
import copy

class Order:
    def __init__(self, items):
        self.items = items

o1 = Order([1, 2, 3])
o2 = copy.copy(o1)          # 浅拷贝
o3 = copy.deepcopy(o1)      # 深拷贝

o1.items.append(4)
o2.items                    # [1, 2, 3, 4] —— 浅拷贝共享内部列表
o3.items                    # [1, 2, 3]     —— 深拷贝完全独立
```

可自定义拷贝行为：实现 `__copy__` 和 `__deepcopy__`。

---

## 代码文件说明

| 文件 | 内容 | 电商场景 |
|------|------|---------|
| `Code/magic_methods.py` | 比较方法、容器方法、`__call__`、运算符重载、`total_ordering` | Product 比较排序、Order 索引访问、可调用对象 |
| `Code/dataclass_enum.py` | `@dataclass`、`field`、`frozen`、`Enum`/`IntEnum`/`auto` | 完整数据模型 Product/Order + OrderStatus 枚举 |
| `Code/abc_demo.py` | ABC、`@abstractmethod`、子类实现 | BaseRepository → ProductRepository/OrderRepository |
| `Code/mixin_demo.py` | Mixin 模式、多继承组合、MRO 查看 | Product 混入 LogMixin + SerializeMixin |

运行方式：

```bash
cd "Python/Day08 - 面向对象编程(进阶)/Code"
python magic_methods.py
python dataclass_enum.py
python abc_demo.py
python mixin_demo.py
```

---

## 关键知识点总结

### 魔术方法速查表

| 魔术方法 | 触发 | 用途 |
|---------|------|------|
| `__init__` | `Obj()` | 初始化 |
| `__str__` | `print()`/`str()` | 用户字符串 |
| `__repr__` | `repr()` | 开发者字符串 |
| `__eq__` | `==` | 相等比较 |
| `__lt__` | `<` | 小于 |
| `__hash__` | `hash()` | 哈希（作字典键） |
| `__bool__` | `bool()` | 真值测试 |
| `__len__` | `len()` | 长度 |
| `__getitem__` | `obj[k]` | 索引取值 |
| `__setitem__` | `obj[k]=v` | 索引赋值 |
| `__contains__` | `in` | 成员判断 |
| `__iter__` | `for` | 迭代 |
| `__call__` | `obj()` | 可调用 |
| `__add__` | `+` | 加法 |
| `__enter__`/`__exit__` | `with` | 上下文管理（Day12） |

### `@dataclass` 参数表

| 参数 | 默认 | 作用 |
|------|------|------|
| `init` | True | 生成 `__init__` |
| `repr` | True | 生成 `__repr__` |
| `eq` | True | 生成 `__eq__` |
| `order` | False | 生成 `__lt__`/`__le__`/`__gt__`/`__ge__` |
| `frozen` | False | 不可变（可哈希） |
| `slots` | False | 生成 `__slots__`（3.10+） |
| `unsafe_hash` | False | 强制生成 `__hash__` |

### Enum 用法速查

| 操作 | 语法 | 示例 |
|------|------|------|
| 定义 | `class X(Enum)` | `class Color(Enum): RED=1` |
| 访问 | `X.NAME` | `Color.RED` |
| 按名查 | `X['NAME']` | `Color['RED']` |
| 按值查 | `X(value)` | `Color(1)` |
| 名称 | `.name` | `'RED'` |
| 值 | `.value` | `1` |
| 遍历 | `for x in X` | — |
| 自动值 | `auto()` | `RED = auto()` |

### ABC 设计模式图

```
┌─────────────────────────┐
│   BaseRepository (ABC)  │  ← 抽象基类，定义接口
│   ───────────────────   │
│   + find(id) [abstract] │
│   + save(obj) [abstract]│
│   + delete(id) [abstract]│
│   + count() [concrete]  │  ← 可有具体方法
└───────────┬─────────────┘
            │ 继承
   ┌────────┴─────────┐
   ▼                  ▼
┌──────────────┐  ┌──────────────┐
│ProductRepo   │  │OrderRepo     │  ← 子类实现所有抽象方法
│ find() 实现  │  │ find() 实现  │
│ save() 实现  │  │ save() 实现  │
│ delete() 实现│  │ delete() 实现│
└──────────────┘  └──────────────┘

不能实例化：BaseRepository()  →  TypeError
```

### 多继承 MRO 图解

```
钻石继承：

       object
         │
          A
        /   \
       B     C
        \   /
          D

D.__mro__ = (D, B, C, A, object)

super() 调用链（D 的方法中调 super()）：
  D.method() → B.method() → C.method() → A.method()

注意：super() 不是"调用父类"，而是"按 MRO 调用下一个类"
```

---

## 实战练习

### 练习 1：可排序的 Product

用 `@dataclass(order=True)` 定义 `Product`，让商品可按价格排序。再写一个 `Order` 类实现 `__len__`、`__getitem__`、`__contains__`，让订单能像列表一样用 `len(order)`、`order[0]`、`"iPhone" in order` 操作。

### 练习 2：订单状态枚举

定义 `OrderStatus(Enum)` 枚举（PENDING/PAID/SHIPPED/DELIVERED/CANCELLED），用 `auto()` 自动赋值。写一个 `Order` 类，`status` 字段类型为 `OrderStatus`，提供 `pay()`、`ship()`、`cancel()` 方法做状态转换，并校验非法转换（如已取消的订单不能再次支付）。

### 练习 3：数据仓库抽象

定义 `BaseRepository(ABC)` 抽象基类，含 `find(id)`、`save(obj)`、`delete(id)`、`list_all()` 抽象方法。实现 `ProductRepository` 和 `CustomerRepository` 两个子类，内部用字典存储数据。再加一个 `LogMixin`，让两个 Repository 通过多继承获得日志能力，验证 MRO 顺序。

---

**下一章预告**：Day09 进入工程化阶段，学习模块、包与标准库，把零散的脚本组织成结构化项目。
