# Day06 - 函数与 Lambda

> 函数是代码复用的基本单元，Python 的函数是"一等公民"——可赋值、可传参、可返回，配合丰富的参数形式和 Lambda 表达式，能写出既灵活又优雅的代码。

随着程序规模增长，把重复逻辑封装成函数是控制复杂度的第一步。Python 函数远不止"输入参数返回结果"那么简单：它支持位置参数、关键字参数、默认参数、可变参数、仅关键字参数、仅位置参数等多种形式；函数本身可以作为变量传递、作为参数传入、作为返回值返回；闭包让函数"记住"外部状态。本章系统讲解函数的方方面面，并通过电商场景演示其实战价值。

---

## 学习目标

- 掌握函数的定义、调用、返回值与文档字符串（docstring）
- 理解并能熟练使用 5 种参数形式：位置 / 默认 / `*args` / `**kwargs` / 仅关键字 / 仅位置参数
- 理解函数作为"一等公民"的特性：赋值、传参、返回、存入数据结构
- 掌握 Lambda 匿名函数与高阶函数（map / filter / reduce / sorted）
- 理解闭包原理与 `nonlocal` 关键字，能编写工厂函数和计数器
- 掌握作用域 LEGB 规则与 `global` / `nonlocal` 的使用
- 了解函数注解（type hints）与递归

---

## 理论知识讲解

### 一、函数定义与调用

```python
def function_name(params):
    """文档字符串"""
    # 函数体
    return value
```

```python
def greet(name: str) -> str:
    """返回问候语（docstring）"""
    return f"Hello, {name}!"

msg = greet("Python")    # 调用
```

- `def` 关键字定义函数
- 函数名遵循 snake_case 命名约定
- `return` 返回值；无 `return` 或 `return` 无值则返回 `None`
- 三引号字符串是 docstring，可通过 `__doc__` 或 `help()` 查看

---

### 二、参数类型

Python 函数支持非常灵活的参数形式，这是它区别于很多语言的一大特色。

#### 2.1 位置参数

```python
def add(a, b):
    return a + b
add(1, 2)           # a=1, b=2，按位置对应
```

#### 2.2 默认参数

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}"
greet("Tom")               # Hello, Tom
greet("Tom", "Hi")         # Hi, Tom
```

> ⚠️ **陷阱**：默认参数必须是不可变对象。可变默认值（如 `[]`）会在多次调用间共享：

```python
def append_to(item, lst=[]):   # ❌ 危险！
    lst.append(item)
    return lst
append_to(1)    # [1]
append_to(2)    # [1, 2] —— 不是 [2]！默认列表被共享

