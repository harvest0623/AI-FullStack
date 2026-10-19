# Day15 - 包管理与虚拟环境

包管理和虚拟环境是 Python 工程化的基础，好的工具链让开发事半功倍。从一个简单的 `pip install` 到完整的 Poetry 项目管理，从 `python -m venv` 虚拟环境到 Docker 容器化部署，从 black 代码格式化到 mypy 静态检查、pre-commit 自动化钩子——这些工具链决定了你的 Python 项目是混乱不堪还是井井有条。本章将系统讲解 Python 包管理生态、项目结构最佳实践与代码质量工具链，为生产级项目打下工程化基础。

## 学习目标

完成本章后，你应能：

- 熟练使用 venv / virtualenv 创建和管理虚拟环境
- 掌握 pip 包管理器的常用命令与 requirements.txt
- 理解 pip-tools 的分层依赖管理（requirements.in → requirements.txt）
- 熟练使用 Poetry 管理完整 Python 项目（pyproject.toml / lock 文件）
- 了解 uv（Rust 编写的高性能替代）与 conda（数据科学场景）
- 理解 `__pycache__` 与字节码机制
- 掌握项目结构最佳实践（src 布局 / pyproject.toml）
- 配置代码质量工具链（black / ruff / mypy / isort / pre-commit）
- 编写生产可用的 Dockerfile 打包 Python 应用

## 理论知识讲解

### 1. 虚拟环境

#### 1.1 为什么需要虚拟环境

| 问题 | 无虚拟环境 | 有虚拟环境 |
|------|----------|----------|
| 项目 A 需要 Django 3.x | 全局只能装一个版本 | 项目 A 用 3.x，项目 B 用 4.x |
| 项目 B 需要 Django 4.x | 版本冲突 | 互不影响 |
| 系统稳定性 | 误装包可能破坏系统 Python | 隔离的沙箱 |
| 依赖可复现 | 无法精确还原 | requirements.txt / lock 文件 |

#### 1.2 venv（标准库）

```bash
# 创建虚拟环境（在项目目录下）
python -m venv .venv

# 激活（Linux/macOS）
source .venv/bin/activate

# 激活（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活（Windows cmd）
.venv\Scripts\activate.bat

# 退出虚拟环境
deactivate
```

#### 1.3 virtualenv（第三方，更快）

```bash
# 安装
pip install virtualenv

# 创建（比 venv 更快，支持更多功能）
virtualenv .venv

# 指定 Python 版本
virtualenv -p python3.12 .venv
```

#### 1.4 pyenv-virtualenv

```bash
# 结合 pyenv 版本管理
pyenv install 3.12.0
pyenv virtualenv 3.12.0 myproject
pyenv activate myproject
```

### 2. pip 包管理器

#### 2.1 常用命令

| 命令 | 用途 |
|------|------|
| `pip install requests` | 安装包 |
| `pip install requests==2.31.0` | 安装指定版本 |
| `pip install "requests>=2.30,<3.0"` | 安装版本范围 |
| `pip uninstall requests` | 卸载包 |
| `pip list` | 已安装包列表 |
| `pip show requests` | 查看包信息 |
| `pip freeze` | 导出已安装包（格式化） |
| `pip install --upgrade requests` | 升级包 |
| `pip install --force-reinstall requests` | 强制重装 |
| `pip cache dir` | 缓存目录 |
| `pip cache purge` | 清除缓存 |

#### 2.2 requirements.txt

```bash
# 从文件安装
pip install -r requirements.txt

# 导出当前环境的所有依赖
pip freeze > requirements.txt
```

```txt
# requirements.txt 示例
requests==2.31.0
flask>=2.3.0,<3.0
python-dotenv==1.0.0
```

#### 2.3 约束文件 constraints.txt

```bash
# constraints.txt 限制版本但不安装
requests==2.31.0

# 安装时应用约束
pip install -c constraints.txt flask
```

### 3. pip-tools

分层管理依赖：`requirements.in` 声明直接依赖，`requirements.txt` 锁定完整依赖树。

```bash
# 安装
pip install pip-tools

# requirements.in（只写直接依赖）
echo "flask" > requirements.in

# 编译：生成 requirements.txt（含所有间接依赖及版本锁定）
pip-compile requirements.in

# 同步：按 requirements.txt 精确安装/卸载
pip-sync requirements.txt
```

**分层管理**：
```txt
# dev.in
-r requirements.in
pytest
mypy
black
ruff

# dev.txt（pip-compile dev.in 生成）
```

### 4. Poetry（推荐）

Poetry 是目前最流行的 Python 项目管理工具，集依赖管理、虚拟环境、打包发布于一体。

#### 4.1 常用命令

