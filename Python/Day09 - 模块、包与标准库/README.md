# Day09 - 模块、包与标准库

模块和包是组织 Python 代码的基本单元：一个 `.py` 文件就是一个模块，一个含 `__init__.py` 的目录就是一个包。标准库则是 Python 自带的超级武器——从文件操作、路径处理、JSON/CSV 解析到命令行参数解析、日志、正则，几乎覆盖了日常工程的全部基础设施。本 Day 将系统梳理 import 机制、包结构设计，并精选 20+ 标准库模块逐一演示，为后面的 eshop CLI 工具打地基。

---

## 学习目标

- 理解模块与包的概念，掌握 5 种 import 写法及其差异
- 理解 `__name__ == '__main__'` 的执行机制
- 掌握 `__init__.py` 与 `__all__` 的作用，能设计规范的包结构
- 区分绝对导入与相对导入，理解 `.` 与 `..` 的含义
- 精通 pathlib、json、csv、datetime、collections、argparse 等高频标准库
- 了解 itertools、functools、re、subprocess、logging、hashlib 等进阶库
- 能用 argparse 开发一个电商 CLI 工具（含子命令）
- 掌握 src 布局与 flat 布局的取舍

---

## 理论知识讲解

### 1. 模块概念

**一个 `.py` 文件就是一个模块，模块名就是文件名（去掉 `.py`）**。

```
math_utils.py   →   模块名 math_utils
```

模块的好处：
- 代码复用：把通用逻辑抽到模块，多处导入
- 命名空间隔离：不同模块里同名变量互不冲突
- 可维护性：按功能拆分文件，避免单文件膨胀

### 2. import 语法

Python 提供 5 种 import 写法，各有适用场景：

| 写法 | 示例 | 说明 | 推荐 |
|------|------|------|------|
| `import module` | `import os` | 导入整个模块，用 `os.path` 访问 | ✅ 推荐 |
| `from module import name` | `from os import path` | 导入具体对象，直接用 `path` | ✅ 常用 |
| `from module import name as alias` | `import numpy as np` | 起别名，避免冲突或简化 | ✅ 推荐 |
| `import module as alias` | `import pandas as pd` | 给整个模块起别名 | ✅ 常用 |
| `from module import *` | `from os import *` | 导入全部公开名 | ❌ 不推荐 |

```python
import os                              # 写法1
from os import path, getenv            # 写法2
from os import path as p               # 写法3
import numpy as np                     # 写法4
from os import *                       # 写法5（污染命名空间，禁止）
```

> **为什么禁止 `import *`**：会把模块里所有非下划线开头的名字全倒进当前命名空间，容易覆盖已有变量，且无法追踪名字来源。PEP 8 明确反对。

### 3. `__name__ == '__main__'`

每个模块都有一个 `__name__` 属性：
- **直接运行**该文件时，`__name__` 等于 `'__main__'`
- **被导入**时，`__name__` 等于模块名

```python
# greet.py
def hello():
    print("Hello from module")

if __name__ == '__main__':
    # 只有直接运行 greet.py 才执行
    # 被 import 时不执行，避免副作用
    hello()
```

这个写法的意义：让模块既能被导入复用，又能作为脚本独立运行测试。

### 4. 包与 `__init__.py`

**包是包含 `__init__.py` 的目录**，用来组织多个模块。

```
eshop/                  ← 包（目录）
├── __init__.py         ← 包标识文件
├── models/             ← 子包
│   ├── __init__.py
│   └── product.py      ← 模块
└── services/
    ├── __init__.py
    └── analytics.py
```

`__init__.py` 的作用：
1. **标识目录是包**（Python 3.3+ 可省略，但建议保留）
2. **执行包级初始化代码**（导入包时自动执行一次）
3. **用 `__all__` 控制 `from package import *` 的导出**
4. **简化对外接口**：在 `__init__.py` 里 `from .product import Product`，用户只需 `from eshop.models import Product`

```python
# eshop/models/__init__.py
from .product import Product
from .order import Order
from .customer import Customer

__all__ = ['Product', 'Order', 'Customer']
```

> **命名空间包**（namespace package）：3.3+ 支持没有 `__init__.py` 的包，可跨多个目录分布。但普通项目用普通包即可。

### 5. 相对导入 vs 绝对导入

| 类型 | 写法 | 说明 |
|------|------|------|
| 绝对导入 | `from eshop.models.product import Product` | 从项目根开始，路径完整清晰 |
| 相对导入 | `from .product import Product` | `.` 表示当前包 |
| 相对导入 | `from ..utils import helper` | `..` 表示上一级包 |

