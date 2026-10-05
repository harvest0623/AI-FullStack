# Day05 - 元组、字典与集合

> Python 内置数据结构的重要补充：元组、字典与集合各有独特用途，理解它们的选择与组合是写出 Pythonic 代码的关键一步。

列表（list）解决了"有序可变"的需求，但现实世界中数据形态远不止于此：商品记录往往不可变、购物车需要键值对映射、用户标签需要去重与集合运算。元组（tuple）、字典（dict）和集合（set）正是 Python 对这三类需求给出的答案。本章在列表的基础上，补齐 Python 四大内置容器，并通过电商场景演示它们各自的不可替代性。

---

## 学习目标

- 掌握元组的创建、不可变性、解包语法与 namedtuple 的使用场景
- 掌握字典的增删改查、遍历、推导式与 `collections` 模块（defaultdict / OrderedDict / Counter）
- 掌握集合的运算（交集、并集、差集、对称差集）与 frozenset 的应用
- 理解四种数据结构（list / tuple / dict / set）的差异，能根据场景做出合理选型
- 能够用电商数据模型（Product / Order / Customer）完成真实的数据处理任务

---

## 理论知识讲解

### 一、元组 tuple

#### 1.1 创建元组

元组是有序、不可变的容器，用圆括号 `()` 表示：

```python
# 空元组
t1 = ()
t2 = tuple()

# 多元素元组
t3 = (1, 2, 3)
t4 = 1, 2, 3          # 括号可省略

# 单元素元组——必须带逗号！
t5 = (1,)             # 正确，单元素元组
t6 = (1)              # 错误！这只是整数 1，不是元组
```

> ⚠️ **常见陷阱**：单元素元组必须带逗号 `(1,)`，写成 `(1)` 会被当作普通表达式。

#### 1.2 不可变性

元组本身不可变，不能增删改元素：

```python
t = (1, 2, 3)
# t[0] = 10          # TypeError: 'tuple' object does not support item assignment
# t.append(4)        # AttributeError
```

但元组内的元素若是可变对象，则该对象自身仍可修改——不可变的是元组对元素的引用，不是元素本身：

```python
t = ([1, 2], [3, 4])
t[0].append(99)       # 合法，t 变为 ([1, 2, 99], [3, 4])
```

#### 1.3 索引与切片

元组的索引和切片与列表完全一致：

```python
t = ('a', 'b', 'c', 'd', 'e')
t[0]                  # 'a'
t[-1]                 # 'e'
t[1:4]                # ('b', 'c', 'd')
t[::-1]               # ('e', 'd', 'c', 'b', 'a')
```

#### 1.4 打包与解包

```python
# 打包：多个值赋给一个元组
point = (3, 4)

# 解包：元组拆给多个变量
x, y = point

# 扩展解包：用 * 收集剩余元素
a, *rest = (1, 2, 3, 4)       # a=1, rest=[2, 3, 4]
first, *middle, last = (1, 2, 3, 4, 5)  # first=1, middle=[2,3,4], last=5
```

#### 1.5 namedtuple 命名元组

普通元组只能用下标访问，可读性差。`collections.namedtuple` 让字段有名字：

```python
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])
p = Point(3, 4)
p.x          # 3，比 p[0] 更清晰
p.y          # 4
p._asdict()  # {'x': 3, 'y': 4}
```

#### 1.6 元组 vs 列表

| 特性 | 列表 list | 元组 tuple |
|------|----------|-----------|
| 可变性 | 可变 | 不可变 |
| 可哈希 | 否 | 是（元素均不可变时） |
| 作字典键 | ❌ | ✅ |
| 创建开销 | 略大 | 略小 |
| 内存占用 | 略大 | 略小 |
| 语义 | 同质、可变序列 | 异质记录、不可变序列 |

**何时用元组**：函数多返回值、固定结构的记录（如坐标、RGB）、作字典键、不可变配置。

---

### 二、字典 dict

#### 2.1 创建字典

```python
# 空字典
d1 = {}
d2 = dict()

# 字面量
d3 = {'a': 1, 'b': 2}

# dict() 关键字参数
d4 = dict(a=1, b=2)

# 可迭代对
d5 = dict([('a', 1), ('b', 2)])

# 字典推导式
pairs = [('a', 1), ('b', 2)]
d6 = {k: v for k, v in pairs}
```

#### 2.2 增删改查

```python
d = {'name': 'iPhone', 'price': 5999}

# 增 / 改
d['stock'] = 100            # 新增
d['price'] = 5499           # 修改

# 查
d['name']                   # 不存在会 KeyError
d.get('color', 'unknown')   # 不存在返回默认值，不报错

# 删
del d['stock']              # 删除键
d.pop('color', None)        # 删除并返回值，不存在返回默认
d.popitem()                 # 删除并返回最后插入的键值对（3.7+）

# 安全新增
d.setdefault('color', 'black')  # 键存在则返回原值，不存在则设置并返回
```

#### 2.3 遍历字典

