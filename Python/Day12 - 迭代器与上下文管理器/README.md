# Day12 - 迭代器与上下文管理器

迭代器和上下文管理器是 Python 的两大核心协议，深入理解它们能让代码更加 Pythonic。迭代器协议（`__iter__` + `__next__`）是 for 循环、推导式、生成器的底层基石；上下文管理器协议（`__enter__` + `__exit__`）则是 `with` 语句的资源管理根基。本 Day 将从迭代协议本质讲到自定义迭代器、itertools 与 functools 精选，再从上下文管理器类实现讲到 contextlib 的 `@contextmanager` 装饰器，为 eshop 工具构建自定义迭代能力和健壮的资源管理体系。

---

## 学习目标

- 理解迭代协议：Iterable 与 Iterator 的区别
- 掌握 `iter()` / `next()` / `StopIteration` 的工作机制
- 理解 for 循环的本质：`iter()` → `next()` → `StopIteration`
- 能自定义迭代器（实现 `__iter__` 与 `__next__`）
- 精通 itertools：chain/combinations/permutations/product/groupby/islice/count/cycle/repeat/accumulate
- 掌握 functools：reduce/partial/lru_cache/cached_property/singledispatch
- 理解上下文管理器协议：`__enter__` 与 `__exit__`
- 能用类实现自定义上下文管理器
- 能用 contextlib 的 `@contextmanager` 用生成器实现上下文管理器
- 掌握 contextlib 工具：closing/suppress/redirect_stdout/ExitStack

---

## 理论知识讲解 - 迭代器

### 1. 迭代协议

Python 的迭代基于两个协议：

| 协议 | 方法 | 说明 |
|------|------|------|
| **Iterable（可迭代对象）** | `__iter__()` | 返回一个迭代器 |
| **Iterator（迭代器）** | `__iter__()` + `__next__()` | `__next__` 返回下一个值，无值时抛 `StopIteration` |

```python
# 可迭代对象：列表、字典、字符串、集合、生成器等都是 Iterable
lst = [1, 2, 3]
isinstance(lst, Iterable)    # True
isinstance(lst, Iterator)    # False ← 列表是可迭代，但不是迭代器

# 迭代器：用 iter() 从可迭代对象获取
it = iter(lst)
isinstance(it, Iterator)     # True
next(it)    # 1
next(it)    # 2
next(it)    # 3
next(it)    # 抛 StopIteration
```

### 2. `iter()` 与 `next()`

| 函数 | 作用 |
|------|------|
| `iter(iterable)` | 获取可迭代对象的迭代器 |
| `next(iterator)` | 取下一个值，耗尽抛 `StopIteration` |
| `next(iterator, default)` | 耗尽返回 default，不抛异常 |

### 3. for 循环的本质

`for x in iterable:` 的底层等价于：

```python
# for x in lst: ... 等价于
iterator = iter(lst)
while True:
    try:
        x = next(iterator)
    except StopIteration:
        break
    # 循环体
```

### 4. Iterable vs Iterator 区别

| 维度 | Iterable | Iterator |
|------|----------|----------|
| 协议 | `__iter__` | `__iter__` + `__next__` |
| 可重复遍历 | ✅（每次新建迭代器） | ❌（一次性，耗尽即止） |
| 例 | list/dict/str/set | 生成器、`iter(lst)` 返回值 |
| `next()` | ❌ 不支持 | ✅ 支持 |

> 生成器既是 Iterable 也是 Iterator（它的 `__iter__` 返回自身）。

### 5. 自定义迭代器

实现 `__iter__` 和 `__next__` 即可：

```python
class Range:
    def __init__(self, start, stop, step=1):
        self.current = start
        self.stop = stop
        self.step = step

    def __iter__(self):
        return self           # 迭代器返回自身

    def __next__(self):
        if self.current >= self.stop:
            raise StopIteration
        value = self.current
        self.current += self.step
        return value

for x in Range(1, 5):
    print(x)    # 1 2 3 4
```

### 6. itertools 精选详解

| 函数 | 作用 | 示例 |
|------|------|------|
| `chain(*iterables)` | 串联多个迭代器 | `chain([1,2],[3,4])` → 1,2,3,4 |
| `combinations(iter, r)` | 组合 C(n,r) | `combinations('ABC',2)` → AB,AC,BC |
| `permutations(iter, r)` | 排列 P(n,r) | `permutations('AB',2)` → AB,BA |
| `product(*iterables)` | 笛卡尔积 | `product('AB','12')` → A1,A2,B1,B2 |
| `groupby(iter, key)` | 分组（需先排序） | 按分类分组 |
| `islice(iter, start, stop, step)` | 切片 | 取前 N 个 |
| `count(start, step)` | 无限计数 | `count(10)` → 10,11,12,... |
| `cycle(iter)` | 无限循环 | `cycle('AB')` → A,B,A,B,... |
| `repeat(elem, times)` | 重复 | `repeat('x', 3)` → x,x,x |
| `accumulate(iter)` | 累积 | `[1,2,3]` → 1,3,6 |
| `takewhile(pred, iter)` | 取到条件为 False | `takewhile(<5, [1,2,5,3])` → 1,2 |
| `dropwhile(pred, iter)` | 丢到条件为 False | `dropwhile(<5,[1,2,5,3])` → 5,3 |