`.` 和 `..` 的含义：
- `.` = 当前包（当前 `__init__.py` 所在目录）
- `..` = 上一级包
- `...` = 上上一级包（少见）

```python
# eshop/services/analytics.py

# 绝对导入（推荐，清晰且工具友好）
from eshop.models.product import Product
from eshop.utils.decorators import timer

# 相对导入（包内部紧密模块间可用，但只能用在包内，不能用作顶层脚本）
from ..models.product import Product
from ..utils.decorators import timer
```

> **推荐用绝对导入**：可读性强、IDE 跳转友好、不易出错。相对导入仅限包内部、且不能用作 `python xxx.py` 直接运行的顶层脚本（会报 `ImportError: attempted relative import with no known parent package`）。

### 6. 标准库精选

Python 标准库极其丰富，下面按模块逐一演示。

#### 6.1 os —— 操作系统接口

```python
import os

# 环境变量
os.environ.get('HOME')              # 获取，不存在返回 None
os.environ.get('FOO', 'default')    # 带默认值
os.environ['MY_VAR'] = 'value'      # 设置

# 路径操作（推荐改用 pathlib）
os.path.join('a', 'b', 'c.py')      # 'a/b/c.py'（跨平台）
os.path.exists('/tmp/x')            # 是否存在
os.path.dirname('/a/b/c.py')        # '/a/b'
os.path.basename('/a/b/c.py')       # 'c.py'
os.path.splitext('c.py')            # ('c', '.py')

# 文件操作
os.remove('tmp.txt')                # 删除文件
os.rename('a.txt', 'b.txt')         # 重命名
os.makedirs('a/b/c', exist_ok=True) # 递归建目录

# 执行命令（推荐改用 subprocess）
os.system('echo hello')             # 返回退出码
```

#### 6.2 sys —— 解释器相关

```python
import sys

sys.argv          # 命令行参数列表，argv[0] 是脚本名
sys.path          # 模块搜索路径列表
sys.exit(0)       # 退出程序，0 表示正常
sys.stdin         # 标准输入
sys.stdout        # 标准输出
sys.stderr        # 标准错误
sys.platform      # 'win32' / 'linux' / 'darwin'
sys.version       # Python 版本字符串
```

#### 6.3 pathlib（推荐替代 os.path）

面向对象的路径操作，**现代 Python 首选**：

```python
from pathlib import Path

p = Path('data') / 'products.json'   # / 运算符拼接路径
p = Path.cwd()                       # 当前工作目录
p = Path.home()                      # 用户主目录

p.exists()                           # 是否存在
p.is_file()                          # 是否文件
p.is_dir()                           # 是否目录
p.name                               # 'products.json'
p.stem                               # 'products'
p.suffix                             # '.json'
p.parent                             # 父目录

p.mkdir(parents=True, exist_ok=True) # 建目录
p.read_text(encoding='utf-8')        # 读文本
p.write_text('hello', encoding='utf-8')  # 写文本
p.read_bytes()                       # 读字节

list(p.parent.glob('*.json'))        # 匹配当前目录
list(p.parent.rglob('*.json'))       # 递归匹配
```

#### 6.4 json —— JSON 读写

```python
import json

# 字符串 ↔ 对象
json.dumps({'a': 1, 'b': '中文'})            # 序列化为字符串
json.loads('{"a": 1}')                       # 反序列化为对象

# 文件 ↔ 对象
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(obj, f, ensure_ascii=False, indent=2)  # 写文件
with open('data.json', encoding='utf-8') as f:
    obj = json.load(f)                                # 读文件
```

> **中文陷阱**：`dumps` 默认 `ensure_ascii=True`，会把中文转成 `\uXXXX`。处理中文一定要 `ensure_ascii=False`。

#### 6.5 csv —— CSV 读写

```python
import csv

# 写
with open('orders.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'total'])
    writer.writeheader()
    writer.writerow({'id': 1, 'total': 99.5})

# 读（推荐 DictReader，返回字典）
with open('orders.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['id'], row['total'])
```

#### 6.6 datetime —— 日期时间

```python
from datetime import datetime, date, time, timedelta, timezone

now = datetime.now()                          # 本地现在
utc = datetime.now(timezone.utc)              # UTC 现在
dt = datetime(2026, 7, 30, 10, 30, 0)

dt.strftime('%Y-%m-%d %H:%M:%S')              # 格式化为字符串
datetime.strptime('2026-07-30', '%Y-%m-%d')   # 字符串解析为 datetime

delta = timedelta(days=7)
tomorrow = date.today() + timedelta(days=1)
```