| 命令 | 用途 |
|------|------|
| `poetry init` | 交互式初始化 pyproject.toml |
| `poetry new myproject` | 创建新项目结构 |
| `poetry add requests` | 添加依赖 |
| `poetry add pytest --group dev` | 添加开发依赖 |
| `poetry remove requests` | 移除依赖 |
| `poetry install` | 安装所有依赖（含开发依赖） |
| `poetry install --no-dev` | 只安装生产依赖 |
| `poetry shell` | 激活虚拟环境 |
| `poetry run python script.py` | 在虚拟环境中运行 |
| `poetry build` | 构建 wheel/sdist |
| `poetry publish` | 发布到 PyPI |
| `poetry lock` | 生成/更新 poetry.lock |
| `poetry show` | 查看已安装包 |
| `poetry show --tree` | 树状查看依赖关系 |

#### 4.2 pyproject.toml 结构

```toml
[tool.poetry]
name = "eshop"
version = "0.1.0"
description = "电商数据处理 CLI 工具"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{include = "eshop", from = "src"}]

[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.31.0"
click = "^8.1.0"
rich = "^13.0.0"

[tool.poetry.group.dev]
optional = true

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
mypy = "^1.5.0"
black = "^23.0.0"
ruff = "^0.1.0"

[tool.poetry.scripts]
eshop = "eshop.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 5. uv（Rust 编写，极速）

uv 是 Astral 公司用 Rust 编写的极速包管理器，兼容 pip 命令，速度比 pip 快 10-100 倍。

```bash
# 安装
pip install uv

# 创建虚拟环境
uv venv

# 兼容 pip 命令
uv pip install requests
uv pip install -r requirements.txt
uv pip list
uv pip freeze

# 编译和同步（替代 pip-tools）
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

| 特性 | pip | uv |
|------|-----|-----|
| 语言 | Python | Rust |
| 速度 | 基准 | 10-100x |
| 缓存 | 有 | 有（更高效） |
| 兼容性 | - | 兼容 pip 命令 |

### 6. conda 简介

conda 主要用于数据科学场景，能管理二进制依赖（如 NumPy 的 BLAS 库）。

```bash
# 创建环境
conda create -n myenv python=3.12

# 激活
conda activate myenv

# 安装包
conda install numpy pandas

# 从 environment.yml 创建
conda env create -f environment.yml
```

| 维度 | pip | conda |
|------|-----|-------|
| 适用场景 | 通用 Python | 数据科学 |
| 二进制依赖 | ❌ 需编译 | ✅ 预编译 |
| 包数量 | 多（PyPI） | 少（但科学计算齐全） |
| 虚拟环境 | 配合 venv | 内置 |

### 7. __pycache__ 与字节码

Python 会将 `.py` 编译为 `.pyc` 字节码缓存，下次运行时跳过编译。

```bash
# .pyc 文件位置
__pycache__/module.cpython-312.pyc

# 不生成 .pyc
python -B script.py

# 自定义缓存位置
export PYTHONPYCACHEPREFIX=/tmp/pycache
```

**.gitignore 必须包含**：
```
__pycache__/
*.py[cod]
*$py.class
```

### 8. 项目结构最佳实践

#### 8.1 src 布局 vs flat 布局

```
# src 布局（推荐，避免测试时误用源码）
myproject/
├── pyproject.toml
├── src/
│   └── mypackage/
│       ├── __init__.py
│       └── module.py
└── tests/

# flat 布局（简单项目可用）
myproject/
├── pyproject.toml
├── mypackage/
│   ├── __init__.py
│   └── module.py
└── tests/
```

**src 布局优势**：强制通过安装方式导入包，避免测试时直接导入源码而漏测打包配置。

#### 8.2 完整项目结构

```
eshop/
├── pyproject.toml
├── poetry.lock
├── README.md
├── Makefile
├── .gitignore
├── .pre-commit-config.yaml
├── docker/
│   ├── Dockerfile
│   └── .dockerignore
├── src/
│   └── eshop/
│       ├── __init__.py
│       ├── cli.py
│       ├── models/
│       └── services/
└── tests/
    ├── conftest.py
    └── test_models.py
```

### 9. 代码质量工具链

#### 9.1 black（代码格式化）

```bash
# 安装
pip install black

# 格式化
black .
black src/

# 指定行宽
black --line-length 99 .

# 检查（不修改）
black --check .
```

配置在 `pyproject.toml`：
```toml
[tool.black]
line-length = 99
target-version = ["py310"]
```

#### 9.2 ruff（代码检查，替代 flake8/pylint）

```bash
# 安装
pip install ruff

# 检查
ruff check .

# 自动修复
ruff check --fix .

# 格式化（替代 black）
ruff format .
```

#### 9.3 mypy（静态类型检查）

```bash
# 安装
pip install mypy

# 检查
mypy src/

# 严格模式
mypy --strict src/
```

#### 9.4 isort（import 排序）

```bash
# 安装
pip install isort

# 排序
isort .
```

#### 9.5 pre-commit（Git 钩子管理）