### 7. functools 精选

| 函数 | 作用 |
|------|------|
| `reduce(func, iter, initial)` | 累积归约 |
| `partial(func, *args)` | 偏函数，固定部分参数 |
| `lru_cache(maxsize)` / `cache` | 缓存（Day11 已讲） |
| `cached_property` | 缓存属性，只算一次 |
| `singledispatch` | 单分派泛型函数，按第一个参数类型分派 |

```python
from functools import reduce, partial, cached_property, singledispatch

reduce(lambda x, y: x + y, [1, 2, 3, 4])        # 10
round2 = partial(round, ndigits=2)              # round2(3.14159) → 3.14

class Circle:
    def __init__(self, r): self.r = r
    @cached_property
    def area(self):
        print('计算面积')
        return 3.14 * self.r ** 2                # 只算一次，后续直接取缓存

@singledispatch
def to_json(obj):
    return str(obj)
@to_json.register
def _(obj: dict): return dict(obj)              # 按类型分派
```

---

## 理论知识讲解 - 上下文管理器

### 1. 上下文管理器协议

实现 `__enter__` 和 `__exit__` 两个方法的对象就是上下文管理器：

```python
with manager as value:
    # 使用 value
    ...
# 离开 with 块自动调用 __exit__
```

### 2. `with` 语句执行流程

```
1. 调用 manager.__enter__()，返回值赋给 as 变量
2. 执行 with 块内代码
3. 无论是否异常，调用 manager.__exit__(exc_type, exc_val, exc_tb)
4. 若 __exit__ 返回 True，则抑制异常（不向外传播）
5. 若 __exit__ 返回 False 或 None，异常继续传播
```

### 3. 自定义上下文管理器（类实现）

```python
class FileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        self.file = open(self.filename, self.mode, encoding='utf-8')
        return self.file                # as 变量拿到的是这个返回值

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False                    # 不抑制异常，让它正常传播

with FileManager('a.txt', 'w') as f:
    f.write('hello')
# 离开 with，f 自动 close
```

`__exit__` 的三个参数：
- `exc_type`：异常类型（无异常时为 None）
- `exc_val`：异常实例
- `exc_tb`：异常 traceback

### 4. contextlib 模块

#### `@contextmanager` 装饰器

用生成器实现上下文管理器，比写类更简洁：

```python
from contextlib import contextmanager

@contextmanager
def my_context():
    # __enter__ 逻辑（前置）
    print('进入')
    try:
        yield value          # with 块内拿到的值（yield 出去）
    finally:
        # __exit__ 逻辑（后置，无论是否异常都执行）
        print('退出')
```

`yield` 之前的代码 = `__enter__`，`yield` 之后的代码 = `__exit__`。如果 with 块内抛异常，会在 `yield` 处重新抛出，可用 `try/except` 捕获处理。

#### 其他 contextlib 工具

| 工具 | 作用 |
|------|------|
| `closing(thing)` | 退出时自动调用 `thing.close()` |
| `suppress(*exceptions)` | 忽略指定异常 |
| `redirect_stdout(target)` | 重定向标准输出 |
| `redirect_stderr(target)` | 重定向标准错误 |
| `ExitStack()` | 管理多个上下文 |

```python
from contextlib import suppress, redirect_stdout, ExitStack, closing

# suppress：忽略指定异常
with suppress(FileNotFoundError):
    os.remove('不存在.txt')      # 不存在也不报错

# redirect_stdout：捕获 print 输出
import io
buf = io.StringIO()
with redirect_stdout(buf):
    print('被重定向')
print(buf.getvalue())            # '被重定向\n'

# ExitStack：动态管理多个上下文
with ExitStack() as stack:
    f1 = stack.enter_context(open('a.txt'))
    f2 = stack.enter_context(open('b.txt'))
    # 退出时按相反顺序关闭
```

### 5. 实战上下文管理器

| 场景 | 用途 |
|------|------|
| 数据库连接管理 | 自动提交/回滚/关闭连接 |
| 计时器 | 测量代码块耗时 |
| 临时目录 | 用完自动清理 |
| 文件锁 | 自动释放锁 |
| 资源池 | 借还资源 |

---

## 代码文件说明

