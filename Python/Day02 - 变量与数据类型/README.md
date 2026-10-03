# Day02 - 变量与数据类型

变量和数据类型是编程的基础。Python 采用动态类型系统，变量无需声明类型即可使用，这让代码编写既灵活又高效；但灵活性也意味着开发者必须清楚地知道每个变量当前持有的类型，否则容易在运算、传参时埋下隐患。本章围绕 `eshop` 电商场景中的商品与订单数据，系统讲解变量赋值、基本数据类型、类型转换、真值测试等内容，帮助你建立对 Python 类型系统的扎实理解。

## 学习目标

- 掌握变量赋值、命名规则与多变量赋值技巧
- 理解动态类型的本质，会用 `type()` 与 `id()` 观察变量
- 熟练使用 `int`、`float`、`bool`、`None` 等基本数据类型
- 理解浮点数精度陷阱，能用 `Decimal` 进行精确金额计算
- 掌握类型转换函数与转换规则
- 区分 `type()` 与 `isinstance()`，理解真值测试（Truthy/Falsy）
- 了解变量作用域 LEGB 规则的预备知识

## 理论知识讲解

### 1. 变量赋值

Python 中变量赋值的语法为 `name = value`，等号左边是变量名，右边是值。变量在赋值时被创建，无需提前声明。

#### 1.1 命名规则

- 只能包含**字母、数字、下划线**
- **不能以数字开头**
- **不能使用关键字**（如 `if`、`for`、`class`、`def`）
- 区分大小写（`Price` 与 `price` 是两个变量）
- 建议遵循 PEP 8：变量与函数用 `snake_case`，常量用 `UPPER_CASE`

```python
# 合法命名
product_id = 1001
product_name = "iPhone 15"
MAX_STOCK = 9999

# 非法命名（会报错）
# 1product = 100      # 不能数字开头
# product-price = 99  # 不能用连字符
# class = "电子产品"    # 不能用关键字
```

#### 1.2 多变量赋值

```python
# 多变量同时赋值（元组解包）
product_id, product_name, price = 1001, "iPhone 15", 5999

# 链式赋值（同一值赋给多个变量）
a = b = c = 0

# 变量交换（无需中间变量）
x, y = 1, 2
x, y = y, x   # 现在 x=2, y=1
```

### 2. 动态类型

Python 是动态类型语言，变量本身没有类型，**变量指向的对象才有类型**。同一个变量可以被重新赋值为任意类型。

```python
x = 10          # x 是 int
print(type(x))  # <class 'int'>

x = "eshop"     # 现在 x 是 str
print(type(x))  # <class 'str'>
```

- `type(obj)`：返回对象的类型
- `id(obj)`：返回对象在内存中的唯一标识（整数）

```python
a = 100
b = 100
print(id(a) == id(b))   # True（小整数缓存，-5~256 共享对象）
```

### 3. 基本数据类型

#### 3.1 int 整数

Python 的整数是**任意精度**的，没有溢出问题，可以表示非常大的数：

```python
big = 10 ** 100   # 10 的 100 次方，依然精确
print(big)
```

进制表示：

| 进制 | 前缀 | 示例 |
| --- | --- | --- |
| 十进制 | 无 | `255` |
| 二进制 | `0b` | `0b11111111`（=255） |
| 八进制 | `0o` | `0o377`（=255） |
| 十六进制 | `0x` | `0xff`（=255） |

下划线分隔（提升可读性，3.6+）：

```python
population = 1_000_000   # 等价于 1000000
price = 5_999.99
```

#### 3.2 float 浮点数

Python 的 `float` 基于 IEEE 754 双精度（64 位），存在经典的**浮点精度陷阱**：

```python
print(0.1 + 0.2)        # 0.30000000000000004
print(0.1 + 0.2 == 0.3) # False
```

**金额计算必须避免直接使用 float**。解决方案是 `decimal.Decimal`：

```python
from decimal import Decimal

# 用字符串初始化 Decimal，避免 float 精度问题
price = Decimal("0.1") + Decimal("0.2")
print(price)            # 0.3
print(price == Decimal("0.3"))  # True
```

`round(x, n)` 可四舍五入到 n 位小数，但仍不能根治 float 精度问题；判断浮点数是否相等应使用 `math.isclose`。

#### 3.3 bool 布尔

`bool` 只有两个值：`True` 与 `False`（首字母大写）。bool 是 int 的子类：

```python
print(True == 1)    # True
print(False == 0)   # True
print(True + True)  # 2
print(isinstance(True, int))  # True
```

#### 3.4 str 字符串

字符串用于表示文本，本节仅作预览，详见 Day04：

```python
name = "eshop"
greeting = f"欢迎来到 {name}"
```

#### 3.5 NoneType None

`None` 表示"空值"或"没有值"，它既不是 `0`，也不是空字符串 `""`。

```python
result = None
print(result is None)   # True，判断 None 必须用 is
print(result == None)   # 也能工作，但 PEP 8 推荐用 is
```

### 4. 类型转换

| 函数 | 作用 | 示例 |
| --- | --- | --- |
| `int(x)` | 转整数 | `int("123")` → `123`，`int(3.9)` → `3` |
| `float(x)` | 转浮点 | `float("3.14")` → `3.14` |
| `str(x)` | 转字符串 | `str(123)` → `"123"` |
| `bool(x)` | 转布尔 | `bool(0)` → `False`，`bool("")` → `False` |

转换规则要点：