#### 6.7 collections —— 容器扩展

```python
from collections import namedtuple, defaultdict, Counter, deque, OrderedDict

Point = namedtuple('Point', ['x', 'y'])       # 命名元组
p = Point(1, 2); p.x, p.y

dd = defaultdict(list)                        # 缺键自动建默认值
dd['a'].append(1)

c = Counter('aabbbcccc')                      # 计数器
c.most_common(2)                              # [('c', 4), ('b', 3)]

dq = deque([1, 2, 3])                         # 双端队列
dq.appendleft(0); dq.popleft()
```

#### 6.8 random —— 随机数

```python
import random

random.random()                # [0.0, 1.0) 浮点
random.randint(1, 100)         # [1, 100] 整数
random.choice(['a', 'b', 'c']) # 随机选一个
random.choices([1,2,3], k=5)   # 有放回抽样 5 个
random.sample(range(100), 5)   # 无放回抽样 5 个
random.shuffle(my_list)        # 原地打乱
random.seed(42)                # 固定种子，结果可复现
```

#### 6.9 math —— 数学

```python
import math

math.ceil(3.2)        # 4   向上取整
math.floor(3.8)       # 3   向下取整
math.sqrt(16)         # 4.0
math.pi, math.e       # 3.14159..., 2.71828...
math.factorial(5)     # 120
math.gcd(12, 18)      # 6
math.log(100, 10)     # 2.0
```

#### 6.10 itertools —— 迭代器工具

```python
from itertools import chain, combinations, permutations, product, groupby, islice, count, cycle, repeat, accumulate

list(chain([1,2], [3,4]))               # [1,2,3,4] 串联
list(combinations('ABC', 2))            # 排列组合 C(3,2)
list(permutations('ABC', 2))            # 排列 P(3,2)
list(product('AB', '12'))               # 笛卡尔积
list(islice(count(1), 5))               # [1,2,3,4,5] 切片无限序列
list(accumulate([1,2,3,4]))             # [1,3,6,10] 累积
```

> Day12 会详解 itertools，本节先建立印象。

#### 6.11 functools —— 函数工具

```python
from functools import reduce, partial, lru_cache, wraps, cached_property

reduce(lambda x, y: x + y, [1,2,3,4])   # 10 累积
add5 = partial(lambda a, b: a + b, 5)   # 偏函数，固定 b=5

@lru_cache(maxsize=128)
def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)
fib.cache_info()                        # 查看命中情况
```

> Day11 详解装饰器与 `lru_cache`。

#### 6.12 re —— 正则表达式

```python
import re

re.match(r'\d+', '123abc')             # 从头匹配
re.search(r'\d+', 'abc123')            # 搜索任意位置
re.findall(r'\d+', 'a1b22c333')        # 找全部 ['1','22','333']
re.sub(r'\d+', '#', 'a1b22')           # 替换 'a#b#'
re.split(r'[,;]', 'a,b;c')             # 分割 ['a','b','c']

p = re.compile(r'(\w+)@(\w+)\.(\w+)')  # 预编译，分组
m = p.search('email me at tom@a.com')
m.group(0), m.group(1)                 # 'tom@a.com', 'tom'

# 贪婪 vs 非贪婪
re.search(r'<.*>', '<a><b>')           # 贪婪 '<a><b>'
re.search(r'<.*?>', '<a><b>')          # 非贪婪 '<a>'
```

#### 6.13 subprocess —— 调用外部命令

```python
import subprocess

# 推荐写法：run，捕获输出
result = subprocess.run(['git', 'status'], capture_output=True, text=True)
result.returncode    # 退出码
result.stdout        # 标准输出
result.stderr        # 标准错误

# 简便取输出
out = subprocess.check_output(['python', '--version'], text=True)
```

#### 6.14 shutil —— 高级文件操作

```python
import shutil

shutil.copy('a.txt', 'b.txt')              # 复制（不含元数据）
shutil.copy2('a.txt', 'b.txt')             # 复制（保留元数据）
shutil.copytree('src/', 'dst/')            # 复制整个目录
shutil.rmtree('dst/')                      # 删除整个目录
shutil.move('a.txt', 'dir/a.txt')          # 移动
shutil.make_archive('backup', 'zip', 'src/')  # 打包
```

#### 6.15 tempfile —— 临时文件

