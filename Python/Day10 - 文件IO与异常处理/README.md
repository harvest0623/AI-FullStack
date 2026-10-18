# Day10 - 文件IO与异常处理

文件 IO 和异常处理是生产级 Python 程序的基础：前者让数据能够持久化到磁盘、从外部读入内存；后者让程序在遇到意外情况时仍能安全降级而非崩溃。本 Day 将系统讲解 `open()` 的各种模式、`with` 语句的资源管理、JSON/CSV 的读写、pathlib 面向对象的路径操作，并深入异常处理体系——从内置异常层级到自定义异常、异常链与最佳实践，为 eshop 工具构建稳健的数据读写与错误处理能力。

---

## 学习目标

- 掌握 `open()` 与各种读写模式（r/w/a/r+/x、二进制 rb/wb/ab）
- 理解 `encoding` 参数与 UTF-8 编码的重要性
- 熟练使用 `with` 语句自动管理资源
- 掌握大文件逐行读取避免内存爆炸
- 用 pathlib 优雅地读写文件
- 精通 JSON 与 CSV 的读写（含中文处理）
- 了解 tempfile 临时文件与 shutil 高级文件操作
- 掌握 try/except/else/finally 四段式异常处理
- 理解异常类型层级，能捕获多种异常
- 能用 `raise` 主动抛出异常并构建异常链
- 能设计电商场景的自定义异常体系

---

## 理论知识讲解 - 文件 IO

### 1. `open()` 函数

```python
open(file, mode='r', encoding=None)
```

`open()` 返回一个文件对象，用完必须关闭。三个核心参数：

| 参数 | 说明 |
|------|------|
| `file` | 文件路径（字符串或 Path 对象） |
| `mode` | 读写模式，默认 `'r'` |
| `encoding` | 文本编码，文本模式建议显式指定 `utf-8` |

```python
f = open('a.txt', 'r', encoding='utf-8')
content = f.read()
f.close()              # 必须手动关闭
```

> **Windows 编码陷阱**：Windows 默认编码是 GBK，不指定 `encoding` 读 UTF-8 文件会乱码或报错。**永远显式写 `encoding='utf-8'`**。

### 2. 读写模式

| 模式 | 含义 | 文件不存在 | 文件已存在 |
|------|------|-----------|-----------|
| `r` | 只读（默认） | 报错 | 从头读 |
| `w` | 只写（覆盖） | 创建 | **清空内容** |
| `a` | 追加写 | 创建 | 在末尾追加 |
| `r+` | 读写 | 报错 | 保留内容，指针在开头 |
| `x` | 独占创建 | 创建 | **报错**（防覆盖） |

加 `b` 变二进制模式：`rb` / `wb` / `ab` / `r+b`。二进制模式读写 `bytes`，不带 `encoding`。

```python
# 文本模式
with open('log.txt', 'a', encoding='utf-8') as f:
    f.append('新日志\n')          # 注意：文件对象没有 append，用 write

# 二进制模式（图片、视频、序列化数据）
with open('image.png', 'rb') as f:
    data = f.read()               # bytes
with open('copy.png', 'wb') as f:
    f.write(data)
```

> **x 模式的价值**：写新文件时用 `x` 而非 `w`，可避免误覆盖已存在文件——存在则抛 `FileExistsError`。

### 3. `with` 语句：自动关闭文件

```python
# 旧写法：容易忘记 close，异常时也不会关闭
f = open('a.txt', encoding='utf-8')
try:
    data = f.read()
finally:
    f.close()

# 推荐写法：with 语句自动管理资源，即使异常也会关闭
with open('a.txt', encoding='utf-8') as f:
    data = f.read()
# 离开 with 块，f 自动 close
```

`with` 的本质是上下文管理器（Day12 详讲原理），它保证资源一定被释放，是处理文件、数据库连接、锁的**首选方式**。

### 4. 读取方式

| 方法 | 行为 | 适用 |
|------|------|------|
| `read()` | 一次性读全部内容 | 小文件 |
| `read(size)` | 读 size 个字符/字节 | 控制读取量 |
| `readline()` | 读一行（含 `\n`） | 逐行处理 |
| `readlines()` | 读所有行成列表 | 小文件 |
| `for line in f` | **迭代文件对象** | 大文件首选 |

```python
# ❌ 大文件用 read() 会撑爆内存
with open('huge.csv', encoding='utf-8') as f:
    all_text = f.read()        # 几百 MB 全进内存

# ✅ 逐行读取，内存友好
with open('huge.csv', encoding='utf-8') as f:
    for line in f:             # 每次只在内存中保留一行
        process(line)
```

> **大文件必用逐行迭代**：`for line in f` 是 Python 处理大文件最优雅、最省内存的方式。