- `int("abc")` 会抛出 `ValueError`，因为无法解析
- `int("123")` 成功，但 `int("12.3")` 失败（需先 `float` 再 `int`）
- `bool()` 对空容器、零值、`None` 返回 `False`，其余返回 `True`

### 5. type() vs isinstance()

| 对比项 | `type()` | `isinstance()` |
| --- | --- | --- |
| 匹配方式 | 精确匹配 | 考虑继承关系 |
| bool 是 int 子类 | `type(True) == int` 为 False | `isinstance(True, int)` 为 True |
| 推荐度 | 调试时用 | 业务代码推荐 |

```python
print(type(True) == int)        # False
print(isinstance(True, int))    # True
```

业务代码判断类型应优先使用 `isinstance()`，因为它能正确处理继承关系。

### 6. 真值测试（Truthy/Falsy）

在 `if`、`while`、`and`、`or` 等需要布尔值的语境中，Python 会自动对对象进行真值测试。

#### Falsy 值清单（判定为 False）

| 类型 | Falsy 值 |
| --- | --- |
| bool | `False` |
| int | `0` |
| float | `0.0` |
| str | `""`、`''` |
| list | `[]` |
| dict | `{}` |
| tuple | `()` |
| set | `set()` |
| NoneType | `None` |

其余所有值都是 **Truthy**（判定为 True）。

```python
if []:
    print("空列表是 Truthy")   # 不会执行
else:
    print("空列表是 Falsy")    # 会执行
```

### 7. 数字类型详解

#### 7.1 整数运算

| 运算符 | 含义 | 示例 |
| --- | --- | --- |
| `//` | 整除（向下取整） | `7 // 2` → `3` |
| `%` | 取余 | `7 % 2` → `1` |
| `**` | 幂运算 | `2 ** 10` → `1024` |
| `divmod(a, b)` | 同时返回商和余 | `divmod(7, 2)` → `(3, 1)` |
| `abs(x)` | 绝对值 | `abs(-5)` → `5` |
| `round(x, n)` | 四舍五入 | `round(3.1415, 2)` → `3.14` |

#### 7.2 浮点数陷阱与 Decimal

```python
# float 陷阱：金额累加可能出错
total = 0.1 + 0.1 + 0.1
print(total)              # 0.30000000000000004
print(total == 0.3)       # False

# Decimal 精确计算（用字符串初始化）
from decimal import Decimal
total = Decimal("0.1") + Decimal("0.1") + Decimal("0.1")
print(total)              # 0.3
```

#### 7.3 bool 是 int 子类

```python
print(True + True)        # 2
print(sum([True, False, True]))  # 2，可用于统计布尔列表
```

### 8. 变量作用域预告 LEGB

Python 查找变量时遵循 **LEGB** 规则（从内到外）：

- **L**ocal：函数内部局部作用域
- **E**nclosing：外层嵌套函数作用域
- **G**lobal：模块全局作用域
- **B**uilt-in：内置作用域（如 `print`、`len`）

```python
x = "global"        # G

def outer():
    x = "enclosing" # E
    def inner():
        x = "local" # L
        print(x)
    inner()

outer()   # 输出 local
```

作用域的详细内容将在函数章节展开。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/variables.py` | 变量赋值与命名规则练习，演示多变量赋值、变量交换、`type()`/`id()`、动态类型 |
| `Code/data_types.py` | 数据类型练习，演示 int 任意精度、float 精度陷阱、bool 运算、None 判断，用电商商品价格演示 Decimal |
| `Code/type_conversion.py` | 类型转换练习，演示 `int/float/str/bool` 转换、`isinstance` vs `type`、Truthy/Falsy 测试，用电商数据演示类型转换 |

## 关键知识点总结

### 数据类型速查表

| 类型 | 关键字 | 示例 | 说明 |
| --- | --- | --- | --- |
| 整数 | int | `100`、`0xff`、`1_000` | 任意精度 |
| 浮点 | float | `3.14`、`1e5` | IEEE 754 双精度 |
| 布尔 | bool | `True`、`False` | int 子类 |
| 字符串 | str | `"eshop"` | 不可变 |
| 空值 | NoneType | `None` | 用 `is None` 判断 |

### 类型转换规则表

| 转换 | 示例 | 结果 | 说明 |
| --- | --- | --- | --- |
| str → int | `int("123")` | `123` | 必须是合法整数文本 |
| str → int | `int("12.3")` | 报错 | 需先 `float` |
| float → int | `int(3.9)` | `3` | 直接截断，不四舍五入 |
| int → float | `float(5)` | `5.0` | 自动加小数点 |
| int → str | `str(123)` | `"123"` | 任意类型可转 str |
| 任意 → bool | `bool(0)` | `False` | Falsy 值见上表 |

### Falsy 值清单

`False`、`0`、`0.0`、`""`、`''`、`[]`、`{}`、`()`、`set()`、`None`、`0j`、`b""`

## 实战练习

### 练习 1：商品价格计算

定义商品价格 `price = 19.99`，购买数量 `qty = 3`，分别用 `float` 和 `Decimal` 计算总价，对比两者结果是否完全相等，并说明原因。

### 练习 2：类型转换挑战

给定字符串 `s = "1024"`，依次完成：

1. 转为 int 并加 1
2. 转为 float 并除以 2
3. 转为 bool 并放入 `if` 判断
4. 思考：`bool("0")` 的结果是 True 还是 False？为什么？

### 练习 3：Truthy/Falsy 探索

对以下值分别用 `bool()` 转换并记录结果，总结规律：

`0`、`0.0`、`""`、`"0"`、`"False"`、`[]`、`[0]`、`None`、`-1`、`0.0001`