```python
import tempfile

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('临时数据')
    print(f.name)                          # 临时文件路径

with tempfile.TemporaryDirectory() as d:
    print(d)                               # 临时目录，退出 with 自动删除
```

#### 6.16 logging —— 日志

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    filename='app.log',
)
logger = logging.getLogger('eshop')

logger.debug('调试信息')      # 默认不输出（级别低于 INFO）
logger.info('商品已上架')
logger.warning('库存不足')
logger.error('订单失败')
logger.exception('出错了')    # 自动附带异常堆栈
```

#### 6.17 argparse —— 命令行工具

```python
import argparse

parser = argparse.ArgumentParser(description='eshop CLI')
parser.add_argument('--product', help='商品名称')
parser.add_argument('--limit', type=int, default=10)
args = parser.parse_args()
print(args.product, args.limit)
```

> 详见本章 `argparse_demo.py`，包含子命令开发。

#### 6.18 copy —— 浅拷贝与深拷贝

```python
import copy

lst = [[1, 2], [3, 4]]
shallow = copy.copy(lst)       # 浅拷贝：外层新对象，内层共享引用
deep = copy.deepcopy(lst)      # 深拷贝：完全独立副本

shallow[0][0] = 99             # 会影响原 lst！
deep[0][0] = 99                # 不影响原 lst
```

#### 6.19 hashlib —— 哈希

```python
import hashlib

hashlib.md5(b'hello').hexdigest()           # 5d41402a...（不安全，别用于密码）
hashlib.sha256(b'hello').hexdigest()        # 推荐，64 位十六进制
hashlib.sha512(b'hello').hexdigest()

# 文件哈希
h = hashlib.sha256()
with open('big.bin', 'rb') as f:
    for chunk in iter(lambda: f.read(8192), b''):
        h.update(chunk)
print(h.hexdigest())
```

#### 6.20 typing —— 类型注解

```python
from typing import List, Dict, Tuple, Optional, Union, Any, Callable

def process(items: List[int]) -> Dict[str, int]: ...
def find(x: int, items: Optional[List[int]] = None) -> Union[int, None]: ...
def apply(fn: Callable[[int], int], x: int) -> int: ...
```

> Day14 会详讲 typing，本节先了解。

### 7. `__all__` 控制导出

`__all__` 是一个列表，控制 `from module import *` 时导出哪些名字：

```python
# module_demo/__init__.py
from .math_utils import add, multiply
from .string_utils import upper, lower

__all__ = ['add', 'multiply', 'upper', 'lower']
```

即使模块里还有别的公开名，`import *` 也只会导入 `__all__` 列出的。这是声明「公开 API」的标准方式。

### 8. 第三方库安装

```bash
pip install requests               # 安装最新版
pip install requests==2.31.0       # 指定版本
pip install "requests>=2.30,<3"    # 版本范围
pip install -r requirements.txt    # 批量安装
pip uninstall requests             # 卸载
pip list                           # 已安装列表
pip show requests                  # 包详情
```

**PyPI**（Python Package Index，pypi.org）是 Python 官方包仓库，`pip install` 默认从这里下载。所有第三方库发布到 PyPI 后，全世界都能用 `pip` 安装。

### 9. 包结构设计最佳实践

#### src 布局 vs flat 布局

```
flat 布局（不推荐用于正式项目）：
myproject/
├── eshop/          ← 包直接在根
│   └── __init__.py
└── tests/

src 布局（推荐）：
myproject/
├── src/
│   └── eshop/      ← 包放在 src 下
│       └── __init__.py
└── tests/
```

| 对比项 | flat 布局 | src 布局 |
|--------|-----------|----------|
| 简单程度 | 简单，适合脚本 | 稍复杂，适合正式包 |
| 测试隔离 | 测试可能误导入当前目录的包 | 强制以安装版测试，更可靠 |
| 发布 | 容易误打包无关文件 | 打包边界清晰 |
| 适用 | 小脚本、学习项目 | 库、可发布应用 |

> **eshop 项目采用 src 布局**，见总 README 的项目结构图。

---

## 代码文件说明

| 文件 | 用途 |
|------|------|
| `Code/module_demo/__init__.py` | 包标识，用 `__all__` 控制导出，对外暴露简洁接口 |
| `Code/module_demo/math_utils.py` | 数学工具函数（add/multiply/factorial 等） |
| `Code/module_demo/string_utils.py` | 字符串工具函数（upper/lower/reverse 等） |
| `Code/module_demo/__main__.py` | `python -m module_demo` 的执行入口，演示 `__name__` 机制 |
| `Code/stdlib_examples.py` | 标准库精选示例（os/sys/pathlib/json/datetime/collections/random/math） |
| `Code/argparse_demo.py` | eshop CLI 工具演示，含 `--product/--order/--export` 与子命令 subparsers |

**运行方式**：

```bash
cd "Day09 - 模块、包与标准库/Code"