### 5. 写入方式

```python
with open('out.txt', 'w', encoding='utf-8') as f:
    f.write('第一行\n')        # write 不自动加换行
    f.write('第二行\n')
    f.writelines(['a\n', 'b\n', 'c\n'])  # writelines 也不加换行，需自带
```

> `write` 和 `writelines` 都**不会自动加换行符**，必须手动在内容里带 `\n`。

### 6. pathlib 文件读写

Path 对象直接提供读写方法，更简洁：

```python
from pathlib import Path

p = Path('config.txt')
p.write_text('配置内容', encoding='utf-8')        # 一次写完
text = p.read_text(encoding='utf-8')             # 一次读完
p.write_bytes(b'\x00\x01\x02')                   # 写字节
data = p.read_bytes()                            # 读字节
```

适合小文件读写一气呵成；大文件仍需用 `open()` 逐行。

### 7. JSON 读写

| 方法 | 作用 |
|------|------|
| `json.dump(obj, f)` | 对象 → 文件 |
| `json.load(f)` | 文件 → 对象 |
| `json.dumps(obj)` | 对象 → 字符串 |
| `json.loads(s)` | 字符串 → 对象 |

```python
import json
from pathlib import Path

products = [
    {'id': 1, 'name': '手机', 'price': 2999.0},
    {'id': 2, 'name': '耳机', 'price': 399.0},
]

# 写文件：ensure_ascii=False 保留中文，indent=2 美化
with open('products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

# 读文件
with open('products.json', encoding='utf-8') as f:
    loaded = json.load(f)
```

**自定义序列化**：JSON 不支持 datetime 等类型，需用 `default` 参数：

```python
from datetime import datetime

def default_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()        # 转成 ISO 字符串
    raise TypeError(f'无法序列化 {type(obj)}')

json.dump({'time': datetime.now()}, f, default=default_encoder, ensure_ascii=False)
```

### 8. CSV 读写

```python
import csv

# 写 DictWriter（推荐，按字段名写）
with open('orders.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'customer', 'total'])
    writer.writeheader()
    writer.writerow({'id': 1, 'customer': '张三', 'total': 99.5})

# 读 DictReader（推荐，返回字典）
with open('orders.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['id'], row['customer'], row['total'])

# 也可用 reader/writer（返回列表）
with open('orders.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:                # row 是 list
        print(row)
```

> **Windows 写 CSV 必须 `newline=''`**：否则每行之间会多一个空行（Windows 换行符 `\r\n` 与 csv 模块自动加的 `\r\n` 叠加）。

`delimiter` 改分隔符（如 TSV 用 `\t`），`quotechar` 改引用字符。

### 9. tempfile 临时文件

```python
import tempfile

# 临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('临时数据')
    path = f.name                    # 拿到路径
# delete=False 表示退出 with 后不自动删，需手动清理

# 临时目录：退出 with 自动删除
with tempfile.TemporaryDirectory() as d:
    print(f'临时目录: {d}')
    # 在里面写文件...
# 离开 with 后 d 整个删除
```

### 10. shutil 文件操作

```python
import shutil

shutil.copy('a.txt', 'b.txt')              # 复制文件（不含元数据）
shutil.copy2('a.txt', 'b.txt')             # 复制文件（保留修改时间等元数据）
shutil.copytree('src/', 'backup/')         # 复制整个目录树
shutil.rmtree('backup/')                   # 删除整个目录树
shutil.move('a.txt', 'subdir/a.txt')       # 移动/重命名
shutil.make_archive('data', 'zip', 'src/') # 打包成 zip
```

---

## 理论知识讲解 - 异常处理

### 1. 异常概念

异常是**运行时错误**，本质是对象。程序出错时会抛出异常对象，如果不处理则程序终止并打印堆栈。

```python
1 / 0                   # ZeroDivisionError
int('abc')              # ValueError
open('不存在.txt')       # FileNotFoundError
[1, 2][10]              # IndexError
{'a': 1}['b']           # KeyError
```

### 2. try / except / else / finally

四段式结构：

```python
try:
    # 可能出错的代码
    data = open('data.json').read()
except FileNotFoundError as e:
    # 捕获特定异常
    print(f'文件不存在: {e}')
except (ValueError, KeyError) as e:
    # 捕获多种异常
    print(f'数据错误: {e}')
else:
    # try 块没有异常时才执行（放成功后的逻辑）
    print(f'读取成功: {data}')
finally:
    # 无论是否异常都执行（资源清理）
    print('清理完成')
```

| 子句 | 执行时机 |
|------|---------|
| `try` | 总是先执行，可能抛异常 |
| `except` | 仅在 try 抛出匹配异常时执行 |
| `else` | 仅在 try 没抛异常时执行 |
| `finally` | **总是执行**（有无异常都执行） |

