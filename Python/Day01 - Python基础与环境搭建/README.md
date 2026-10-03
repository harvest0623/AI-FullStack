# Day01 - Python 基础与环境搭建

Python 是全球最流行的编程语言之一，凭借简洁的语法和强大的生态，它横跨人工智能、Web 开发、数据分析、自动化运维、网络爬虫等众多领域。对于想要构建电商数据处理 CLI 工具 `eshop` 的开发者来说，Python 是一门性价比极高的语言：上手快、表达力强、标准库丰富。本章将带你从零开始认识 Python，搭建可用的开发环境，并写出第一个程序，为后续四天的语法学习打下基础。

## 学习目标

- 了解 Python 的诞生背景、设计哲学与核心特点
- 理解 Python 2 与 Python 3 的差异，明确为什么必须使用 Python 3
- 掌握 Python 在各领域的应用场景与代表性框架
- 区分解释型与编译型语言，理解 CPython 与 `.pyc` 字节码
- 完成 Python 3.10+ 的本地安装，并学会使用 `pyenv`、`venv`、`pip`
- 熟悉 REPL、脚本执行、`python -c`、`python -m` 等多种执行方式
- 掌握 PEP 8 代码风格规范，写出可读性强的代码
- 运行第一个 Python 程序 `hello.py`

## 理论知识讲解

### 1. Python 简介与定位

Python 由荷兰程序员 **Guido van Rossum** 于 1989 年圣诞节假期开始设计，1991 年正式发布。它的设计哲学强调**优雅、明确、简单**，追求代码的可读性高于一切。

Python 的设计哲学可以通过 `import this` 查看到的 **The Zen of Python** 来体会，其中几条尤为关键：

- 简洁胜于复杂（Simple is better than complex）
- 明确胜于隐晦（Explicit is better than implicit）
- 可读性很重要（Readability counts）
- 应该有一种——最好只有一种——显而易见的方式去做一件事（There should be one-- and preferably only one --obvious way to do it）

### 2. Python 2 vs Python 3

Python 3 于 2008 年发布，是一次不向后兼容的重大升级。Python 2 已于 **2020 年 1 月 1 日**正式停止官方维护，所有新项目都应使用 Python 3。

| 对比项 | Python 2 | Python 3 |
| --- | --- | --- |
| print 语句 | `print "hi"` | `print("hi")` 函数 |
| 字符串默认编码 | ASCII | Unicode（UTF-8） |
| 整数除法 | `3/2 == 1` | `3/2 == 1.5`，`3//2 == 1` |
| range 返回 | 列表 | 迭代器（节省内存） |
| 中文标识符 | 不支持 | 支持 |
| 官方维护 | 2020 年停止 | 持续维护 |

Python 3 的重大改进包括：统一的 Unicode 字符串、更清晰的整数除法语义、异步语法 `async/await`（3.5+）、类型提示 `type hints`（3.5+）、海象运算符 `:=`（3.8+）、模式匹配 `match-case`（3.10+）。

### 3. 应用领域

Python 的强大在于其生态覆盖几乎所有热门方向：

| 领域 | 代表框架/库 | 典型用途 |
| --- | --- | --- |
| Web 开发 | Django、Flask、FastAPI | 网站后端、API 服务 |
| AI / 机器学习 | PyTorch、TensorFlow、scikit-learn | 模型训练、推理 |
| 数据科学 | pandas、numpy、matplotlib | 数据清洗、分析、可视化 |
| 自动化运维 | Ansible、Fabric、SaltStack | 服务器批量管理 |
| 网络爬虫 | Scrapy、requests、BeautifulSoup | 数据采集 |
| 桌面 GUI | PyQt、Tkinter | 跨平台桌面应用 |

### 4. Python 特点

- **解释型**：代码逐行翻译执行，无需编译环节
- **动态类型**：变量无需声明类型，运行时确定
- **跨平台**：一份代码可在 Windows、macOS、Linux 运行
- **多范式**：支持面向对象、函数式、过程式编程
- **GIL（全局解释器锁）**：CPython 实现中的锁，使得同一时刻只有一个线程执行 Python 字节码，因此 CPU 密集型多线程无法真正并行，可使用多进程（`multiprocessing`）绕过

### 5. 解释型 vs 编译型

| 对比项 | 编译型（C/C++） | 解释型（Python） |
| --- | --- | --- |
| 执行前 | 编译为机器码 | 不编译，逐行解释 |
| 执行速度 | 快 | 较慢 |
| 跨平台 | 需重新编译 | 一份源码到处运行 |
| 开发效率 | 较低 | 高 |

实际上 Python 有一个折中机制：源码 `.py` 会先被编译为**字节码** `.pyc`（存放在 `__pycache__` 目录），再由 **CPython** 解释器逐条执行字节码。这就是为什么 Python 既能跨平台，又有相对可接受的速度。

### 6. 安装方式

#### 6.1 各平台官方安装包

