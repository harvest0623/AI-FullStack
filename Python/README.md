# Python 学习指南

> 系统化掌握 Python 编程核心能力，为 AI/ML、数据分析与后端开发奠定语言基础

> 共 15 天，覆盖从环境搭建、语法基础、面向对象到并发编程与元编程的完整知识体系

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [学习路线图](#学习路线图)
- [示例项目](#示例项目)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

本板块是全栈学习系列的**通用编程语言基石**。Python 是全球最流行的编程语言之一（TIOBE 长期前三），凭借简洁的语法和强大的生态，横跨 AI/ML、数据分析、Web 后端、自动化脚本、DevOps 运维等领域。掌握 Python 意味着打开了从传统后端到 AI 全栈的大门。

**与 TypeScript 板块的关系**：TypeScript 让你理解了类型系统和面向对象思想，Python 用更简洁的语法再次印证这些概念，同时引入动态语言的灵活性。两者在类型注解上有异曲同工之妙——Python 3.5+ 的 type hints 正是向静态类型靠拢。

**学习目标**：完成本板块后，你应能：
- 熟练使用 Python 语法完成日常编程任务
- 理解 Python 数据模型（万物皆对象、魔术方法）
- 用面向对象思想设计程序结构
- 用装饰器、生成器、上下文管理器编写 Pythonic 代码
- 用模块和包组织项目结构
- 掌握文件 IO、异常处理、类型注解
- 理解 GIL 并用多线程/协程处理并发
- 用 venv/pip/poetry 管理项目依赖

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行代码 + 实战练习
- 全程围绕统一的**电商数据处理 CLI 工具**项目展开
- 所有代码可在 Python 3.10+ 直接运行
- 紧扣 AI 全栈视角，为后续 LLM/RAG/Agent 板块铺垫

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 编程基础 | 了解即可 | 有任意语言经验（JS/TS 更好），理解变量、条件、循环 |
| 命令行操作 | 基础 | 能在终端执行命令 |
| TypeScript 板块 | 已完成更好 | 类型系统、OOP、泛型概念可迁移 |

**环境准备**：
- Python 3.10+（推荐 3.12，本板块以 3.10+ 为基准）
- 代码编辑器：VS Code（安装 Python 扩展）或 PyCharm
- 可选：Docker（用容器隔离 Python 环境）

---

## 学习路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python 学习路线（15天）                       │
└─────────────────────────────────────────────────────────────────┘

阶段一：语法基础（Day01-Day05）
┌────────┬────────┬────────┬────────┬────────┐
│Day01   │Day02   │Day03   │Day04   │Day05   │
│环境搭建│变量与  │运算符  │字符串  │元组字典│
│        │数据类型│与控制流│与列表  │与集合  │
└───┬────┴───┬────┴───┬────┴───┬────┴───┬────┘
    │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼
阶段二：函数与面向对象（Day06-Day08）
┌────────────────┬────────────────┬────────────────┐
│  Day06 函数与  │  Day07 OOP基础 │  Day08 OOP进阶 │
│  Lambda        │                │                │
└───────┬────────┴───────┬────────┴───────┬────────┘
        │                │                │
        ▼                ▼                ▼
阶段三：工程化（Day09-Day12）
┌────────┬────────┬────────┬────────┐
│Day09   │Day10   │Day11   │Day12   │
│模块包  │文件IO  │装饰器  │迭代器  │
│标准库  │异常    │生成器  │上下文  │
└───┬────┴───┬────┴───┬────┴───┬────┘
    │        │        │        │
    ▼        ▼        ▼        ▼
阶段四：进阶与生态（Day13-Day15）
┌────────────────┬────────────────┬────────────────┐
│  Day13 并发编程 │  Day14 类型注解│  Day15 包管理   │
│  多线程/协程    │  与元编程      │  与虚拟环境     │
└────────────────┴────────────────┴────────────────┘
```

---

## 示例项目

本板块全程围绕一个**电商数据处理 CLI 工具 `eshop`** 展开，逐步用所学知识构建完整项目。

### 项目结构

```
eshop/
├── pyproject.toml              ← 项目配置（Day15）
├── README.md
├── src/
│   └── eshop/
│       ├── __init__.py
│       ├── cli.py              ← 命令行入口
│       ├── models/             ← 数据模型（Day07-08 OOP）
│       │   ├── product.py      ← 商品模型
│       │   ├── order.py        ← 订单模型
│       │   └── customer.py     ← 客户模型
│       ├── services/           ← 业务逻辑（Day06 函数）
│       │   ├── analytics.py     ← 数据分析
│       │   ├── report.py        ← 报告生成
│       │   └── export.py        ← 数据导出
│       ├── utils/              ← 工具函数（Day11-12 装饰器/上下文）
│       │   ├── decorators.py    ← 装饰器集合
│       │   ├── timer.py         ← 计时器
│       │   └── fileio.py        ← 文件读写
│       └── data/                ← 示例数据
│           ├── products.json
│           └── orders.csv
├── tests/                      ← 测试
└── scripts/                     ← 运维脚本
```

### 数据模型示例

```python
# 商品模型
@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int
    category: str

# 订单模型
@dataclass
class Order:
    id: int
    customer_id: int
    items: list[OrderItem]
    total: float
    status: OrderStatus
    created_at: datetime
```

> 各天的代码围绕这个项目逐步构建，从简单脚本演进为完整工程。

---

## 每日内容详表

### 阶段一：语法基础

#### Day01 - Python基础与环境搭建
- **核心**：Python 简介与定位、Python 2 vs 3、版本管理（pyenv）、安装、REPL 交互式解释器、pip 包管理器、venv 虚拟环境、VS Code 配置、第一个 Python 程序、print/input、代码风格 PEP 8、注释、执行方式（python file.py / python -m）
- **代码**：`hello.py` / `basics.py` / `README.md`（环境配置指南）
- **重点**：搭建可运行环境，理解 Python 执行模型

#### Day02 - 变量与数据类型
- **核心**：变量赋值与命名规则、动态类型、多变量赋值、基本数据类型（int/float/bool/str/None）、类型转换（int()/float()/str()/bool()）、type() 与 isinstance()、数字类型详解（整数精度、浮点数陷阱、Decimal）、布尔值与真值测试（Falsy/Truthy）、None 与空值、变量作用域预告、字符串预览
- **代码**：`variables.py` / `data_types.py` / `type_conversion.py`
- **重点**：动态类型与类型安全、浮点数精度问题

#### Day03 - 运算符与控制流
- **核心**：算术运算符（+ - * / // % **）、比较运算符、逻辑运算符（and/or/not）、赋值运算符（+= -= := 海象运算符）、位运算符、成员运算符（in/not in）、身份运算符（is/is not vs ==）、运算符优先级、if/elif/else、条件表达式（三元运算符）、match-case（3.10+ 模式匹配）、for 循环、while 循环、range()、break/continue/else 子句、pass、enumerate()、zip()
- **代码**：`operators.py` / `if_else.py` / `loops.py` / `match_case.py`
- **重点**：海象运算符、for-else、match-case 模式匹配

#### Day04 - 字符串与列表
- **核心**：
  - 字符串：创建（引号/三引号）、索引与切片、格式化（% / .format() / f-string）、常用方法（upper/lower/strip/split/join/replace/find/count/startswith/endswith/center/ljust/rjust/zfill）、字符串不可变性、encode/decode、原始字符串 r""、正则表达式预览（re模块简介）
  - 列表：创建、索引与切片、增删改（append/extend/insert/remove/pop/del/clear）、查找（in/index/count）、排序（sort/sorted/reverse）、列表推导式（[x for x in range(10)]）、嵌套列表、列表复制（浅拷贝 vs 深拷贝）、列表解包
- **代码**：`strings.py` / `string_methods.py` / `lists.py` / `list_comprehension.py`
- **重点**：f-string 格式化、列表推导式、浅拷贝 vs 深拷贝

#### Day05 - 元组、字典与集合
- **核心**：
  - 元组：创建、不可变性、索引切片、打包与解包、namedtuple、元组 vs 列表
  - 字典：创建、增删改查、keys/values/items、get/setdefault、字典推导式、update、pop/popitem、嵌套字典、有序字典 OrderedDict（3.7+ dict 默认有序）、 defaultdict、Counter
  - 集合：创建、增删（add/remove/discard）、集合运算（交集/并集/差集/对称差集）、集合推导式、frozenset、去重应用
  - 数据结构选择指南：何时用列表/元组/字典/集合
- **代码**：`tuples.py` / `dictionaries.py` / `sets.py` / `data_structures_comparison.py`
- **重点**：字典推导式、defaultdict/Counter、数据结构选型

---

### 阶段二：函数与面向对象

#### Day06 - 函数与Lambda
- **核心**：函数定义（def）、参数（位置参数/关键字参数/默认参数/可变参数 *args/**kwargs/仅关键字参数/仅位置参数 /）、返回值（return/多返回值/无返回值 None）、函数是一等公民（赋值/传参/返回）、Lambda 匿名函数、高阶函数（map/filter/reduce/sorted with key）、函数注解预告、递归、闭包、global/nonlocal、函数文档 docstring、type hints 初探
- **代码**：`functions.py` / `args_kwargs.py` / `lambda_higher_order.py` / `closures.py`
- **重点**：*args/**kwargs 灵活参数、闭包、高阶函数

#### Day07 - 面向对象编程(基础)
- **核心**：类与对象、class 定义、__init__ 构造器、self、实例属性与类属性、实例方法、__str__ 与 __repr__、访问控制约定（_protected/__private/名称重整）、@property 装饰器（getter/setter/deleter）、静态方法 @staticmethod、类方法 @classmethod、继承（单继承/super()、方法重写、MRO）、object 基类
- **代码**：`class_basics.py`（Product 类）/ `inheritance.py`（Order 继承）/ `property_decorator.py`
- **重点**：@property、继承与 super()、名称重整

#### Day08 - 面向对象编程(进阶)
- **核心**：多继承与 MRO（Method Resolution Order）、Mixin 模式、魔术方法（__eq__/__lt__/__hash__/__len__/__getitem__/__iter__/__contains__/__call__/__enter__/__exit__）、运算符重载、@dataclass（3.7+，简化数据类）、Enum 枚举、抽象基类 ABC（@abstractmethod）、元类 type 简介、__slots__、对象拷贝（copy.copy/copy.deepcopy）
- **代码**：`magic_methods.py`（运算符重载）/ `dataclass_enum.py` / `abc_demo.py` / `mixin_demo.py`
- **重点**：dataclass、魔术方法、ABC 抽象类

---

### 阶段三：工程化

#### Day09 - 模块、包与标准库
- **核心**：模块概念、import 语法（import module / from module import name / import as）、__name__ == '__main__'、包与 __init__.py、相对导入 vs 绝对导入、标准库精选（os/sys/pathlib/json/csv/datetime/collections/random/math/itertools/functools/re/subprocess/shutil/tempfile/logging/argparse/copy/hashlib/typing）、第三方库安装、__all__ 控制导出、包结构设计
- **代码**：`module_demo/`（包结构演示）/ `stdlib_examples.py` / `argparse_demo.py`
- **重点**：包结构设计、标准库精选实践

#### Day10 - 文件IO与异常处理
- **核心**：文件操作（open/read/write/close/with 语句）、读写模式（r/w/a/r+/wb/rb 二进制）、编码（encoding='utf-8'）、大文件逐行读取、JSON 读写（json.load/dump/load/dumps）、CSV 读写（csv模块/pandas 简介）、pathlib 面向对象路径操作、临时文件 tempfile、shutil 文件操作（copy/move/rmtree）、异常处理（try/except/else/finally）、异常类型（ValueError/TypeError/KeyError/IndexError/FileNotFoundError 等）、自定义异常、raise、异常链（from）、assert
- **代码**：`file_io.py` / `json_csv.py` / `pathlib_demo.py` / `exception_handling.py` / `custom_exceptions.py`
- **重点**：with 语句、JSON/CSV 读写、自定义异常体系

#### Day11 - 装饰器与生成器
- **核心**：
  - 装饰器：函数是一等公民回顾、装饰器概念（@语法糖）、无参装饰器、带参装饰器（三层嵌套）、functools.wraps 保留元信息、类装饰器、装饰器堆叠（执行顺序）、常用装饰器（@property/@staticmethod/@classmethod/@dataclass/functools.lru_cache/functools.wraps）、实战装饰器（计时/日志/重试/缓存/权限校验）
  - 生成器：列表推导式 vs 生成器表达式、yield 关键字、生成器函数、生成器 vs 列表（惰性求值/内存效率）、send() 与生成器交互、yield from 委托生成器、无限生成器、生成器管道（数据处理流水线）
- **代码**：`decorators.py` / `advanced_decorators.py` / `generators.py` / `generator_pipeline.py`
- **重点**：带参装饰器、lru_cache、生成器惰性求值、yield from

#### Day12 - 迭代器与上下文管理器
- **核心**：迭代协议（__iter__/__next__）、可迭代对象 Iterable vs 迭代器 Iterator、iter() 与 next()、自定义迭代器、itertools 精选（chain/combinations/permutations/product/groupby/islice/count/cycle/repeat/accumulate）、functools 精选（reduce/partial/cache/lru_cache）、上下文管理器协议（__enter__/__exit__）、contextlib（@contextmanager 装饰器/closing/suppress/redirect_stdout）、自定义上下文管理器（数据库连接/文件锁/资源管理）
- **代码**：`iterators.py` / `itertools_demo.py` / `context_manager.py` / `contextlib_demo.py`
- **重点**：迭代协议、itertools、@contextmanager

---

### 阶段四：进阶与生态

#### Day13 - 并发编程(多线程与协程)
- **核心**：并发 vs 并行、GIL（全局解释器锁）原理与影响、多线程（threading.Thread/Thread Pool/Lock/RLock/Semaphore/Event/Condition/Queue）、多进程（multiprocessing/Process/Pool/Value/Array/Queue）、线程 vs 进程选择、asyncio 异步编程（async/await/event loop/coroutine/create_task/gather/wait）、aiohttp/httpx 异步 HTTP、concurrent.futures（ThreadPoolExecutor/ProcessPoolExecutor）、何时用哪种并发模型
- **代码**：`threading_demo.py` / `multiprocessing_demo.py` / `asyncio_demo.py` / `concurrent_futures_demo.py`
- **重点**：GIL 理解、asyncio 异步编程、并发模型选型

#### Day14 - 类型注解与元编程
- **核心**：类型注解（typing 模块）、基本类型注解（int/str/float/bool/None）、复合类型（list[int]/dict[str,int]/tuple[int,...]/set[str]，3.9+ 内置泛型）、Optional/Union（3.10+ X | Y）、Callable/TypeVar/Generic/Protocol、TypeAlias/NewType、Any/Never/NoReturn、mypy 静态类型检查、pydantic 数据验证简介、元编程（元类 type/Metaclass/__new__/__init_subclass__/__class_getitem__）、描述符协议（__get__/__set__/__delete__）、dataclasses 深入（field/default_factory/frozen）
- **代码**：`type_hints.py` / `typing_advanced.py` / `metaclass_demo.py` / `descriptor_demo.py`
- **重点**：类型注解体系、Protocol、元类、描述符

#### Day15 - 包管理与虚拟环境
- **核心**：venv 虚拟环境（python -m venv / activate / deactivate）、pip 包管理（install/uninstall/freeze/list/show）、requirements.txt、pip-tools、pipenv 简介、Poetry（pyproject.toml / poetry init / add / install / build / publish）、uv（Rust 编写的高速替代）、conda 简介（数据科学场景）、__pycache__ 与字节码、Docker 打包 Python 应用、项目结构最佳实践、代码质量工具（black 格式化 / ruff 代码检查 / mypy 类型检查 / pre-commit hooks）
- **代码**：`pyproject.toml`（完整项目配置）/ `requirements.txt` / `docker/Dockerfile` / `Makefile` / `.pre-commit-config.yaml` / `README.md`（包管理指南）
- **重点**：Poetry/pyproject.toml、代码质量工具链

---

## 目录结构

```
Python/
├── README.md                              ← 本文件（板块总入口）
├── Day01 - Python基础与环境搭建/
│   ├── README.md                          ← 当天学习文档
│   └── Code/                              ← 当天 Python 代码
│       ├── hello.py
│       ├── basics.py
│       └── README.md
├── Day02 - 变量与数据类型/
│   ├── README.md
│   └── Code/
│       ├── variables.py
│       ├── data_types.py
│       └── type_conversion.py
├── ...（Day03-Day14 同构）...
└── Day15 - 包管理与虚拟环境/
    ├── README.md
    └── Code/
        ├── pyproject.toml
        ├── requirements.txt
        ├── docker/
        │   └── Dockerfile
        ├── Makefile
        ├── .pre-commit-config.yaml
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码文件统一放在 `Code/` 子文件夹内，均为 `.py` 文件（可直接 `python file.py` 运行）
- 部分天数含配置文件（`.toml` / `.yaml` / `Dockerfile` / `Makefile`）
- 部分天数含子目录结构（如 Day09 的 `module_demo/` 包）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-6 小时 | 约 2-3 周 |
| 标准 | 业余学习 | 2-3 小时 | 约 4-5 周 |
| 保守 | 碎片时间 | 1 小时 | 约 2 月 |

### 学习方法论

1. **先读后写**：每天先通读 README，理解概念后在 REPL 或编辑器中动手敲代码
2. **REPL 探索**：善用 `python` 交互式解释器快速验证语法
3. **改写实验**：改参数、改逻辑，观察行为变化
4. **对比 TS**：有 TypeScript 经验的同学，多对比两者的类型系统与 OOP 实现
5. **完成实战**：每天 README 末尾的实战练习是巩固知识的关键
6. **构建项目**：随着学习推进，逐步完善 `eshop` CLI 工具项目

### 阶段性检查点

完成每个阶段后，应能回答以下问题：

- **阶段一完成后**：能否用 Python 基本数据结构和控制流完成简单的数据处理脚本？
- **阶段二完成后**：能否用 OOP 设计数据模型并用函数封装业务逻辑？
- **阶段三完成后**：能否用装饰器/生成器/上下文管理器编写 Pythonic 代码？能否用包结构组织项目？
- **阶段四完成后**：能否用 asyncio 处理异步任务？用类型注解提升代码质量？用 Poetry 管理完整项目？

---

## 如何运行代码

### 方式一：本地安装 Python

1. 从 [python.org](https://www.python.org/downloads/) 下载 Python 3.12+
2. 安装时勾选 "Add Python to PATH"（Windows）
3. 验证安装：

```bash
python --version          # 查看 Python 版本
python -m pip --version   # 查看 pip 版本
```

### 方式二：Docker

```bash
# 用 Docker 运行 Python 脚本
docker run -it --rm -v "$(pwd):/workspace" -w /workspace python:3.12 python hello.py

# 进入交互式 Python
docker run -it --rm -v "$(pwd):/workspace" -w /workspace python:3.12 python
```

### 方式三：pyenv 版本管理

```bash
# 安装 pyenv
curl https://pyenv.run | bash

# 安装指定版本
pyenv install 3.12.0
pyenv global 3.12.0
pyenv version
```

### 虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活（Linux/macOS）
source .venv/bin/activate

# 激活（Windows）
.venv\Scripts\activate

# 退出虚拟环境
deactivate
```

### 执行 Python 代码

```bash
# 方式一：执行脚本文件
python hello.py

# 方式二：交互式 REPL
python
>>> print("Hello, Python!")
>>> exit()

# 方式三：执行单行代码
python -c "print('Hello')"

# 方式四：以模块方式运行
python -m eshop.cli

# 方式五：IPython（增强 REPL，需 pip install ipython）
ipython
```

### pip 包管理

```bash
pip install requests            # 安装包
pip install requests==2.31.0   # 指定版本
pip install -r requirements.txt # 批量安装
pip uninstall requests          # 卸载
pip list                        # 已安装列表
pip freeze > requirements.txt  # 导出依赖
pip show requests               # 查看包信息
```

### VS Code 配置

推荐安装扩展：
- **Python**（微软官方，必装）
- **Pylance**（类型检查与智能提示）
- **Ruff**（代码格式化与检查）
- **Jupyter**（Notebook 支持，数据分析用）

---

## 知识点速查

### Python 数据类型速查

| 类型 | 关键字 | 可变性 | 有序性 | 对应天数 |
|------|--------|--------|--------|---------|
| 整数 | int | 不可变 | - | Day02 |
| 浮点 | float | 不可变 | - | Day02 |
| 布尔 | bool | 不可变 | - | Day02 |
| 字符串 | str | 不可变 | 有序 | Day04 |
| 列表 | list | 可变 | 有序 | Day04 |
| 元组 | tuple | 不可变 | 有序 | Day05 |
| 字典 | dict | 可变 | 有序(3.7+) | Day05 |
| 集合 | set | 可变 | 无序 | Day05 |
| 冻结集合 | frozenset | 不可变 | 无序 | Day05 |
| None | NoneType | 不可变 | - | Day02 |

### 可变/不可变类型速查

```
不可变类型（Immutable）：
  int, float, bool, str, tuple, frozenset, bytes
  → 修改会创建新对象，原对象不变

可变类型（Mutable）：
  list, dict, set, bytearray
  → 可以原地修改，id() 不变
```

### 魔术方法速查

| 魔术方法 | 触发场景 | 对应天数 |
|---------|---------|---------|
| `__init__` | 对象初始化 | Day07 |
| `__str__` | print()/str() | Day07 |
| `__repr__` | repr()/调试输出 | Day07 |
| `__eq__` | == 运算符 | Day08 |
| `__lt__` | < 运算符 | Day08 |
| `__hash__` | hash()/字典键 | Day08 |
| `__len__` | len() | Day08 |
| `__getitem__` | obj[key] | Day08 |
| `__iter__` | for 循环 | Day12 |
| `__next__` | 迭代器 | Day12 |
| `__call__` | obj() 调用 | Day08 |
| `__enter__` | with 语句 | Day12 |
| `__exit__` | with 语句退出 | Day12 |
| `__contains__` | in 运算符 | Day08 |

### 装饰器速查

| 装饰器 | 用途 | 来源 | 对应天数 |
|--------|------|------|---------|
| `@property` | 属性 getter/setter | 内置 | Day07 |
| `@staticmethod` | 静态方法 | 内置 | Day07 |
| `@classmethod` | 类方法 | 内置 | Day07 |
| `@dataclass` | 自动生成数据类 | dataclasses | Day08 |
| `@abstractmethod` | 抽象方法 | abc | Day08 |
| `@functools.wraps` | 保留函数元信息 | functools | Day11 |
| `@functools.lru_cache` | LRU 缓存 | functools | Day11 |
| `@contextmanager` | 上下文管理器 | contextlib | Day12 |
| `@dataclass(frozen=True)` | 不可变数据类 | dataclasses | Day14 |

### 并发模型速查

| 模型 | 模块 | 适用场景 | GIL 影响 | 对应天数 |
|------|------|---------|---------|---------|
| 多线程 | threading | IO 密集型 | 受限 | Day13 |
| 多进程 | multiprocessing | CPU 密集型 | 不受限 | Day13 |
| 协程 | asyncio | 高并发 IO | 单线程异步 | Day13 |
| 线程池 | concurrent.futures | 混合型 | 受限 | Day13 |
| 进程池 | concurrent.futures | CPU 密集型 | 不受限 | Day13 |

### 包管理工具速查

| 工具 | 配置文件 | 特点 | 对应天数 |
|------|---------|------|---------|
| pip + venv | requirements.txt | 最基础、最通用 | Day15 |
| pip-tools | requirements.in/.txt | 锁文件分层 | Day15 |
| Poetry | pyproject.toml | 依赖管理+打包发布 | Day15 |
| uv | pyproject.toml | Rust 编写、极快 | Day15 |
| conda | environment.yml | 数据科学、二进制依赖 | Day15 |
| pipenv | Pipfile | 已逐渐被 Poetry 替代 | Day15 |

### 代码质量工具速查

| 工具 | 用途 | 安装 |
|------|------|------|
| black | 代码格式化 | `pip install black` |
| ruff | 代码检查（替代 flake8） | `pip install ruff` |
| mypy | 静态类型检查 | `pip install mypy` |
| isort | import 排序 | `pip install isort` |
| pre-commit | Git 钩子管理 | `pip install pre-commit` |

---

## 后续板块

本板块完成后，推荐按以下顺序继续学习：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **LLM / RAG / Agent** | Python 是 AI 领域的统治性语言，LangChain/LlamaIndex/PyTorch 均基于 Python |
| **数据分析** | pandas/numpy/matplotlib 数据处理与可视化 |
| **FastAPI / Flask** | Python Web 后端框架，对应 NestJS 的 Python 版本 |
| **Docker** | Python 应用容器化部署、Dockerfile 编写 |
| **Linux** | Python 运维脚本、subprocess 调用、crontab 定时执行 |
| **Node.js / NestJS** | 对比学习动态语言后端框架的设计差异 |

---

## 学习资源补充

> 以下为官方权威资源，遇到疑问时优先查阅

- [Python 官方文档](https://docs.python.org/3/) - 最权威的参考
- [Python Tutorial](https://docs.python.org/3/tutorial/) - 官方入门教程
- [PEP 8](https://peps.python.org/pep-0008/) - Python 代码风格指南
- [Real Python](https://realpython.com/) - 优质 Python 教程网站
- [Python Tricks](https://realpython.com/python-tricks/) - Python 技巧集
- [Fluent Python](https://www.oreilly.com/library/view/fluent-python-2nd/) - 进阶必读经典

---

## 贡献与反馈

本学习手册为原创内容，参考 GitHub 优质仓库的文档风格但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，用 Pythonic 方式开启你的 AI 全栈之路！**
