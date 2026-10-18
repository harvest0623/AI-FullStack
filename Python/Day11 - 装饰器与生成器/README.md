# Day11 - 装饰器与生成器

装饰器和生成器是 Python 的高级特性，也是编写 Pythonic 代码的关键。装饰器让你在不修改原函数的前提下优雅地扩展功能——计时、日志、缓存、重试、权限校验都可以用一行 `@decorator` 完成；生成器则用 `yield` 实现惰性求值，让你能用极小的内存处理无限序列或百万级数据流。本 Day 将从无参装饰器讲到带参装饰器、类装饰器、装饰器堆叠，再从生成器表达式讲到 `yield from`、生成器管道，为 eshop 工具加上缓存、日志、流式数据处理能力。

---

## 学习目标

- 理解装饰器本质：接收函数返回函数的高阶函数
- 熟练编写无参装饰器与带参装饰器（三层嵌套）
- 掌握 `functools.wraps` 保留函数元信息的原因
- 能编写类装饰器（`__call__`）并理解装饰器堆叠的执行顺序
- 会用 `functools.lru_cache` / `cache` 缓存函数结果
- 实战装饰器：计时、日志、重试、权限校验
- 理解生成器与列表推导式的内存差异
- 熟练使用 `yield`、`next()`、`send()`、`yield from`
- 能构建生成器管道处理大数据流

---

## 理论知识讲解 - 装饰器

### 1. 装饰器概念

装饰器是**在不修改原函数源代码的前提下扩展其功能**的语法糖，用 `@` 应用：

```python
@timer
def slow_func():
    ...

# 等价于
def slow_func():
    ...
slow_func = timer(slow_func)   # timer 接收函数，返回新函数
```

### 2. 装饰器本质

装饰器是**接收函数返回函数的高阶函数**：

```python
def my_decorator(func):          # 接收原函数
    def wrapper(*args, **kwargs): # 定义新函数
        print('前置')
        result = func(*args, **kwargs)  # 调用原函数
        print('后置')
        return result            # 返回原函数结果
    return wrapper               # 返回新函数
```

### 3. 无参装饰器

```python
import functools

def my_decorator(func):
    @functools.wraps(func)       # 保留原函数的 __name__/__doc__/__module__
    def wrapper(*args, **kwargs):
        # 前置逻辑
        result = func(*args, **kwargs)
        # 后置逻辑
        return result
    return wrapper

@my_decorator
def hello(name):
    """打招呼"""
    return f'Hello, {name}'

hello('Tom')
# 等价于 hello = my_decorator(hello); hello('Tom')
```

### 4. `functools.wraps` 的作用

不加 `wraps`，被装饰函数的元信息会丢失：

```python
def bad_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@bad_decorator
def hello(name): ...

hello.__name__    # 'wrapper'  ← 不是 'hello'！
hello.__doc__      # None       ← 原 docstring 丢了
```

加 `@functools.wraps(func)` 后，`wrapper` 的 `__name__`、`__doc__`、`__module__`、`__wrapped__` 都会指向原函数，调试和反射才正常。

### 5. 带参装饰器（三层嵌套）

带参数的装饰器需要**三层函数**：最外层接收参数，中层接收函数，内层是 wrapper：

```python
def repeat(n):                       # 第1层：接收装饰器参数
    def decorator(func):             # 第2层：接收被装饰函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):# 第3层：实际包装
            result = None
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)        # 先调用 repeat(3) 得到 decorator，再用 decorator 装饰 greet
def greet(name):
    print(f'Hi, {name}')

greet('Tom')      # 打印 3 次
```

### 6. 类装饰器

用 `__call__` 让类的实例可调用，从而当装饰器用：

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f'第 {self.count} 次调用 {self.func.__name__}')
        return self.func(*args, **kwargs)

@CountCalls
def say(msg):
    print(msg)

say('a'); say('b')   # count 累加到 2
print(say.count)     # 类装饰器可保存状态
```

### 7. 装饰器堆叠

多个装饰器叠加时，**从下往上应用，从上往下执行**：

```python
@a
@b
@c
def f(): ...