```bash
# 安装
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行
pre-commit run --all-files
```

### 10. Docker 打包 Python 应用

#### 10.1 Dockerfile 最佳实践

```dockerfile
# 多阶段构建
FROM python:3.12-slim AS builder
# ... 构建阶段

FROM python:3.12-slim AS runtime
# ... 运行阶段
```

| 实践 | 说明 |
|------|------|
| 多阶段构建 | 减小最终镜像体积 |
| slim 基础镜像 | 比 alpine 兼容性更好 |
| 非 root 用户 | 安全最佳实践 |
| .dockerignore | 排除不必要文件 |
| HEALTHCHECK | 容器健康检查 |
| requirements.txt | 比 poetry 更适合容器 |

## 关键知识点总结

### 包管理工具对比表

| 工具 | 配置文件 | 速度 | 依赖解析 | 打包发布 | 推荐场景 |
|------|---------|------|---------|---------|---------|
| pip + venv | requirements.txt | 基准 | 基础 | ❌ | 简单项目 |
| pip-tools | requirements.in/.txt | 基准 | 锁文件 | ❌ | 需要精确锁版本 |
| Poetry | pyproject.toml + lock | 中 | 优秀 | ✅ | 通用推荐 |
| uv | pyproject.toml | 极快 | 优秀 | 部分 | 追求速度 |
| conda | environment.yml | 中 | 优秀 | ❌ | 数据科学 |
| pipenv | Pipfile + lock | 慢 | 一般 | ❌ | 已不推荐 |

### venv 命令速查

| 命令 | 用途 |
|------|------|
| `python -m venv .venv` | 创建虚拟环境 |
| `source .venv/bin/activate` | 激活（Linux/macOS） |
| `.venv\Scripts\activate` | 激活（Windows） |
| `deactivate` | 退出 |
| `which python` | 确认使用虚拟环境的 Python |

### Poetry 命令速查

| 命令 | 用途 |
|------|------|
| `poetry init` | 初始化项目 |
| `poetry new <name>` | 创建新项目 |
| `poetry add <pkg>` | 添加依赖 |
| `poetry add <pkg> --group dev` | 添加开发依赖 |
| `poetry remove <pkg>` | 移除依赖 |
| `poetry install` | 安装所有依赖 |
| `poetry install --no-dev` | 只装生产依赖 |
| `poetry shell` | 激活虚拟环境 |
| `poetry run <cmd>` | 运行命令 |
| `poetry build` | 构建包 |
| `poetry publish` | 发布到 PyPI |
| `poetry lock` | 生成锁文件 |
| `poetry show --tree` | 依赖树 |

### 代码质量工具速查表

| 工具 | 用途 | 命令 | 配置位置 |
|------|------|------|---------|
| black | 格式化 | `black .` | `[tool.black]` |
| ruff | 检查+格式化 | `ruff check .` / `ruff format .` | `[tool.ruff]` |
| mypy | 类型检查 | `mypy src/` | `[tool.mypy]` |
| isort | import 排序 | `isort .` | `[tool.isort]` |
| pre-commit | Git 钩子 | `pre-commit run --all-files` | `.pre-commit-config.yaml` |

### Dockerfile 最佳实践清单

| 实践 | 说明 |
|------|------|
| 多阶段构建 | builder + runtime 两阶段 |
| slim 基础镜像 | `python:3.12-slim` |
| .dockerignore | 排除 .git / __pycache__ / .venv |
| 非 root 用户 | `USER appuser` |
| HEALTHCHECK | 容器健康检查 |
| 最小权限 | 只装运行时依赖 |
| 缓存优化 | 先 copy requirements 再 copy 源码 |
| 环境变量 | `PYTHONUNBUFFERED=1` |

## 实战练习

### 练习 1：用 Poetry 创建完整项目

1. 用 `poetry new eshop` 创建项目结构
2. 添加依赖：`click`（CLI）、`rich`（终端美化）、`requests`（HTTP）
3. 添加开发依赖：`pytest`、`mypy`、`ruff`、`black`
4. 编写一个简单的 `eshop` CLI 命令
5. 运行 `poetry build` 构建包

### 练习 2：配置代码质量工具链

1. 在 `pyproject.toml` 中配置 black（line-length=99）、ruff、mypy
2. 创建 `.pre-commit-config.yaml`，配置 ruff、black、mypy、isort
3. 运行 `pre-commit install` 安装钩子
4. 故意写一段不规范的代码，提交时观察 pre-commit 自动修复

### 练习 3：Docker 化 Python 应用

1. 参考本目录的 `docker/Dockerfile`，将你的 `eshop` 项目容器化
2. 编写 `.dockerignore`
3. 构建镜像：`docker build -t eshop:latest .`
4. 运行容器：`docker run --rm eshop:latest`
5. 优化：使用多阶段构建，对比镜像体积差异
