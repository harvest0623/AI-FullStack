# Day07 - 面向对象编程（基础）

> 面向对象编程（OOP）是组织复杂代码的核心范式，Python 的 OOP 简洁而强大——用类把数据和操作数据的方法打包在一起，让代码结构更清晰、复用性更强。

当电商系统中的商品、订单、客户越来越多时，用散落的字典和函数会让代码难以维护。OOP 提供了一种自然的建模方式：把"商品"抽象成 `Product` 类，把"订单"抽象成 `Order` 类，每个对象自带数据和操作。本章讲解 Python OOP 的基础概念：类与对象、`__init__`、`self`、实例属性与类属性、`__str__`/`__repr__`、访问控制约定、`@property`、`@staticmethod`/`@classmethod`、继承与 `super()`。

---

## 学习目标

- 理解类与对象的关系，能用 `class` 定义类并创建实例
- 掌握 `__init__` 构造器与 `self` 参数的作用
- 区分实例属性与类属性，理解访问优先级
- 掌握 `__str__` 与 `__repr__` 的区别与编写
- 理解访问控制约定（public / protected / private / 名称重整）
- 掌握 `@property` 装饰器实现 getter/setter/deleter 与属性验证
- 掌握 `@staticmethod` 与 `@classmethod` 的区别与使用场景
- 掌握单继承、`super()`、方法重写，理解 `isinstance()` / `issubclass()`

---

## 理论知识讲解

### 一、类与对象

- **类（Class）**：是创建对象的"蓝图" / "模板"，定义了属性和行为
- **对象（Object）**：是类的实例，每个对象拥有独立的数据

```python
class Product:
    """商品类"""
    pass

p1 = Product()      # 实例化
p2 = Product()
print(p1 is p2)     # False，两个不同对象
```

类名使用 **PascalCase** 命名（如 `OrderItem`、`CustomerService`）。

---

### 二、`__init__` 构造器与 self

`__init__` 是初始化方法，在创建对象时自动调用；`self` 指向当前实例：

```python
class Product:
    def __init__(self, pid: str, name: str, price: float):
        self.id = pid            # self.属性 = 值
        self.name = name
        self.price = price

p = Product("P001", "iPhone", 5999)
# 等价于：Product.__init__(p, "P001", "iPhone", 5999)
print(p.name)                    # iPhone
```

- `self` 必须是实例方法的第一个参数（名字可改但约定用 `self`）
- Python 显式传递 `self`，调用时不需要手动传

---

### 三、实例属性 vs 类属性

#### 3.1 实例属性

每个对象独立拥有，通过 `self.xxx = value` 在 `__init__` 中定义：

```python
class Product:
    def __init__(self, name, price):
        self.name = name       # 每个实例独立的 name
        self.price = price
```

#### 3.2 类属性

所有实例共享，直接在类体中定义：

```python
class Product:
    tax_rate = 0.13            # 类属性，所有实例共享
    count = 0

    def __init__(self, name, price):
        self.name = name
        self.price = price
        Product.count += 1     # 通过类名访问/修改类属性
```

#### 3.3 访问优先级

通过实例访问属性时，**先查实例属性，再查类属性**：

```python
p = Product("iPhone", 5999)
print(p.tax_rate)      # 0.13，实例没有 tax_rate，向上找类属性
print(Product.tax_rate)  # 0.13，直接访问类属性
```

> ⚠️ **陷阱**：通过实例赋值会创建实例属性，遮蔽类属性（不影响其他实例）：
> ```python
> p.tax_rate = 0.1      # 创建实例属性，不修改类属性
> Product.tax_rate       # 仍是 0.13
> ```

---

### 四、实例方法

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def discount(self, rate: float) -> float:
        """实例方法：第一个参数是 self"""
        return self.price * (1 - rate)

p = Product("iPhone", 5999)
p.discount(0.1)        # 5399.1
```

---

### 五、`__str__` 与 `__repr__`

| 方法 | 触发 | 面向 | 要求 |
|------|------|------|------|
| `__str__` | `print(obj)` / `str(obj)` | 用户 | 可读性好 |
| `__repr__` | `repr(obj)` / 调试输出 / 列表中 | 开发者 | 尽量能重建对象 |

```python
class Product:
    def __init__(self, pid, name, price):
        self.id = pid
        self.name = name
        self.price = price

    def __str__(self):
        return f"{self.name} (¥{self.price})"

    def __repr__(self):
        return f"Product(id={self.id!r}, name={self.name!r}, price={self.price})"