# 等价于：f = a(b(c(f)))
# 应用顺序：c → b → a（从下往上）
# 执行顺序：a 的前置 → b 的前置 → c 的前置 → f → c 的后置 → b 的后置 → a 的后置
```

### 8. 常用内置装饰器回顾

| 装饰器 | 作用 | 来源 |
|--------|------|------|
| `@property` | 把方法变属性 | 内置 |
| `@staticmethod` | 静态方法 | 内置 |
| `@classmethod` | 类方法 | 内置 |
| `@dataclass` | 自动生成数据类 | dataclasses |
| `@abstractmethod` | 抽象方法 | abc |

### 9. `functools.lru_cache` / `functools.cache`

缓存函数结果，避免重复计算：

```python
from functools import lru_cache

@lru_cache(maxsize=128)     # 最多缓存 128 个结果
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)

fib(100)                    # 瞬间完成（无缓存会极慢）
fib.cache_info()            # 查看命中情况
fib.cache_clear()           # 清空缓存

# Python 3.9+ 的 cache 等价于 lru_cache(maxsize=None)
from functools import cache
@cache
def expensive(x): ...
```

> **注意**：被缓存的函数参数必须是可哈希的（list/dict/set 不行，需转 tuple/frozenset）。

### 10. 实战装饰器

| 装饰器 | 用途 |
|--------|------|
| `@timer` | 测量函数执行时间 |
| `@log` | 记录函数调用日志 |
| `@retry(n)` | 失败自动重试 n 次 |
| `@require_admin` | 权限校验 |
| `@validate_args` | 参数验证 |

---

## 理论知识讲解 - 生成器

### 1. 列表推导式 vs 生成器表达式

```python
[x * 2 for x in range(10)]    # 列表推导式：[] 立即生成全部，占内存
(x * 2 for x in range(10))    # 生成器表达式：() 惰性生成，省内存
```

### 2. `yield` 关键字

函数里出现 `yield`，它就变成**生成器函数**，调用后返回一个生成器对象（不立即执行）：

```python
def gen():
    print('start')
    yield 1          # 暂停并返回 1
    print('after 1')
    yield 2          # 暂停并返回 2
    print('after 2')

g = gen()            # 不执行任何代码，只创建生成器
next(g)              # 打印 start，返回 1
next(g)              # 打印 after 1，返回 2
next(g)              # 打印 after 2，抛 StopIteration
```

### 3. 生成器 vs 列表

| 对比项 | 列表 | 生成器 |
|--------|------|--------|
| 内存 | 占用大（全量存储） | 极小（只存当前状态） |
| 求值 | 立即（eager） | 惰性（lazy） |
| 重复遍历 | 可多次 | 只能一次 |
| 索引 | 支持 `lst[i]` | 不支持 |
| 适用 | 需随机访问/多次遍历 | 大数据/流式/无限序列 |

```python
# 内存对比
import sys
lst = [x for x in range(1000000)]     # 列表：约 8MB
gen = (x for x in range(1000000))     # 生成器：约 200 字节
sys.getsizeof(lst), sys.getsizeof(gen)
```

### 4. `next()` 与 `StopIteration`

```python
g = (x for x in range(3))
next(g)    # 0
next(g)    # 1
next(g)    # 2
next(g)    # 抛 StopIteration

# 用默认值避免异常
g = (x for x in range(3))
next(g, '结束')   # 0
next(g, '结束')   # 1
next(g, '结束')   # 2
next(g, '结束')   # '结束'（耗尽后返回默认值）
```

### 5. `send()` 与生成器交互

`send()` 向生成器内部传值，`yield` 表达式会接收这个值：

```python
def accumulator():
    total = 0
    while True:
        value = yield total      # yield 返回 total，并接收 send 进来的 value
        total += value

acc = accumulator()
next(acc)        # 启动生成器，返回 0（必须先 next 或 send(None) 启动）
acc.send(10)     # 返回 10
acc.send(20)     # 返回 30
acc.send(5)      # 返回 35
```

### 6. `yield from` 委托生成器

`yield from` 把一个可迭代对象的元素逐个 yield 出来，常用于扁平化嵌套或委托给子生成器：

```python
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)   # 递归委托
        else:
            yield item

list(flatten([1, [2, [3, 4]], 5]))    # [1, 2, 3, 4, 5]
```

### 7. 无限生成器

```python
def counter(start=0):
    i = start
    while True:        # 永不停止
        yield i
        i += 1