```python
d = {'a': 1, 'b': 2, 'c': 3}

for key in d.keys():        # 只遍历键
    ...
for value in d.values():    # 只遍历值
    ...
for k, v in d.items():      # 同时遍历键值（最常用）
    ...
```

#### 2.4 合并字典

```python
d1 = {'a': 1, 'b': 2}
d2 = {'b': 3, 'c': 4}

# update：原地修改
d1.update(d2)               # d1 变为 {'a':1, 'b':3, 'c':4}

# 解包合并（3.5+）：生成新字典
merged = {**d1, **d2}

# | 运算符（3.9+）：生成新字典
merged = d1 | d2
```

#### 2.5 字典推导式

```python
# 过滤
prices = {'a': 10, 'b': 50, 'c': 100}
expensive = {k: v for k, v in prices.items() if v > 30}

# 转换
squares = {x: x**2 for x in range(5)}
```

#### 2.6 有序性（3.7+）

Python 3.7 起，普通字典保证**插入顺序**（3.6 是实现细节，3.7 成为语言规范）：

```python
d = {}
d['z'] = 1
d['a'] = 2
d['m'] = 3
list(d.keys())              # ['z', 'a', 'm']，保持插入顺序
```

#### 2.7 嵌套字典

```python
shop = {
    'beijing': {'staff': 10, 'sales': 50000},
    'shanghai': {'staff': 8, 'sales': 60000},
}
shop['beijing']['sales']    # 50000
```

#### 2.8 collections 模块

**defaultdict**：访问不存在的键时自动创建默认值，避免 KeyError：

```python
from collections import defaultdict

# 按分类分组
groups = defaultdict(list)
for product in products:
    groups[product['category']].append(product)

# 计数
counts = defaultdict(int)
for word in words:
    counts[word] += 1
```

**OrderedDict**：3.7 后普通 dict 已有序，但 OrderedDict 仍有独有功能：

```python
from collections import OrderedDict

od = OrderedDict()
od['a'] = 1
od['b'] = 2
od.move_to_end('a')         # 把 a 移到末尾
od.popitem(last=False)      # 弹出最先插入的（FIFO 队列语义）
```

**Counter**：计数器专用的字典子类：

```python
from collections import Counter

c = Counter(['a', 'b', 'a', 'c', 'a', 'b'])
c['a']                      # 3
c.most_common(2)            # [('a', 3), ('b', 2)]
c.update(['a', 'd'])        # 增量计数
```

---

### 三、集合 set

#### 3.1 创建集合

```python
# 多元素集合
s1 = {1, 2, 3}

# 空集合——必须用 set()！
s2 = set()                  # 正确
s3 = {}                     # ❌ 这是空字典，不是空集合！

# 从可迭代对象创建
s4 = set([1, 2, 2, 3])      # {1, 2, 3}，自动去重
s5 = set('hello')           # {'h', 'e', 'l', 'o'}
```

> ⚠️ **常见陷阱**：`{}` 是空字典，空集合必须用 `set()`。

#### 3.2 增删元素

```python
s = {1, 2, 3}

s.add(4)                    # 添加
s.remove(2)                 # 删除，不存在会 KeyError
s.discard(99)               # 删除，不存在不报错（推荐）
removed = s.pop()           # 随机弹出一个元素
s.clear()                   # 清空
```