> `else` 的意义：把「成功后逻辑」与「可能出错的代码」分开，避免 `else` 里的代码也被 `except` 误捕获。

### 3. 捕获多种异常

```python
# 一个 except 捕获多种类型，用元组
except (TypeError, ValueError, KeyError) as e:
    print(f'出错: {type(e).__name__}: {e}')

# 多个 except 分支，从具体到通用
except FileNotFoundError:
    print('文件不存在')
except PermissionError:
    print('无权限')
except OSError as e:        # 上面两个的父类，放后面兜底
    print(f'其他 OS 错误: {e}')
```

> **顺序原则**：具体异常在前，通用异常（父类）在后，否则父类会先匹配。

### 4. 异常类型层级

```
BaseException
├── SystemExit                 ← sys.exit() 触发
├── KeyboardInterrupt          ← Ctrl+C
└── Exception                  ← 所有常规异常的基类
    ├── ValueError             ← 值错误（int('abc')）
    ├── TypeError              ← 类型错误（1 + 'a'）
    ├── KeyError               ← 字典键不存在
    ├── IndexError             ← 索引越界
    ├── AttributeError         ← 属性不存在
    ├── ZeroDivisionError      ← 除以零
    ├── StopIteration          ← 迭代器耗尽
    ├── ImportError            ← 导入失败
    │   └── ModuleNotFoundError
    ├── NameError              ← 名字未定义
    ├── RuntimeError
    │   └── RecursionError
    ├── OSError                ← 系统相关错误（文件/权限等）
    │   ├── FileNotFoundError
    │   ├── FileExistsError
    │   ├── PermissionError
    │   ├── IsADirectoryError
    │   └── TimeoutError
    └── ArithmeticError
        ├── ZeroDivisionError
        └── OverflowError
```

### 5. `raise` 主动抛出异常

```python
def set_price(price: float) -> None:
    if price < 0:
        raise ValueError(f'价格不能为负: {price}')
    if not isinstance(price, (int, float)):
        raise TypeError(f'价格必须是数字, 收到 {type(price).__name__}')

set_price(-10)    # 抛 ValueError
```

### 6. 自定义异常

继承 `Exception` 建立异常体系：

```python
class EshopError(Exception):
    """电商业务异常基类"""
    pass

class ProductNotFoundError(EshopError):
    """商品不存在"""
    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(f'商品 {product_id} 不存在')

class InvalidPriceError(EshopError):
    """价格非法"""
    pass

# 使用
def get_product(pid: int):
    if pid not in PRODUCTS:
        raise ProductNotFoundError(pid)
```

> 自定义异常继承 `Exception`（而非 `BaseException`），确保不会被 `sys.exit`/`KeyboardInterrupt` 干扰。

### 7. 异常链 `raise ... from`

用 `raise NewError from original` 保留原始异常的因果链：

```python
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    # 包装成业务异常，但保留原始异常
    raise InvalidDataError('商品数据格式错误') from e
```

`__cause__` 属性会保存原始异常，打印堆栈时显示：

```
InvalidDataError: 商品数据格式错误

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  ...
JSONDecodeError: ...
```

### 8. `assert` 断言

```python
assert price >= 0, f'价格不能为负: {price}'   # 条件为 False 时抛 AssertionError
```

> **断言不是错误处理**：`assert` 用于开发期调试不变式，可用 `python -O` 禁用所有 assert。生产代码的错误校验应直接 `raise`，不要用 `assert`。

### 9. 异常处理最佳实践

| ❌ 反模式 | ✅ 正确做法 |
|----------|-----------|
| `except:` 裸捕获 | `except SpecificError as e:` 指定类型 |
| `except: pass` 吞异常 | 记录日志或重新抛出 |
| `except Exception: print(e)` 只打印 | 用 `logging.exception` 记录堆栈 |
| 父类在前 | 具体异常在前，通用在后 |
| 用异常做正常流程控制 | 异常用于异常情况，正常分支用 if |
| `finally` 里写业务逻辑 | `finally` 只做资源清理 |

```python
import logging
logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except (ValueError, KeyError) as e:
    logger.exception('数据处理失败')   # 自动带堆栈
    raise                              # 重新抛出，让上层决定
else:
    save_result(result)
finally:
    cleanup()                          # 资源清理
```

---

## 代码文件说明