| 文件 | 用途 |
|------|------|
| `Code/iterators.py` | 自定义迭代器：实现 `__iter__`/`__next__`；电商场景：ProductIterator、PageIterator、反向迭代器 |
| `Code/itertools_demo.py` | itertools 练习：chain/combinations/permutations/product/groupby/islice/count/cycle/repeat/accumulate；电商场景：商品组合推荐、按分类分组、批量处理 |
| `Code/context_manager.py` | 自定义上下文管理器：类实现 `__enter__`/`__exit__`；电商场景：数据库连接管理器、文件锁、计时器上下文 |
| `Code/contextlib_demo.py` | contextlib 练习：`@contextmanager`、closing/suppress/redirect_stdout/ExitStack；电商场景：计时器、临时目录、忽略文件不存在错误 |

**运行方式**：

```bash
cd "Day12 - 迭代器与上下文管理器/Code"
python iterators.py
python itertools_demo.py
python context_manager.py
python contextlib_demo.py
```

---

## 关键知识点总结

### 迭代协议图解

```
        ┌──────────────────────────────────────────┐
        │           for x in iterable:             │
        └──────────────────┬───────────────────────┘
                           │ 1. iter(iterable)
                           ▼
        ┌──────────────────────────────────────────┐
        │  iterator = iterable.__iter__()          │
        └──────────────────┬───────────────────────┘
                           │ 2. 循环 next(iterator)
                           ▼
        ┌──────────────────────────────────────────┐
        │  x = iterator.__next__()                 │
        │  ├─ 有值 → 执行循环体，回到 2            │
        │  └─ 无值 → 抛 StopIteration → 结束循环   │
        └──────────────────────────────────────────┘

        Iterable：只实现 __iter__（list/dict/str/set）
        Iterator：实现 __iter__ + __next__（生成器、iter() 返回值）
```

### itertools 函数速查表

| 函数 | 签名 | 用途 | 是否惰性 |
|------|------|------|---------|
| `chain` | `chain(*iterables)` | 串联 | ✅ |
| `combinations` | `combinations(iter, r)` | 组合 C(n,r) | ✅ |
| `permutations` | `permutations(iter, r)` | 排列 P(n,r) | ✅ |
| `product` | `product(*iter, repeat=1)` | 笛卡尔积 | ✅ |
| `groupby` | `groupby(iter, key)` | 分组 | ✅ |
| `islice` | `islice(iter, stop)` | 切片 | ✅ |
| `count` | `count(start, step)` | 无限计数 | ✅ |
| `cycle` | `cycle(iter)` | 无限循环 | ✅ |
| `repeat` | `repeat(elem, times)` | 重复 | ✅ |
| `accumulate` | `accumulate(iter, func)` | 累积 | ✅ |
| `takewhile` | `takewhile(pred, iter)` | 取到 False 止 | ✅ |
| `dropwhile` | `dropwhile(pred, iter)` | 丢到 False 止 | ✅ |

### 上下文管理器协议图

```
with Manager() as value:
    ┌─────────────────────────────────────────┐
    │ 1. Manager.__enter__()                  │
    │    └─ 返回值 → 赋给 value               │
    ├─────────────────────────────────────────┤
    │ 2. 执行 with 块内代码（用 value）       │
    │    └─ 可能抛异常                        │
    ├─────────────────────────────────────────┤
    │ 3. Manager.__exit__(exc_type, exc_val,  │
    │                      exc_tb)            │
    │    └─ 返回 True  → 抑制异常             │
    │    └─ 返回 False → 异常传播             │
    └─────────────────────────────────────────┘
```

### contextlib 工具速查表

| 工具 | 用途 | 等价类实现 |
|------|------|-----------|
| `@contextmanager` | 用生成器实现上下文管理器 | 自定义类 `__enter__`/`__exit__` |
| `closing(thing)` | 退出调 `thing.close()` | `__exit__` 里调 close |
| `suppress(*exc)` | 忽略指定异常 | `__exit__` 返回 True |
| `redirect_stdout(target)` | 重定向 stdout | 替换 sys.stdout |
| `redirect_stderr(target)` | 重定向 stderr | 替换 sys.stderr |
| `ExitStack()` | 管理多个动态上下文 | 嵌套多个 with |

---

## 实战练习

### 练习 1：实现双向迭代器

扩展 `iterators.py` 的 `ProductIterator`，实现一个支持正向和反向遍历的迭代器。提示：在 `__init__` 加 `reverse` 参数；实现 `__iter__` 返回自身；`__next__` 根据方向移动指针。

### 练习 2：商品推荐组合生成器

用 itertools 实现：给定一组商品和预算金额，找出所有「总价不超过预算」的商品组合（2 件及以上）。要求用 `combinations` 生成组合，用 `takewhile` 提前终止超出预算的遍历。

### 练习 3：事务上下文管理器

实现一个 `Transaction` 上下文管理器，模拟数据库事务：
- `__enter__` 开启事务，返回连接对象
- with 块内执行多条「SQL」（用 print 模拟）
- 无异常 → `__exit__` 提交事务（COMMIT）
- 有异常 → `__exit__` 回滚事务（ROLLBACK）并记录日志
- 用 `@contextmanager` 版本再实现一次，对比两种写法
