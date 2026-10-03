# Day04 - 字符串与列表

字符串和列表是 Python 最常用的数据结构，掌握它们是高效编程的前提。字符串承载了电商系统中的商品名称、订单号、用户输入等所有文本信息；列表则是有序数据的容器，购物车、商品清单、订单明细都离不开它。本章将系统讲解字符串的创建、切片、格式化与方法，以及列表的增删改查、推导式、拷贝机制，并通过 `eshop` 场景演示如何格式化商品信息、解析 CSV 数据、操作购物车等实际任务。

## 学习目标

- 掌握字符串的多种创建方式与不可变性
- 熟练使用索引与切片，包括反转与步长
- 掌握三种字符串格式化方式，重点掌握 f-string
- 熟练使用字符串常用方法（大小写、查找、替换、分割、对齐）
- 理解 `encode`/`decode` 与 UTF-8 编码
- 掌握列表的增删改查与排序
- 熟练使用列表推导式，理解浅拷贝与深拷贝的区别

## 理论知识讲解

### 一、字符串

#### 1. 字符串创建

```python
s1 = 'hello'           # 单引号
s2 = "hello"           # 双引号（与单引号等价）
s3 = """多行
字符串"""              # 三引号（可跨行）
s4 = r"C:\new\folder"  # 原始字符串（反斜杠不转义）
```

#### 2. 字符串不可变性

字符串是**不可变**对象，任何"修改"操作都会创建新字符串：

```python
s = "eshop"
# s[0] = "E"   # 报错：str 不支持项赋值
s = "E" + s[1:] # 创建新字符串 "Eshop"
```

#### 3. 索引与切片

```python
s = "eshop-cli"
s[0]       # 'e'（正索引从 0 开始）
s[-1]      # 'i'（负索引从末尾开始）
s[1:4]     # 'sho'（左闭右开）
s[:5]      # 'eshop'（从头到索引5前）
s[6:]      # 'cli'（从索引6到末尾）
s[::2]     # 'eh-ci'（步长2）
s[::-1]    # 'ilc-pohse'（反转字符串）
```

切片语法：`s[start:stop:step]`，左闭右开。

#### 4. 字符串格式化

| 方式 | 语法 | 推荐度 | 示例 |
| --- | --- | --- | --- |
| % 格式化（旧） | `"%.2f" % price` | 不推荐 | `"价格: %.2f" % 99.5` |
| str.format() | `"{:.2f}".format(x)` | 一般 | `"价格: {:.2f}".format(99.5)` |
| f-string（3.6+） | `f"{x:.2f}"` | **推荐** | `f"价格: {99.5:.2f}"` |

f-string 高级用法：

```python
name = "iPhone"
price = 5999
rate = 0.85

f"{name} 价格 {price}"            # 普通插值
f"{name=}"                         # 调试：输出 name='iPhone'
f"{price:>10}"                     # 右对齐，宽10
f"{price:<10}"                     # 左对齐
f"{price:^10}"                     # 居中
f"{price:,.2f}"                    # 千分位：5,999.00
f"{rate:.2%}"                      # 百分比：85.00%
f"{price:010d}"                    # 零填充：0000005999
```

#### 5. 常用方法

**大小写转换**：

| 方法 | 作用 | 示例 |
| --- | --- | --- |
| `upper()` | 全大写 | `"abc".upper()` → `"ABC"` |
| `lower()` | 全小写 | `"ABC".lower()` → `"abc"` |
| `title()` | 每词首字母大写 | `"hello world".title()` → `"Hello World"` |
| `capitalize()` | 首字母大写 | `"hello".capitalize()` → `"Hello"` |
| `swapcase()` | 大小写互换 | `"AbC".swapcase()` → `"aBc"` |

**查找**：

| 方法 | 作用 | 找不到返回 |
| --- | --- | --- |
| `find(sub)` | 从左查找子串位置 | `-1` |
| `rfind(sub)` | 从右查找 | `-1` |
| `index(sub)` | 同 find | **抛 ValueError** |
| `count(sub)` | 统计出现次数 | `0` |

**判断**：

| 方法 | 作用 |
| --- | --- |
| `startswith(prefix)` | 是否以指定前缀开头 |
| `endswith(suffix)` | 是否以指定后缀结尾 |
| `isdigit()` | 是否全是数字 |
| `isalpha()` | 是否全是字母 |
| `isalnum()` | 是否全是字母或数字 |
| `isspace()` | 是否全是空白 |

**替换与分割**：

