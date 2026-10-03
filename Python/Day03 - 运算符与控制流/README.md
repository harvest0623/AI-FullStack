# Day03 - 运算符与控制流

运算符和控制流是编程逻辑的骨架。Python 提供了丰富的运算符（算术、比较、逻辑、位、成员、身份）和简洁强大的控制流语句（`if/elif/else`、`for`、`while`、`match-case`），配合 `break`、`continue`、`enumerate`、`zip` 等工具，可以优雅地表达几乎所有业务逻辑。本章将围绕 `eshop` 的订单状态处理、库存检查、商品遍历等场景，系统讲解运算符与控制流的用法，包括 Python 3.10+ 引入的 `match-case` 模式匹配。

## 学习目标

- 掌握各类运算符：算术、比较、逻辑、赋值、位、成员、身份
- 理解短路求值、海象运算符 `:=`、小整数缓存
- 熟练使用 `if/elif/else` 与三元运算符
- 掌握 `match-case` 模式匹配（3.10+）的多种用法
- 熟练使用 `for`、`while`、`break`、`continue`、`pass`
- 理解 `for-else` 与 `while-else` 的执行逻辑
- 掌握 `enumerate`、`zip` 等循环辅助工具

## 理论知识讲解

### 1. 算术运算符

| 运算符 | 含义 | 示例 | 结果 |
| --- | --- | --- | --- |
| `+` | 加 | `5 + 3` | `8` |
| `-` | 减 | `5 - 3` | `2` |
| `*` | 乘 | `5 * 3` | `15` |
| `/` | 除（真除法） | `7 / 2` | `3.5` |
| `//` | 整除（向下取整） | `7 // 2` | `3` |
| `%` | 取余 | `7 % 2` | `1` |
| `**` | 幂 | `2 ** 3` | `8` |

辅助函数：`divmod(a, b)` 返回 `(商, 余数)`，`abs(x)` 绝对值，`round(x, n)` 四舍五入。

### 2. 比较运算符

| 运算符 | 含义 | 示例 |
| --- | --- | --- |
| `==` | 等于（比较值） | `5 == 5` → `True` |
| `!=` | 不等于 | `5 != 3` → `True` |
| `>` | 大于 | `5 > 3` → `True` |
| `<` | 小于 | `5 < 3` → `False` |
| `>=` | 大于等于 | `5 >= 5` → `True` |
| `<=` | 小于等于 | `5 <= 3` → `False` |

**链式比较**（Python 特色）：

```python
x = 5
# 等价于 1 < x and x < 10
print(1 < x < 10)   # True
```

### 3. 逻辑运算符

| 运算符 | 含义 | 示例 |
| --- | --- | --- |
| `and` | 与 | `True and False` → `False` |
| `or` | 或 | `True or False` → `True` |
| `not` | 非 | `not True` → `False` |

**短路求值**与**返回值**：`and`/`or` 返回的是操作数本身，而非布尔值。

```python
# and：遇到 Falsy 就返回它，否则返回最后一个
print(0 and 1)        # 0（0 是 Falsy，短路）
print(1 and 2)        # 2（都 Truthy，返回最后一个）
print(1 and 0 and 3)  # 0

# or：遇到 Truthy 就返回它，否则返回最后一个
print(1 or 2)         # 1（1 是 Truthy，短路）
print(0 or 2)         # 2（0 是 Falsy，继续）
print(0 or "" or 3)   # 3

# eshop 场景：提供默认值
nick = "" or "匿名用户"   # nick = "匿名用户"
```

### 4. 赋值运算符

基本 `=`，以及复合赋值：`+=`、`-=`、`*=`、`/=`、`//=`、`%=`、`**=`、`&=`、`|=`、`^=`、`<<=`、`>>=`。

**海象运算符 `:=`（3.8+）**：在表达式内部赋值，减少重复计算。