c = counter()
next(c)   # 0
next(c)   # 1
next(c)   # 2
# 配合 islice 取有限个
from itertools import islice
list(islice(counter(10), 5))   # [10, 11, 12, 13, 14]
```

### 8. 生成器管道

把多个生成器串联成流水线，每一步惰性处理，内存恒定：

```python
def read_lines(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            yield line.strip()

def filter_amount(lines, min_amount):
    for line in lines:
        _, amount = line.split(',')
        if float(amount) >= min_amount:
            yield line

def transform(lines):
    for line in lines:
        name, amount = line.split(',')
        yield f'{name}: ¥{float(amount):.2f}'

# 管道：读取 → 过滤 → 转换
pipeline = transform(filter_amount(read_lines('orders.csv'), 100))
for item in pipeline:        # 逐条流动，内存只存当前条
    print(item)
```

### 9. 生成器应用场景

- **大数据处理**：百万行 CSV/日志，逐行处理不爆内存
- **流式处理**：网络数据流、传感器数据
- **无限序列**：斐波那契、素数、计数器
- **懒加载**：按需生成，避免预计算浪费

---

## 代码文件说明

| 文件 | 用途 |
|------|------|
| `Code/decorators.py` | 装饰器基础：无参装饰器、`functools.wraps`、类装饰器、装饰器堆叠；电商场景：`@timer` 计时、`@log` 记录调用日志 |
| `Code/advanced_decorators.py` | 高级装饰器：带参装饰器、`@retry` 重试、`@lru_cache` 缓存、权限校验；电商场景：API 重试、商品查询缓存、管理员校验 |
| `Code/generators.py` | 生成器基础：`yield`、`next/send`、`yield from`、无限生成器；电商场景：商品分页生成器、订单流处理 |
| `Code/generator_pipeline.py` | 生成器管道：读取大 CSV → 过滤 → 转换 → 输出；电商场景：流式处理百万级订单数据 |

**运行方式**：

```bash
cd "Day11 - 装饰器与生成器/Code"
python decorators.py
python advanced_decorators.py
python generators.py
python generator_pipeline.py
```

---

## 关键知识点总结

### 装饰器执行流程图

```
@decorator
def func(): ...

调用 func(args):
  ┌─ decorator 的 wrapper 被调用
  │   ┌─ 前置逻辑（如计时开始）
  │   │   ┌─ 原始 func(args) 执行
  │   │   └─ 得到 result
  │   └─ 后置逻辑（如计时结束、记录日志）
  └─ return result
```

### 带参装饰器三层结构图

```
@repeat(3)              repeat(3)
def f(): ...     →      返回 decorator
                         ↓
                         decorator(f)
                         返回 wrapper
                              ↓
                         f() 实际调用 wrapper()

三层函数：
  repeat(n)          ← 接收装饰器参数
    decorator(func)  ← 接收被装饰函数
      wrapper(...)   ← 实际包装逻辑
```

### 生成器 vs 列表对比表

| 维度 | 列表 `[x for x in ...]` | 生成器 `(x for x in ...)` |
|------|------------------------|--------------------------|
| 语法 | `[]` | `()` |
| 求值时机 | 立即全量 | 惰性逐个 |
| 内存 | O(n) | O(1) |
| 重复遍历 | ✅ 多次 | ❌ 一次 |
| 索引 `g[i]` | ✅ | ❌ |
| `len()` | ✅ | ❌ |
| 适用 | 小数据、需随机访问 | 大数据、流式、无限 |

### 生成器管道示意图

```
数据源        过滤器        转换器        输出
─────        ─────        ─────        ─────
read ──→  filter ──→  transform ──→  for item
lines      amount>100   格式化          print

特点：每条数据逐级流动，内存恒定 O(1)
```

---

## 实战练习

### 练习 1：实现 `@memoize` 装饰器

不用 `functools.lru_cache`，自己实现一个 `@memoize` 装饰器，缓存函数结果，并支持查看缓存命中率。要求：用字典存储缓存，参数需可哈希；用 `functools.wraps` 保留元信息。

### 练习 2：电商数据流式统计

用生成器管道处理一个 10 万行的 `orders.csv`（每行 `order_id,customer,amount`），实现：
- 读取所有行（生成器）
- 过滤掉金额异常（< 0）的行
- 按客户聚合消费总额
- 输出消费 TOP 10 客户

要求全程内存恒定，不一次性 `read()` 全部。

### 练习 3：带过期时间的缓存装饰器

扩展 `@lru_cache`，实现 `@timed_cache(seconds=60)`：缓存结果但在指定秒数后失效。提示：用 `time.time()` 记录写入时间，命中时检查是否过期；可结合 `functools.lru_cache` 与自定义逻辑。