| 文件 | 用途 |
|------|------|
| `Code/file_io.py` | 文件 IO 练习：open 读写、with 语句、逐行读取大文件、pathlib 读写；电商场景：读写商品列表、日志追加 |
| `Code/json_csv.py` | JSON 与 CSV 读写：dump/load、DictReader/DictWriter；电商场景：商品导出 JSON、订单导出 CSV、从 CSV 导入 |
| `Code/pathlib_demo.py` | pathlib 路径操作：拼接、exists/is_file/mkdir/glob/rglob；电商场景：遍历数据目录、查找 JSON 文件 |
| `Code/exception_handling.py` | 异常处理：try/except/else/finally、多种异常、异常层级；电商场景：文件不存在、JSON 解析错、类型转换错 |
| `Code/custom_exceptions.py` | 自定义异常体系：EshopError 基类及 4 个子类、`raise from` 异常链 |

**运行方式**：

```bash
cd "Day10 - 文件IO与异常处理/Code"
python file_io.py
python json_csv.py
python pathlib_demo.py
python exception_handling.py
python custom_exceptions.py
```

> 示例脚本会在当前目录创建 `data/` 等临时数据文件用于演示，可运行后查看。

---

## 关键知识点总结

### 文件模式速查表

| 模式 | 读 | 写 | 创建 | 覆盖 | 二进制 | 说明 |
|------|----|----|------|------|--------|------|
| `r` | ✅ | ❌ | ❌ | - | ❌ | 默认只读 |
| `w` | ❌ | ✅ | ✅ | ✅ | ❌ | 覆盖写 |
| `a` | ❌ | ✅ | ✅ | ❌(追加) | ❌ | 追加写 |
| `r+` | ✅ | ✅ | ❌ | ❌ | ❌ | 读写 |
| `x` | ❌ | ✅ | ✅ | ❌(报错) | ❌ | 独占创建 |
| `rb` | ✅ | ❌ | ❌ | - | ✅ | 二进制读 |
| `wb` | ❌ | ✅ | ✅ | ✅ | ✅ | 二进制写 |
| `ab` | ❌ | ✅ | ✅ | ❌(追加) | ✅ | 二进制追加 |

### JSON 方法速查

| 方法 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `dumps(obj)` | Python 对象 | str | 序列化为字符串 |
| `loads(s)` | str | Python 对象 | 反序列化字符串 |
| `dump(obj, f)` | Python 对象 | 文件 | 写入文件 |
| `load(f)` | 文件 | Python 对象 | 读取文件 |

常用参数：`ensure_ascii=False`（保留中文）、`indent=2`（美化）、`default=fn`（自定义序列化）、`sort_keys=True`（键排序）。

### 异常层级图

```
BaseException
├── SystemExit / KeyboardInterrupt        （不要捕获）
└── Exception                            （自定义异常继承这里）
    ├── ValueError / TypeError / KeyError / IndexError
    ├── AttributeError / NameError / StopIteration
    ├── ImportError → ModuleNotFoundError
    ├── OSError → FileNotFoundError / PermissionError / FileExistsError
    ├── ArithmeticError → ZeroDivisionError / OverflowError
    └── RuntimeError → RecursionError
```

### 异常处理最佳实践清单

1. ✅ 指定具体异常类型，不要裸 `except:`
2. ✅ 不要 `except: pass` 吞掉异常
3. ✅ 用 `logging.exception` 记录，而非 `print`
4. ✅ 具体异常在前，通用（父类）在后
5. ✅ `finally` 只做资源清理，不放业务逻辑
6. ✅ 无法处理的异常 `raise` 向上传播
7. ✅ 自定义异常继承 `Exception`
8. ✅ 包装异常用 `raise New from old` 保留因果链
9. ❌ 不要用异常做正常流程控制
10. ❌ 不要用 `assert` 做生产参数校验

---

## 实战练习

### 练习 1：商品库存日志分析器

写一个脚本，模拟生成 1000 行库存变更日志（每行格式 `时间|商品ID|变更数量`），写入 `inventory.log`。然后逐行读取，统计每个商品的净变更量，输出库存预警（变更后库存 < 10 的商品）。要求用 `with` 语句和逐行读取。

### 练习 2：JSON 与 CSV 双格式转换

写一个工具，支持：
- 把 `products.json` 转成 `products.csv`
- 把 `orders.csv` 转成 `orders.json`

要求处理中文（`ensure_ascii=False`），用 `try/except` 捕获文件不存在和 JSON 解析错误，给出友好提示。

### 练习 3：电商订单导入与异常体系

扩展 `custom_exceptions.py`，实现一个 `import_orders(csv_path)` 函数：
- 读取 CSV 订单文件
- 对每行做校验：金额必须为正数、客户名非空、商品 ID 必须存在
- 校验失败抛出对应自定义异常（`InvalidPriceError` / `InvalidCustomerError` / `ProductNotFoundError`）
- 用 `raise from` 保留原始异常链
- 收集所有错误后统一报告，而非遇到第一个错误就停