```python
# 传统写法：input 调用两次
line = input()
if line:
    process(line)

# 海象运算符：赋值与判断一次完成
if (line := input()):
    process(line)

# eshop 场景：循环读取直到空行
while (cmd := input(">>> ")) != "quit":
    print(f"执行: {cmd}")
```

### 5. 位运算符

| 运算符 | 含义 | 示例（a=5=0b101, b=3=0b011） |
| --- | --- | --- |
| `&` | 按位与 | `5 & 3` → `1`（0b001） |
| `\|` | 按位或 | `5 \| 3` → `7`（0b111） |
| `^` | 按位异或 | `5 ^ 3` → `6`（0b110） |
| `~` | 按位取反 | `~5` → `-6` |
| `<<` | 左移 | `5 << 1` → `10` |
| `>>` | 右移 | `5 >> 1` → `2` |

位运算常用于权限标志位：`read=1, write=2, execute=4`。

### 6. 成员运算符

`in` 与 `not in`，判断元素是否在容器中。

```python
print(3 in [1, 2, 3])          # True
print("e" in "eshop")          # True
print("price" in {"price": 99})# True
print(5 not in [1, 2, 3])      # True
```

### 7. 身份运算符

`is` 与 `is not` 比较**对象身份**（`id()`），`==` 比较**值**。

| 对比 | `is` | `==` |
| --- | --- | --- |
| 比较内容 | 对象 id（内存地址） | 值 |
| 适用 | `None`、单例、缓存对象 | 任意值 |

**小整数缓存**：CPython 缓存了 `-5~256` 的整数，此范围内的整数共享同一对象。

```python
a = 256; b = 256
print(a is b)    # True（缓存）

a = 257; b = 257
print(a is b)    # False（不缓存，但同一行赋值可能优化）

# 判断 None 必须用 is
if x is None:
    ...
```

### 8. 运算符优先级（从高到低）

| 优先级 | 运算符 |
| --- | --- |
| 1 | `**` |
| 2 | `~`、`+x`、`-x`（一元） |
| 3 | `*`、`/`、`%`、`//` |
| 4 | `+`、`-` |
| 5 | `<<`、`>>` |
| 6 | `&` |
| 7 | `^` |
| 8 | `\|` |
| 9 | `==`、`!=`、`>`、`<`、`>=`、`<=`、`is`、`in` |
| 10 | `not` |
| 11 | `and` |
| 12 | `or` |
| 13 | `:=`（海象） |

不确定优先级时，**用括号明确意图**。

### 9. if / elif / else

```python
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 60:
    grade = "C"
else:
    grade = "D"
```

- Python 用**缩进**表示代码块，约定 4 空格
- `elif` 是 `else if` 的缩写，避免深层嵌套

**条件表达式（三元运算符）**：

```python
# x if condition else y
status = "有货" if stock > 0 else "缺货"
```

### 10. match-case 模式匹配（3.10+）

`match-case` 是 Python 3.10 引入的结构化模式匹配，比 `if-elif` 更适合处理多分支数据结构。

```python
match value:
    case 1:
        print("一")
    case 2 | 3:          # 或模式
        print("二或三")
    case [x, y]:         # 序列解构
        print(f"两个元素: {x}, {y}")
    case {"name": str(name)}:  # 类模式（字典）
        print(f"名字: {name}")
    case _:              # 通配，必须放最后
        print("其他")
```

匹配规则：

- **字面量匹配**：`case 100`、`case "hi"`
- **变量绑定**：`case [x, y]` 将元素绑定到变量
- **序列解构**：`case [a, *rest]` 支持星号解包
- **或模式**：`case 1 | 2 | 3`
- **类模式**：`case Point(x=0, y=0)`
- **守卫（guard）**：`case [x] if x > 0`

### 11. for 循环

```python
# 遍历可迭代对象
for item in [1, 2, 3]:
    print(item)

# range(start, stop, step)
for i in range(0, 10, 2):   # 0, 2, 4, 6, 8
    print(i)

# 遍历字典
d = {"name": "eshop", "price": 99}
for key in d:               # 默认遍历键
    print(key, d[key])
for key, value in d.items():# 同时遍历键值
    print(key, value)
```