p = Product("P001", "iPhone", 5999)
print(p)          # iPhone (¥5999)        ← __str__
print(repr(p))    # Product(id='P001', name='iPhone', price=5999)  ← __repr__
print([p])        # [Product(...)]        ← 列表中用 __repr__
```

> **建议**：`__repr__` 总是定义；`__str__` 可选。两者都定义时 `print` 优先用 `__str__`。

---

### 六、访问控制约定

Python 没有真正的访问修饰符，靠**命名约定**：

| 约定 | 写法 | 含义 | 强制？ |
|------|------|------|--------|
| public | `name` | 公开 | 否 |
| protected | `_name` | 约定内部用（开发者自觉） | 否 |
| private | `__name` | 名称重整（name mangling） | 部分 |

```python
class Product:
    def __init__(self, name, cost):
        self.name = name           # public
        self._cost = cost          # protected（约定）
        self.__secret = "key"      # private，会被重整为 _Product__secret

p = Product("iPhone", 4000)
print(p.name)          # iPhone
print(p._cost)         # 4000（能访问，但不建议）
# print(p.__secret)    # AttributeError
print(p._Product__secret)  # "key"（重整后仍可访问，但极不推荐）
```

> 名称重整（name mangling）：`__attr` 在类内部被自动改名为 `_ClassName__attr`，主要防止子类意外覆盖。

---

### 七、`@property` 装饰器

把方法变成"属性"访问，支持 getter / setter / deleter：

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price       # 会调用 setter

    @property
    def price(self):
        """getter：读取价格"""
        return self._price

    @price.setter
    def price(self, value):
        """setter：设置价格，带验证"""
        if value < 0:
            raise ValueError("价格不能为负")
        self._price = value

    @price.deleter
    def price(self):
        """deleter：删除价格"""
        print(f"删除 {self.name} 的价格")
        del self._price

p = Product("iPhone", 5999)
print(p.price)        # 5999，像属性一样访问（不加括号）
p.price = 4999        # 调用 setter
# p.price = -1        # ValueError: 价格不能为负
del p.price           # 调用 deleter
```

**计算属性**（派生属性）：

```python
class Product:
    def __init__(self, price, discount_rate=0.0):
        self.price = price
        self.discount_rate = discount_rate

    @property
    def final_price(self):
        """计算属性：不存储，每次访问时计算"""
        return self.price * (1 - self.discount_rate)
```

---

### 八、`@staticmethod` 与 `@classmethod`

| 装饰器 | 第一个参数 | 能否访问类属性 | 能否访问实例属性 | 典型用途 |
|--------|-----------|--------------|----------------|---------|
| `@staticmethod` | 无 | 否（需用类名） | 否 | 工具函数 |
| `@classmethod` | `cls`（类本身） | 是 | 否 | 替代构造器、操作类属性 |

```python
class Product:
    count = 0

    def __init__(self, name, price):
        self.name = name
        self.price = price
        Product.count += 1

    @staticmethod
    def is_valid_price(price):
        """静态方法：与类相关，但不需要 self/cls"""
        return price > 0

    @classmethod
    def from_dict(cls, data):
        """类方法：替代构造器，cls 是当前类"""
        return cls(data["name"], data["price"])

    @classmethod
    def get_count(cls):
        """类方法：操作类属性"""
        return cls.count
```

**替代构造器**是 `@classmethod` 最经典的用法，让对象能从不同数据源创建。

---

### 九、继承

#### 9.1 单继承

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name} makes a sound"

class Dog(Animal):       # 继承 Animal
    def speak(self):     # 方法重写
        return f"{self.name} says Woof"

d = Dog("Rex")
d.speak()         # Rex says Woof
```

#### 9.2 super()

调用父类的方法，常用于 `__init__`：

```python
class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)      # 调用父类 __init__
        self.breed = breed

    def speak(self):
        parent_msg = super().speak()  # 调用父类方法
        return f"{parent_msg}; {self.name} says Woof"