| 方法 | 作用 | 示例 |
| --- | --- | --- |
| `replace(old, new)` | 替换 | `"a-b".replace("-", "_")` → `"a_b"` |
| `split(sep)` | 分割成列表 | `"a,b,c".split(",")` → `['a','b','c']` |
| `rsplit(sep, max)` | 从右分割 | `"a.b.c".rsplit(".", 1)` → `['a.b','c']` |
| `partition(sep)` | 分成三段 | `"a=b".partition("=")` → `('a','=','b')` |
| `join(iterable)` | 用本串连接列表 | `"-".join(["a","b"])` → `"a-b"` |

**去空白**：

| 方法 | 作用 |
| --- | --- |
| `strip()` | 去除两端空白（含 `\t\n`） |
| `lstrip()` | 去除左端 |
| `rstrip()` | 去除右端 |
| `strip(chars)` | 去除两端指定字符 |

**对齐与填充**：

| 方法 | 作用 |
| --- | --- |
| `center(width)` | 居中 |
| `ljust(width)` | 左对齐 |
| `rjust(width)` | 右对齐 |
| `zfill(width)` | 左侧补零 |

#### 6. encode / decode

```python
s = "eshop 商城"
b = s.encode("utf-8")     # str -> bytes
print(b)                   # b'eshop \xe5\x95\x86\xe5\x9f\x8e'
s2 = b.decode("utf-8")    # bytes -> str
print(s2 == s)             # True
```

#### 7. 正则表达式预览

```python
import re

re.match(r"\d+", "123abc")     # 从开头匹配
re.search(r"\d+", "abc123")    # 搜索任意位置
re.findall(r"\d+", "a1b2c3")   # 找出所有 ['1','2','3']
re.sub(r"\d", "#", "a1b2")     # 替换 'a#b#'
re.split(r"[,;]", "a,b;c")     # 按模式分割
```

正则将在后续章节深入。

### 二、列表

#### 1. 列表创建

```python
empty = []
nums = [1, 2, 3]
mixed = [1, "a", True, None]
from_range = list(range(5))           # [0, 1, 2, 3, 4]
comprehension = [x * 2 for x in range(5)]  # 列表推导式
```

#### 2. 索引与切片

与字符串完全一致：`lst[0]`、`lst[-1]`、`lst[1:4]`、`lst[::-1]`。

#### 3. 增

| 方法 | 作用 |
| --- | --- |
| `append(x)` | 末尾追加单个元素 |
| `extend(iter)` | 末尾追加多个元素 |
| `insert(i, x)` | 在索引 i 处插入 |

```python
cart = []
cart.append("iPhone")        # ['iPhone']
cart.extend(["MacBook", "iPad"])  # ['iPhone', 'MacBook', 'iPad']
cart.insert(0, "AirPods")    # ['AirPods', 'iPhone', 'MacBook', 'iPad']
```

#### 4. 删

| 方法/语句 | 作用 |
| --- | --- |
| `remove(x)` | 删除第一个等于 x 的元素 |
| `pop(i)` | 弹出索引 i 的元素（默认末尾） |
| `del lst[i]` | 删除索引 i 的元素 |
| `clear()` | 清空列表 |

#### 5. 改

```python
lst = [1, 2, 3, 4]
lst[0] = 10              # [10, 2, 3, 4]
lst[1:3] = [20, 30, 40]  # [10, 20, 30, 40, 4]（切片替换）
```

#### 6. 查

| 操作 | 作用 |
| --- | --- |
| `in` | 判断元素是否存在 |
| `index(x)` | 返回第一个等于 x 的索引（找不到抛错） |
| `count(x)` | 统计 x 出现次数 |

#### 7. 排序

| 方法 | 作用 |
| --- | --- |
| `lst.sort()` | **原地**排序，返回 None |
| `sorted(lst)` | 返回**新列表**，不改原列表 |
| `lst.reverse()` | 原地反转 |

```python
products = [{"price": 5999}, {"price": 1999}, {"price": 999}]
# 按 price 升序
products.sort(key=lambda p: p["price"])
# 降序
products.sort(key=lambda p: p["price"], reverse=True)
```

#### 8. 列表推导式

```python
# 基本形式
[expr for item in iterable]

# 带条件
[expr for item in iterable if condition]

# 嵌套
[expr for row in matrix for item in row]
```

#### 9. 嵌套列表（矩阵）

```python
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
print(matrix[1][2])   # 6（第2行第3列）
```

#### 10. 列表复制：浅拷贝 vs 深拷贝

| 方式 | 类型 | 说明 |
| --- | --- | --- |
| `lst2 = lst1` | 引用 | 完全同一对象，改一改全改 |
| `lst.copy()` / `lst[:]` / `copy.copy()` | 浅拷贝 | 新列表，但内部元素仍是引用 |
| `copy.deepcopy(lst)` | 深拷贝 | 递归复制所有层级 |