### 12. while 循环

```python
count = 0
while count < 3:
    print(count)
    count += 1
```

`while-else`：循环**正常结束**（未 break）时执行 else。

### 13. break / continue / pass

| 语句 | 作用 |
| --- | --- |
| `break` | 跳出当前循环 |
| `continue` | 跳过本次，进入下一次循环 |
| `pass` | 空操作，占位用 |

### 14. for-else

`for-else` 的 else 在循环**未被 break 中断**时执行，常用于"查找失败"场景：

```python
for item in items:
    if item == target:
        print("找到了")
        break
else:
    print("没找到")   # 循环正常结束（没 break）才执行
```

### 15. enumerate() 与 zip()

```python
# enumerate：同时获取索引和值
for index, value in enumerate(["a", "b", "c"]):
    print(index, value)   # 0 a, 1 b, 2 c

# zip：并行遍历多个序列
names = ["iPhone", "MacBook"]
prices = [5999, 12999]
for name, price in zip(names, prices):
    print(name, price)
```

### 16. 循环常见模式

- **累加**：`total = 0; for x in data: total += x`
- **过滤**：`if x > threshold: ...`
- **查找**：`for x in data: if x == target: break` + `for-else`

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/operators.py` | 运算符演示，覆盖算术/比较/逻辑/位/成员/身份运算符、海象运算符、短路求值、小整数缓存 |
| `Code/if_else.py` | 条件语句练习，演示 if/elif/else、嵌套、三元运算符，用电商订单状态与折扣计算 |
| `Code/loops.py` | 循环练习，演示 for+range、while、break/continue/pass、for-else、enumerate、zip，用电商商品遍历 |
| `Code/match_case.py` | match-case 模式匹配练习，覆盖基本匹配、字面量、变量绑定、序列解构、类模式 |

## 关键知识点总结

### 运算符优先级表（简记）

`**` > 一元 > `* / % //` > `+ -` > 位移 > `& ^ |` > 比较 > `not` > `and` > `or` > `:=`

### 海象运算符用法

```python
# 1. while 读取
while (chunk := read()) != "":
    process(chunk)

# 2. 条件判断中赋值
if (n := len(data)) > 10:
    print(f"数据过长: {n}")

# 3. 列表推导式中复用
results = [y for x in data if (y := f(x)) is not None]
```

### match-case 语法速查

```python
match obj:
    case 1 | 2:              # 或模式
    case [a, b]:             # 序列解构
    case [first, *rest]:     # 星号解包
    case Point(x=0, y=0):    # 类模式
    case x if x > 0:         # 守卫
    case _:                  # 通配（必须最后）
```

### for-else 执行逻辑

- 循环**正常结束**（没遇到 break）→ 执行 else 块
- 循环**被 break 中断** → 不执行 else 块
- 典型用途：查找元素，else 块处理"未找到"

## 实战练习

### 练习 1：订单折扣计算

编写函数 `calc_discount(total, vip_level)`，规则：

- VIP3 以上且金额 ≥ 1000 → 7 折
- VIP2 以上且金额 ≥ 500 → 8 折
- VIP1 以上 → 9 折
- 其他 → 不打折

用 `if/elif/else` 实现，并测试多组数据。

### 练习 2：库存查找

给定商品列表 `products = [("iPhone", 5), ("MacBook", 0), ("AirPods", 3)]`，用 `for-else` 查找第一个缺货商品，找不到则输出"全部有货"。

### 练习 3：订单状态分发

用 `match-case` 处理订单状态字符串：`"pending"`（待付款）、`"paid"`（已付款）、`"shipped"`（已发货）、`"completed"`（已完成）、`"cancelled"`（已取消），对每种状态输出对应处理逻辑，未知状态输出"未知状态"。