```

#### 9.3 isinstance() / issubclass()

```python
isinstance(d, Dog)       # True
isinstance(d, Animal)    # True（子类实例也是父类实例）
issubclass(Dog, Animal)  # True
issubclass(Animal, Dog)  # False
```

#### 9.4 object 基类

Python 3 中所有类都隐式继承自 `object`：

```python
class Foo: pass
isinstance(Foo(), object)   # True
```

---

### 十、OOP 设计原则预告

- **封装**：把数据和方法打包，对外隐藏实现细节（`_` / `__`）
- **继承**：子类复用父类的代码，扩展或修改行为
- **多态**：不同对象对同一方法有不同实现（Day08 详讲）

---

## 代码文件说明

| 文件 | 内容 | 电商场景 |
|------|------|---------|
| `Code/class_basics.py` | 类定义、`__init__`/self、实例属性与类属性、`__str__`/`__repr__` | 完整的商品 Product 类 |
| `Code/inheritance.py` | 单继承、super()、方法重写、isinstance/issubclass | Product → DigitalProduct / PhysicalProduct，Order 继承体系 |
| `Code/property_decorator.py` | @property getter/setter/deleter、属性验证、计算属性、@staticmethod/@classmethod | price setter 验证、discount_price 计算属性、from_dict 类方法 |

运行方式：

```bash
cd "Python/Day07 - 面向对象编程(基础)/Code"
python class_basics.py
python inheritance.py
python property_decorator.py
```

---

## 关键知识点总结

### 类属性 vs 实例属性对比表

| 特性 | 类属性 | 实例属性 |
|------|--------|---------|
| 定义位置 | 类体中 | `__init__` 中 `self.xxx` |
| 归属 | 类 | 实例 |
| 共享 | 所有实例共享 | 每个实例独立 |
| 访问 | `ClassName.attr` 或 `self.attr` | `self.attr` |
| 修改 | `ClassName.attr = v` | `self.attr = v` |
| 通过实例赋值 | 创建实例属性，遮蔽类属性 | 正常修改实例属性 |

### @property / @staticmethod / @classmethod 对比表

| 装饰器 | 第一个参数 | 访问实例 | 访问类 | 用途 |
|--------|-----------|---------|--------|------|
| 普通方法 | `self` | ✅ | ✅(类名) | 操作实例数据 |
| `@property` | `self` | ✅ | ✅(类名) | 把方法变属性 |
| `@staticmethod` | 无 | ❌ | ❌(需类名) | 工具函数 |
| `@classmethod` | `cls` | ❌ | ✅ | 替代构造器 |

### 访问控制约定表

| 约定 | 示例 | 重整 | 含义 |
|------|------|------|------|
| public | `name` | 无 | 公开 API |
| protected | `_name` | 无 | 内部用（约定） |
| private | `__name` | `_ClassName__name` | 防子类覆盖 |

### 继承关系图

```
        object            ← 所有类的基类
          │
        Animal            ← 父类（基类）
        /   \
      Dog   Cat           ← 子类（派生类），继承 Animal
       │
    GuideDog              ← 多层继承

isinstance(dog, Dog)      → True
isinstance(dog, Animal)   → True（子类实例也是父类实例）
isinstance(dog, object)   → True
issubclass(Dog, Animal)   → True
```

---

## 实战练习

### 练习 1：完善 Product 类

为 `Product` 类添加：① `__str__` 和 `__repr__`；② 类属性 `count` 统计创建的商品数；③ `@property` 对 `price` 做 setter 验证（必须 > 0）；④ `@classmethod from_dict` 从字典创建实例。

### 练习 2：员工继承体系

设计 `Employee` 基类（属性：name, salary），派生 `Manager`（增加 department 和 bonus）和 `Developer`（增加 language）。用 `super().__init__()` 调用父类构造器，重写 `__str__`，并用 `isinstance()` 验证继承关系。

### 练习 3：温度转换器

写一个 `Temperature` 类：① `__init__(celsius)` 存储摄氏度；② `@property fahrenheit` 计算属性返回华氏度；③ `@staticmethod is_valid(c)` 判断温度是否合法（> -273.15）；④ `@classmethod from_fahrenheit(f)` 用华氏度创建实例。

---

**下一章预告**：Day08 进入 OOP 进阶，学习魔术方法（运算符重载）、`@dataclass`、`Enum` 枚举、抽象基类 ABC、Mixin 模式，让数据模型更优雅。