- **Windows**：从 [python.org](https://www.python.org/downloads/) 下载安装包，安装时务必勾选 **Add Python to PATH**
- **macOS**：推荐使用 Homebrew：`brew install python@3.12`
- **Linux**：多数发行版自带 Python，可使用包管理器升级，如 `apt install python3`

#### 6.2 pyenv 版本管理

`pyenv` 允许在同一台机器上安装多个 Python 版本并随时切换：

```bash
# 安装 pyenv（macOS/Linux）
curl https://pyenv.run | bash

# 安装指定版本
pyenv install 3.12.4

# 设置全局默认版本
pyenv global 3.12.4

# 为某个项目设置本地版本
pyenv local 3.12.4
```

#### 6.3 conda 简介

`conda` 是 Anaconda 提供的包与环境管理器，在数据科学领域常用。它既能管理 Python 版本，也能管理非 Python 的 C 库依赖（如 numpy 的底层 BLAS）。适合科研与机器学习场景。

### 7. REPL 交互式解释器

在终端输入 `python` 即可进入 **REPL**（Read-Eval-Print Loop）交互式环境，可即时执行代码：

```python
>>> 1 + 1
2
>>> name = "eshop"
>>> print(name)
eshop
>>> exit()    # 退出
```

REPL 适合快速验证小段代码，但不适合编写完整程序。

### 8. pip 包管理器

`pip` 是 Python 的官方包管理器，常用命令：

| 命令 | 作用 |
| --- | --- |
| `pip install requests` | 安装包 |
| `pip uninstall requests` | 卸载包 |
| `pip list` | 列出已安装包 |
| `pip freeze > requirements.txt` | 导出依赖清单 |
| `pip show requests` | 查看包详细信息 |
| `pip install -r requirements.txt` | 批量安装依赖 |

### 9. venv 虚拟环境

每个项目应使用独立的虚拟环境，避免包冲突：

```bash
# 创建虚拟环境（在项目根目录执行）
python -m venv .venv

# 激活（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活（macOS/Linux）
source .venv/bin/activate

# 退出虚拟环境
deactivate
```

### 10. 执行方式

| 方式 | 命令 | 适用场景 |
| --- | --- | --- |
| 脚本执行 | `python file.py` | 运行完整程序 |
| 命令行执行 | `python -c "print('hi')"` | 执行单行代码 |
| 模块执行 | `python -m http.server` | 以模块方式运行 |
| REPL | `python` | 交互式调试 |
| IDLE | `idle` | 自带简易 IDE |

### 11. PEP 8 代码风格

PEP 8 是 Python 官方的代码风格指南，遵守它能让代码更易读、更专业：

- **缩进**：4 个空格，不要用 Tab
- **行宽**：建议 79 字符，最长 99 字符
- **命名规范**：

| 类型 | 规范 | 示例 |
| --- | --- | --- |
| 变量、函数 | snake_case | `product_price` |
| 类 | PascalCase | `ProductOrder` |
| 常量 | UPPER_CASE | `MAX_STOCK` |
| 私有 | 前置下划线 | `_internal_id` |

- **运算符两侧**加空格：`a = b + c`
- **逗号后**加空格：`[1, 2, 3]`

### 12. 注释

```python
# 这是单行注释

"""
这是多行注释（文档字符串 docstring），
通常用于描述函数、类、模块的用途。
"""

def add(a, b):
    """返回两数之和。"""
    return a + b
```

### 13. 第一个程序

```python
# hello.py
print("Hello, Python!")
```

## 环境搭建

详细的环境配置步骤请参考 [Code/README.md](./Code/README.md)，其中包含：

- Windows / macOS / Linux 三平台安装步骤
- pyenv 安装与多版本切换
- venv 虚拟环境创建与激活
- pip 常用命令速查
- VS Code 扩展推荐与配置

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/hello.py` | 第一个 Python 程序，演示 `print`、`input`、f-string、`if __name__ == '__main__'` |
| `Code/basics.py` | 基础语法练习，演示注释、缩进、多行语句、多变量赋值、`print` 的 `sep/end` 参数、`import this` |

## 关键知识点总结

### Python 特点速查

- 解释型、动态类型、跨平台、多范式
- CPython 是官方默认实现，字节码存于 `.pyc`
- GIL 限制多线程并行，CPU 密集任务用多进程

### PEP 8 规范速查

| 项目 | 规范 |
| --- | --- |
| 缩进 | 4 空格 |
| 行宽 | 79 / 99 |
| 变量函数 | snake_case |
| 类 | PascalCase |
| 常量 | UPPER_CASE |
| import | 每行一个，按标准库/三方库/本地分组 |

### 执行方式对比表

| 方式 | 命令示例 | 优点 | 缺点 |
| --- | --- | --- | --- |
| 脚本 | `python hello.py` | 完整、可复用 | 需保存文件 |
| 命令行 | `python -c "..."` | 快速 | 仅适合单行 |
| 模块 | `python -m json.tool` | 复用模块 | 需理解模块路径 |
| REPL | `python` | 即时反馈 | 不易保存 |

## 实战练习

### 练习 1：环境验证

1. 在终端执行 `python --version`，确认版本号 ≥ 3.10
2. 执行 `python -c "import this"`，阅读并翻译其中 3 条你最有共鸣的箴言
3. 创建虚拟环境 `.venv` 并激活，执行 `pip list` 查看默认包

### 练习 2：第一个 eshop 程序

编写 `eshop_hello.py`，使用 `input` 读取用户名，用 f-string 输出欢迎信息：

```python
name = input("请输入您的用户名：")
print(f"欢迎 {name} 来到 eshop 电商数据平台！")
```

### 练习 3：探索 pip

1. 执行 `pip install requests`，再用 `pip show requests` 查看版本与位置
2. 执行 `pip freeze > requirements.txt`，查看生成的依赖文件
3. 思考：为什么每个项目都要用独立的虚拟环境？