```python
import copy
a = [[1, 2], [3, 4]]
b = a.copy()              # 浅拷贝
b[0][0] = 99              # 改了内部列表，a 也跟着变！
c = copy.deepcopy(a)      # 深拷贝，完全独立
```

#### 11. 列表解包

```python
first, *rest = [1, 2, 3, 4]    # first=1, rest=[2,3,4]
first, *mid, last = [1, 2, 3, 4]  # first=1, mid=[2,3], last=4
```

#### 12. 常用内置函数

| 函数 | 作用 |
| --- | --- |
| `len(lst)` | 长度 |
| `max(lst)` | 最大值 |
| `min(lst)` | 最小值 |
| `sum(lst)` | 求和 |
| `any(lst)` | 是否有 Truthy 元素 |
| `all(lst)` | 是否全部 Truthy |

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/strings.py` | 字符串操作练习，演示创建/索引/切片/反转、格式化三种方式对比、encode/decode，用电商场景格式化商品信息 |
| `Code/string_methods.py` | 字符串方法练习，演示大小写/查找/判断/替换/分割/去空白/对齐填充，用电商场景解析 CSV、格式化报告、验证邮箱 |
| `Code/lists.py` | 列表操作练习，演示增删改查/排序/反转、嵌套列表、浅拷贝 vs 深拷贝、列表解包，用电商场景操作购物车 |
| `Code/list_comprehension.py` | 列表推导式练习，演示基本推导式/条件过滤/嵌套/矩阵展平，对比 for 循环写法，用电商场景提取商品数据 |

## 关键知识点总结

### 字符串方法速查表

| 类别 | 方法 |
| --- | --- |
| 大小写 | `upper` `lower` `title` `capitalize` `swapcase` |
| 查找 | `find` `rfind` `index` `rindex` `count` |
| 判断 | `startswith` `endswith` `isdigit` `isalpha` `isalnum` `isspace` |
| 替换分割 | `replace` `split` `rsplit` `partition` `join` |
| 去空白 | `strip` `lstrip` `rstrip` |
| 对齐填充 | `center` `ljust` `rjust` `zfill` |

### f-string 格式化速查

| 写法 | 含义 |
| --- | --- |
| `{x}` | 直接插入 |
| `{x:.2f}` | 保留2位小数 |
| `{x:,}` | 千分位 |
| `{x:.2%}` | 百分比 |
| `{x:>10}` | 右对齐宽10 |
| `{x:<10}` | 左对齐宽10 |
| `{x:^10}` | 居中宽10 |
| `{x:0>5}` | 左补零到5位 |
| `{x=}` | 调试输出变量名与值 |

### 列表方法速查表

| 类别 | 方法 |
| --- | --- |
| 增 | `append` `extend` `insert` |
| 删 | `remove` `pop` `del` `clear` |
| 查 | `in` `index` `count` |
| 排序 | `sort` `sorted` `reverse` |
| 复制 | `copy` `deepcopy` |

### 浅拷贝 vs 深拷贝对比表

| 对比项 | 浅拷贝 | 深拷贝 |
| --- | --- | --- |
| 外层列表 | 新对象 | 新对象 |
| 内层元素 | 共享引用 | 递归复制 |
| 改内层元素 | 影响原列表 | 不影响 |
| 用法 | `lst.copy()` / `lst[:]` | `copy.deepcopy(lst)` |

### 列表推导式语法图

```
[ 表达式  for  变量  in  可迭代对象  if  条件 ]
   ↑        ↑        ↑            ↑
  结果     循环     遍历         过滤（可选）
```

## 实战练习

### 练习 1：商品信息格式化

给定商品字典 `{"id": 1001, "name": "iPhone 15", "price": 5999, "stock": 50}`，用 f-string 输出如下格式：

```
商品编号 | 商品名称   | 单价(元) | 库存
0001     | iPhone 15  | 5,999.00 | 50
```

要求：编号补零到 4 位、名称左对齐宽 10、价格千分位保留 2 位小数。

### 练习 2：CSV 解析

给定字符串 `"1001,iPhone 15,5999,50"`，用 `split` 解析为商品信息，并完成：

1. 用 `strip` 去除可能的空白
2. 将价格和库存转为 `int`
3. 用 f-string 重新输出

### 练习 3：购物车操作

实现一个简单购物车：

1. 用列表存储商品名，支持 `append` 添加、`remove` 删除、`pop` 移除最后一个
2. 用列表推导式提取所有价格高于 3000 的商品名
3. 用 `sorted` 按名称排序并输出