# 正确写法
def append_to_safe(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

#### 2.3 可变位置参数 `*args`

```python
def sum_all(*args):
    return sum(args)
sum_all(1, 2, 3, 4)    # args=(1,2,3,4)，是元组
```

#### 2.4 可变关键字参数 `**kwargs`

```python
def print_config(**kwargs):
    for k, v in kwargs.items():
        print(f"{k} = {v}")
print_config(host="localhost", port=8080)  # kwargs 是字典
```

#### 2.5 仅关键字参数（Keyword-only）

用 `*` 分隔，`*` 之后的参数必须用关键字传递：

```python
def create_user(name, *, age, email):
    ...
create_user("Tom", age=20, email="a@b.com")   # ✅
# create_user("Tom", 20, "a@b.com")          # ❌ age 必须关键字
```

#### 2.6 仅位置参数（Positional-only，3.8+）

用 `/` 分隔，`/` 之前的参数只能用位置传递：

```python
def f(a, b, /, c):
    ...
f(1, 2, 3)        # ✅ a, b 位置传
f(1, 2, c=3)      # ✅ c 关键字传
# f(1, b=2, c=3)  # ❌ b 不能用关键字
```

#### 2.7 参数组合顺序

完整顺序为：**positional-only / 普通 / *args / keyword-only / **kwargs**

```python
def f(a, b, /, c, d=10, *args, e, f=20, **kwargs):
    # a, b: 仅位置
    # c, d: 普通（可位置可关键字）
    # args: 可变位置
    # e, f: 仅关键字
    # kwargs: 可变关键字
    ...
```

---

### 三、返回值

```python
# 单返回值
def square(x):
    return x * x

# 多返回值（本质返回元组）
def min_max(lst):
    return min(lst), max(lst)      # 等价 return (min, max)

lo, hi = min_max([3, 1, 4, 1, 5])

# 无 return 或 return None
def log(msg):
    print(msg)
    # 隐式 return None

# yield：生成器（Day11 详讲）
def counter():
    yield 1
    yield 2
```

---

### 四、函数是一等公民

Python 中函数是对象，可以：

```python
# 1. 赋值给变量
f = len
f([1, 2, 3])          # 3

# 2. 作为参数传递
sorted(["banana", "apple", "cherry"], key=len)

# 3. 作为返回值
def make_multiplier(n):
    return lambda x: x * n
double = make_multiplier(2)

# 4. 存入数据结构
ops = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
}
ops["add"](3, 4)      # 7
```

---

### 五、Lambda 匿名函数

```python
lambda params: expression
```

- 单表达式，不能包含语句（不能有 `if` 块、`for` 等）
- 适合简短的、一次性的函数

```python
# 排序 key
sorted(products, key=lambda p: p["price"])

# map / filter
list(map(lambda x: x**2, [1, 2, 3]))       # [1, 4, 9]
list(filter(lambda x: x > 0, [-1, 2, -3, 4]))  # [2, 4]
```

> **局限**：复杂逻辑应使用 `def`，Lambda 难以阅读和调试。

---

### 六、高阶函数

#### 6.1 map(func, iterable)

对每个元素应用函数，返回迭代器：

```python
list(map(str, [1, 2, 3]))     # ['1', '2', '3']
list(map(lambda x: x**2, range(5)))  # [0, 1, 4, 9, 16]
```

#### 6.2 filter(func, iterable)

过滤元素，保留返回 True 的：

```python
list(filter(lambda x: x % 2 == 0, range(10)))  # [0, 2, 4, 6, 8]
```

#### 6.3 functools.reduce(func, iterable, initial)

累积运算：

```python
from functools import reduce
reduce(lambda a, b: a + b, [1, 2, 3, 4])    # 10
reduce(lambda a, b: a * b, [1, 2, 3, 4])    # 24
```

#### 6.4 sorted(iterable, key=, reverse=)

```python
sorted([3, 1, 4, 1, 5])                      # [1, 1, 3, 4, 5]
sorted([3, 1, 4, 1, 5], reverse=True)       # [5, 4, 3, 1, 1]
sorted(products, key=lambda p: p["price"])  # 按价格升序
```

#### 6.5 any() / all()

```python
any([False, True, False])    # True，任一为真
all([True, True, False])     # False，全部为真
```

> **Pythonic 提示**：能用列表推导式就别用 `map`/`filter`，更易读：
> `[x**2 for x in range(5)]` 优于 `list(map(lambda x: x**2, range(5)))`

---

### 七、函数注解（type hints 初探）

```python
def add(a: int, b: int) -> int:
    return a + b
```

- 注解**不强制**运行时类型检查，仅作为提示和文档
- 配合 `mypy` 工具可做静态类型检查（Day14 详讲）

---

### 八、递归

函数调用自身：

```python
def factorial(n):
    if n <= 1:          # 基线条件
        return 1
    return n * factorial(n - 1)   # 递归调用
```

- 必须有**基线条件**（终止递归）
- Python 默认递归深度限制 1000，可用 `sys.setrecursionlimit()` 调整
- 递归通常比循环慢且有栈溢出风险，但某些问题（树遍历、分治）天然递归

---

### 九、闭包

#### 9.1 概念

内部函数引用了外部函数的变量，且外部函数已返回，这些变量仍被"记住"：

```python
def make_counter():
    count = 0
    def inner():
        nonlocal count     # 声明修改外层变量
        count += 1
        return count
    return inner

c = make_counter()
c()    # 1
c()    # 2
c()    # 3
```

#### 9.2 工厂函数

```python
def make_multiplier(n):
    def multiply(x):
        return x * n      # n 来自外层
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
double(5)    # 10
triple(5)    # 15
```

#### 9.3 nonlocal 关键字

内部函数想**修改**（而非只读）外层函数的变量，必须用 `nonlocal` 声明，否则 Python 会把它当作局部变量。

---

### 十、作用域 LEGB 规则

Python 查找变量的顺序：

| 层级 | 含义 | 示例 |
|------|------|------|
| **L** Local | 函数内局部 | 函数体内定义的变量 |
| **E** Enclosing | 外层嵌套函数 | 闭包中的外层变量 |
| **G** Global | 模块全局 | 模块顶层定义的变量 |
| **B** Built-in | 内置 | `len`, `print`, `range` |

```python
x = "global"            # G
def outer():
    x = "enclosing"     # E
    def inner():
        x = "local"     # L
        print(x)
    inner()
outer()                 # local
```

#### global / nonlocal

```python
counter = 0
def increment():
    global counter      # 声明使用全局变量
    counter += 1
```

---

### 十一、函数文档 docstring

```python
def calc_total(price, qty):
    """计算订单总价。

    Google 风格 docstring 示例。

    Args:
        price: 单价
        qty: 数量

    Returns:
        总价
    """
    return price * qty

print(calc_total.__doc__)    # 查看文档
help(calc_total)             # 交互式查看
```

---

### 十二、内置函数精选

| 函数 | 作用 | 示例 |
|------|------|------|
| `print` | 打印 | `print("hi")` |
| `len` | 长度 | `len([1,2,3])` |
| `range` | 整数序列 | `range(5)` |
| `sum` | 求和 | `sum([1,2,3])` |
| `max` / `min` | 最值 | `max([1,2,3])` |
| `sorted` | 排序 | `sorted([3,1,2])` |
| `reversed` | 反转 | `list(reversed([1,2,3]))` |
| `enumerate` | 带索引遍历 | `for i, v in enumerate(lst)` |
| `zip` | 并行遍历 | `zip([1,2], ['a','b'])` |
| `abs` / `round` | 绝对值 / 四舍五入 | `round(3.14, 1)` |
| `type` / `isinstance` | 类型检查 | `isinstance(x, int)` |
| `id` / `dir` / `vars` | 身份 / 属性 / 实例字典 | `id(obj)` |

---

## 代码文件说明

| 文件 | 内容 | 电商场景 |
|------|------|---------|
| `Code/functions.py` | 函数定义/调用/返回值/默认参数/类型注解/docstring | 计算订单总价、折扣计算、格式化商品信息 |
| `Code/args_kwargs.py` | `*args`/`**kwargs`/仅关键字/仅位置参数/参数组合 | 灵活日志函数、配置合并函数 |
| `Code/lambda_higher_order.py` | Lambda、map/filter/reduce/sorted with key | 商品排序、提取商品名、过滤库存、总库存计算 |
| `Code/closures.py` | 闭包、工厂函数、计数器、nonlocal | 折扣计算器、带状态限流器 |

运行方式：

```bash
cd "Python/Day06 - 函数与Lambda/Code"
python functions.py
python args_kwargs.py
python lambda_higher_order.py
python closures.py
```

---

## 关键知识点总结

### 参数类型速查表

| 参数形式 | 语法 | 调用方式 | 收集类型 |
|---------|------|---------|---------|
| 位置参数 | `def f(a, b)` | `f(1, 2)` | — |
| 默认参数 | `def f(a, b=10)` | `f(1)` 或 `f(1, 20)` | — |
| 可变位置 | `def f(*args)` | `f(1, 2, 3)` | tuple |
| 可变关键字 | `def f(**kwargs)` | `f(a=1, b=2)` | dict |
| 仅关键字 | `def f(a, *, b)` | `f(1, b=2)` | — |
| 仅位置 | `def f(a, /, b)` | `f(1, 2)` | — |

### 高阶函数速查

| 函数 | 作用 | 返回 | 等价推导式 |
|------|------|------|-----------|
| `map(f, it)` | 对每个元素应用 f | 迭代器 | `[f(x) for x in it]` |
| `filter(f, it)` | 保留 f(x) 为真的 | 迭代器 | `[x for x in it if f(x)]` |
| `reduce(f, it)` | 累积运算 | 单值 | 无（用循环） |
| `sorted(it, key=)` | 排序 | 新列表 | — |
| `any(it)` | 任一为真 | bool | — |
| `all(it)` | 全部为真 | bool | — |

### 闭包原理图

```
def make_counter():        外层函数
    count = 0              ┐
    def inner():           │  inner 闭包"捕获" count
        nonlocal count     │  即使 make_counter 返回
        count += 1         │  count 仍存活在 inner 中
        return count       ┘
    return inner

c = make_counter()         c 是 inner 函数
c()  # 1                  每次调用修改被捕获的 count
c()  # 2
```

### 作用域 LEGB 规则

```
查找顺序（从内到外）：
  L (Local)           函数内局部变量
  E (Enclosing)       外层嵌套函数变量
  G (Global)          模块级全局变量
  B (Built-in)        内置函数/常量

修改规则：
  修改全局变量  → global x
  修改外层变量  → nonlocal x
```

---

## 实战练习

### 练习 1：灵活的订单计算函数

写一个函数 `calc_order_total(items, discount=0.0, tax_rate=0.0, **fees)`，`items` 是 `[(price, qty), ...]`，支持：
- `discount`：折扣率（0.0-1.0）
- `tax_rate`：税率
- `**fees`：附加费用（如 shipping=20, packaging=5）

返回最终总价。要求：用 docstring 写文档，用类型注解标注参数。

### 练习 2：商品数据处理流水线

给定商品列表 `products`，用 `map` / `filter` / `sorted`（也可用列表推导式）完成：
1. 过滤出库存 > 0 的商品
2. 对每个商品应用 9 折
3. 按价格升序排序
4. 提取商品名列表

### 练习 3：带状态的限流器闭包

写一个闭包 `make_rate_limiter(max_calls, window_seconds)`，返回一个函数 `allow()`：
- 在 `window_seconds` 时间窗口内最多允许 `max_calls` 次调用
- 超出返回 `False`，未超出返回 `True` 并记录本次调用时间
- 提示：用 `time.time()` 获取当前时间，用列表存储调用时间戳

---

**下一章预告**：Day07 进入面向对象编程（OOP），学习如何用类和对象组织代码结构，理解 `self`、继承、`@property` 等核心概念。