#### 3.3 集合运算

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a & b                       # 交集 {3, 4}        等价 a.intersection(b)
a | b                       # 并集 {1,2,3,4,5,6} 等价 a.union(b)
a - b                       # 差集 {1, 2}        等价 a.difference(b)
a ^ b                       # 对称差集 {1, 2, 5, 6} 等价 a.symmetric_difference(b)
```

#### 3.4 子集与超集

```python
{1, 2} <= {1, 2, 3}         # True，子集
{1, 2} <  {1, 2, 3}         # True，真子集
{1, 2, 3} >= {1, 2}         # True，超集
{1, 2, 3} >  {1, 2}         # True，真超集
{1, 2, 3}.issubset({1,2,3}) # True，方法形式
```

#### 3.5 集合推导式

```python
{x**2 for x in range(-3, 4)}    # {0, 1, 4, 9}
{x % 3 for x in [1, 2, 4, 5, 7]}  # {0, 1, 2}
```

#### 3.6 frozenset 不可变集合

```python
fs = frozenset([1, 2, 3])
# fs.add(4)                 # AttributeError，不可变
hash(fs)                    # 可哈希，可作字典键
d = {frozenset(['a','b']): 'ab 组'}
```

#### 3.7 集合的应用场景

- **去重**：`list(set([1, 1, 2, 2, 3]))`
- **成员判断**：集合 `in` 操作 O(1)，列表 O(n)
- **集合运算**：共同标签、差集找未参与用户

---

### 四、数据结构选择指南

| 数据结构 | 有序 | 可变 | 重复 | 典型场景 |
|---------|------|------|------|---------|
| 列表 list | ✅ | ✅ | ✅ | 有序序列、可增删 |
| 元组 tuple | ✅ | ❌ | ✅ | 不可变记录、函数多返回值 |
| 字典 dict | ✅(3.7+) | ✅ | 键不可 | 键值映射、查找表 |
| 集合 set | ❌ | ✅ | ❌ | 去重、成员判断、集合运算 |

**选型决策**：
1. 需要"键 → 值"映射？→ **dict**
2. 需要去重或集合运算？→ **set**
3. 数据不可变（作字典键、配置、多返回值）？→ **tuple**
4. 否则用最通用的 **list**

---

## 代码文件说明

| 文件 | 内容 | 电商场景 |
|------|------|---------|
| `Code/tuples.py` | 元组创建/索引/解包/namedtuple | 商品记录存储、函数多返回值、坐标 namedtuple |
| `Code/dictionaries.py` | 字典增删改查/遍历/推导式/defaultdict/Counter/嵌套 | 商品分类映射、购物车、订单状态统计、按分类分组 |
| `Code/sets.py` | 集合创建/增删/运算/推导式/frozenset/去重 | 用户标签运算、共同购买商品、未下单用户差集 |
| `Code/data_structures_comparison.py` | 四种结构对比、性能对比、选型演示 | 同一问题的不同实现对比 |

运行方式：

```bash
cd "Python/Day05 - 元组、字典与集合/Code"
python tuples.py
python dictionaries.py
python sets.py
python data_structures_comparison.py
```

---

## 关键知识点总结

### 四种数据结构对比表

| 结构 | 语法 | 可变性 | 有序性 | 重复 | 哈希性 | 查找复杂度 |
|------|------|--------|--------|------|--------|-----------|
| list | `[]` | 可变 | 有序 | 允许 | 不可哈希 | O(n) |
| tuple | `()` | 不可变 | 有序 | 允许 | 元素不可变时可哈希 | O(n) |
| dict | `{k:v}` | 可变 | 插入序(3.7+) | 键不可 | 键不可变时可哈希 | O(1) |
| set | `{x}` | 可变 | 无序 | 不允许 | 不可哈希 | O(1) |
| frozenset | `frozenset()` | 不可变 | 无序 | 不允许 | 可哈希 | O(1) |

### 字典方法速查

| 方法 | 作用 | 不存在时的行为 |
|------|------|--------------|
| `d[k]` | 取值 | KeyError |
| `d.get(k, default)` | 取值 | 返回 default（默认 None） |
| `d[k] = v` | 设置 | 新增或覆盖 |
| `d.setdefault(k, default)` | 取值并设置 | 返回 default 并写入 |
| `d.pop(k, default)` | 删除并返回 | 返回 default |
| `d.popitem()` | 弹出末尾项 | KeyError（空字典时） |
| `d.update(other)` | 批量合并 | — |
| `d.keys()` / `values()` / `items()` | 视图遍历 | — |
| `{**d1, **d2}` | 解包合并 | — |
| `d1 \| d2` (3.9+) | 合并 | — |

### 集合运算速查

| 运算符 | 方法 | 含义 |
|--------|------|------|
| `a & b` | `a.intersection(b)` | 交集 |
| `a \| b` | `a.union(b)` | 并集 |
| `a - b` | `a.difference(b)` | 差集 |
| `a ^ b` | `a.symmetric_difference(b)` | 对称差集 |
| `a <= b` | `a.issubset(b)` | 子集 |
| `a >= b` | `a.issuperset(b)` | 超集 |
| `a < b` | — | 真子集 |
| `a > b` | — | 真超集 |

### collections 模块速查

| 类型 | 用途 | 关键方法/特性 |
|------|------|--------------|
| `defaultdict` | 带默认值的字典 | `defaultdict(list)` / `defaultdict(int)` |
| `OrderedDict` | 有序字典 | `move_to_end()` / `popitem(last=)` |
| `Counter` | 计数字典 | `most_common(n)` / `update()` / `+` `-` |
| `namedtuple` | 命名元组 | 字段名访问 / `_asdict()` / `_replace()` |
| `deque` | 双端队列 | `appendleft()` / `popleft()` O(1) |

---

## 实战练习

### 练习 1：购物车统计器

给定购物车数据 `cart = {'p001': 2, 'p002': 1, 'p003': 5}` 和商品价格表 `prices = {'p001': 99, 'p002': 199, 'p003': 49}`，用字典推导式计算购物车总价，并用 `defaultdict` 按商品价格区间（0-50 / 51-100 / 100+）分组。

### 练习 2：用户兴趣分析

两个用户分别有以下购买过的商品 ID 集合：
```python
user_a = {101, 102, 103, 105, 107}
user_b = {102, 104, 105, 106, 108}
```
用集合运算求：① 两人共同购买的商品；② 各自独有购买的商品；③ 推荐给对方的商品（对方没买过）。

### 练习 3：订单状态分布

给定一个订单列表，每个订单是元组 `(order_id, status)`，`status` 取值为 `'paid' / 'shipped' / 'done' / 'cancelled'`。用 `Counter` 统计各状态订单数量并按数量降序输出前三名。

---

**下一章预告**：Day06 将进入函数与 Lambda，学习如何把重复逻辑封装成可复用的函数，并理解 Python 函数作为"一等公民"的灵活用法。