# 1. 以模块方式运行包
python -m module_demo

# 2. 运行标准库示例
python stdlib_examples.py

# 3. 运行 CLI 工具
python argparse_demo.py --help
python argparse_demo.py product list
python argparse_demo.py product search --name 手机
python argparse_demo.py order stats --top 3
python argparse_demo.py export --format json --output out.json
```

---

## 关键知识点总结

### import 语法速查表

| 写法 | 示例 | 适用 |
|------|------|------|
| 导入模块 | `import os` | 用 `os.path` 访问 |
| 导入对象 | `from os import path` | 直接用 `path` |
| 模块别名 | `import numpy as np` | 约定俗成别名 |
| 对象别名 | `from os import path as p` | 避免冲突 |
| 通配导入 | `from os import *` | ❌ 禁止 |
| 包内相对 | `from . import sibling` | 包内部模块 |
| 包内向上 | `from ..pkg import mod` | 上一级包 |

### 标准库分类速查表

| 分类 | 模块 | 高频用途 |
|------|------|---------|
| 路径文件 | `pathlib`, `os`, `os.path` | 路径拼接、判断、读写 |
| 数据序列化 | `json`, `csv` | 配置、数据导入导出 |
| 时间 | `datetime`, `time` | 时间戳、格式化 |
| 容器 | `collections` | Counter/defaultdict/deque |
| 数学 | `math`, `random`, `statistics` | 运算、随机、统计 |
| 迭代 | `itertools`, `functools` | 组合、累积、缓存 |
| 文本 | `re`, `string` | 正则、字符串常量 |
| 系统 | `sys`, `os`, `subprocess` | 参数、环境、外部命令 |
| 文件操作 | `shutil`, `tempfile` | 复制目录、临时文件 |
| 日志 | `logging` | 分级日志 |
| 命令行 | `argparse` | CLI 开发 |
| 哈希 | `hashlib` | 校验、指纹 |
| 拷贝 | `copy` | 浅/深拷贝 |
| 类型 | `typing` | 类型注解 |

### 包结构最佳实践图

```
src 布局（推荐）
─────────────────────────────
project/
├── src/
│   └── eshop/
│       ├── __init__.py        ← __all__ 控制导出
│       ├── __main__.py        ← python -m eshop 入口
│       ├── models/
│       │   ├── __init__.py    ← 对外暴露 Product/Order/Customer
│       │   └── product.py
│       └── utils/
│           └── fileio.py
├── tests/                     ← 测试在 src 外，强制以安装版测试
└── pyproject.toml
─────────────────────────────
导入约定：
  对外用绝对导入：from eshop.models.product import Product
  包内部可用相对导入：from ..utils.fileio import read_json
  __init__.py 里聚合子模块：from .product import Product
```

---

## 实战练习

### 练习 1：标准库速查卡

写一个脚本 `cheatsheet.py`，用 `collections.Counter` 统计一段电商文案中每个词的出现频率，用 `itertools.islice` 取前 5 个高频词，用 `datetime` 记录生成时间，用 `json` 把结果写到 `cheatsheet.json`（`ensure_ascii=False`，`indent=2`）。

### 练习 2：扩展 eshop CLI

在 `argparse_demo.py` 基础上新增子命令 `customer`，支持：
- `customer list` 列出客户
- `customer add --name 张三 --email zhangsan@a.com` 添加客户
- `customer find --id 1` 查找客户

要求用 `pathlib` 管理数据文件，用 `json` 持久化客户列表到 `customers.json`。

### 练习 3：包结构重构

把本章 `module_demo` 包重构成如下结构，并保证所有导入都能正常工作：

```
eshop/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── product.py
└── utils/
    ├── __init__.py
    ├── math_utils.py
    └── string_utils.py
```

要求：
- `eshop/__init__.py` 用 `__all__` 只暴露 `Product` 类
- `models/product.py` 用绝对导入引用 `eshop.utils.math_utils`
- `utils/math_utils.py` 和 `string_utils.py` 从原 `module_demo` 迁移
- 写一个 `__main__.py` 让 `python -m eshop` 能跑起来
