# Day15 代码文件说明

本目录包含 Day15 包管理与虚拟环境的完整配置文件集，所有配置文件围绕电商项目 `eshop` 设计，可直接用于 Python 3.10+ 项目。

## 文件清单

| 文件 | 用途 |
|------|------|
| `pyproject.toml` | 完整的 Poetry 项目配置（含 ruff/black/mypy/pytest 配置） |
| `requirements.txt` | pip 依赖文件示例（含注释说明） |
| `docker/Dockerfile` | Docker 打包 Python 应用最佳实践 |
| `docker/.dockerignore` | Docker 构建忽略文件 |
| `Makefile` | 常用命令快捷方式（install/dev/test/lint/format/check/clean） |
| `.pre-commit-config.yaml` | pre-commit 配置（ruff/black/mypy/isort/通用钩子） |

## 文件详细说明

### pyproject.toml

完整的 Poetry 项目配置，包含以下部分：

- `[tool.poetry]`：项目元数据（名称、版本、作者、分类器等）
- `[tool.poetry.dependencies]`：生产依赖（click、rich、requests、pydantic 等）
- `[tool.poetry.group.dev]`：开发依赖组（pytest、mypy、ruff、black 等）
- `[tool.poetry.group.docs]`：文档依赖组
- `[tool.poetry.scripts]`：命令行入口（`eshop` 命令）
- `[tool.ruff]`：Ruff 代码检查与格式化配置
- `[tool.black]`：Black 代码格式化配置
- `[tool.isort]`：isort import 排序配置
- `[tool.mypy]`：mypy 静态类型检查配置（严格模式）
- `[tool.pytest.ini_options]`：pytest 测试配置
- `[tool.coverage]`：覆盖率配置
- `[build-system]`：构建系统（Poetry）

### requirements.txt

适用于不用 Poetry 的场景，直接用 pip 安装：
```bash
pip install -r requirements.txt
```

每行依赖都有注释说明用途，便于维护。

### docker/Dockerfile

多阶段构建 Dockerfile，包含以下最佳实践：

- **多阶段构建**：builder 阶段装编译工具，runtime 阶段不带
- **slim 基础镜像**：`python:3.12-slim`，比 alpine 兼容性更好
- **层缓存优化**：先 copy requirements 再 copy 源码
- **非 root 用户**：`appuser` 运行，安全最佳实践
- **环境变量**：`PYTHONUNBUFFERED=1`、`PYTHONDONTWRITEBYTECODE=1`
- **HEALTHCHECK**：容器健康检查
- **时区设置**：`TZ=Asia/Shanghai`

### Makefile

提供常用命令的快捷方式：

| 命令 | 说明 |
|------|------|
| `make help` | 显示帮助 |
| `make install` | 安装项目依赖 |
| `make dev` | 配置开发环境（含 pre-commit） |
| `make run` | 运行 eshop CLI |
| `make test` | 运行测试 |
| `make test-cov` | 运行测试并生成覆盖率 |
| `make lint` | 代码检查（ruff） |
| `make format` | 代码格式化（black + ruff + isort） |
| `make typecheck` | 类型检查（mypy） |
| `make check` | 一键检查（lint + typecheck） |
| `make build` | 构建包 |
| `make docker-build` | 构建 Docker 镜像 |
| `make clean` | 清理临时文件 |

### .pre-commit-config.yaml

Git 钩子配置，提交代码前自动检查：

- **通用钩子**：end-of-file-fixer、trailing-whitespace、check-yaml/json/toml
- **ruff**：代码检查与自动修复
- **black**：代码格式化
- **isort**：import 排序
- **mypy**：静态类型检查（严格模式）
- **poetry-check/lock**：Poetry 配置一致性检查

## 快速开始

### 方式一：使用 Poetry（推荐）

```bash
# 1. 安装 Poetry
pip install poetry

# 2. 复制配置文件到你的项目
cp pyproject.toml /path/to/your/project/

# 3. 初始化（如果 pyproject.toml 已存在，可跳过）
cd /path/to/your/project/
poetry install

# 4. 激活虚拟环境
poetry shell

# 5. 运行项目
poetry run eshop --help
```

### 方式二：使用 pip + venv

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装开发工具
pip install pytest mypy ruff black isort pre-commit

# 4. 配置 pre-commit
pre-commit install
```

### 方式三：使用 uv（极速）

```bash
# 1. 安装 uv
pip install uv

# 2. 创建虚拟环境
uv venv

# 3. 安装依赖
uv pip install -r requirements.txt
```

### 方式四：Docker

```bash
# 构建镜像
docker build -t eshop:latest -f docker/Dockerfile .

# 运行
docker run --rm eshop:latest
docker run --rm eshop:latest eshop --help
```

## 环境要求

- Python 3.10+
- Poetry 1.7+（如使用 Poetry）
- Docker（如需容器化）
- Make（Windows 需安装 GnuMake 或使用 WSL）

## 项目结构参考

将本目录的配置文件配合以下项目结构使用：

```
eshop/
├── pyproject.toml              ← 本目录的 pyproject.toml
├── requirements.txt            ← 本目录的 requirements.txt
├── Makefile                    ← 本目录的 Makefile
├── .pre-commit-config.yaml     ← 本目录的 .pre-commit-config.yaml
├── README.md
├── docker/
│   ├── Dockerfile              ← 本目录的 docker/Dockerfile
│   └── .dockerignore           ← 本目录的 docker/.dockerignore
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

## CI/CD 集成建议

### GitHub Actions 示例

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        run: poetry install
      - name: Lint
        run: poetry run ruff check src/ tests/
      - name: Format check
        run: poetry run black --check src/ tests/
      - name: Type check
        run: poetry run mypy src/
      - name: Test
        run: poetry run pytest
```

### GitLab CI 示例

```yaml
# .gitlab-ci.yml
stages:
  - test

test:
  image: python:3.12-slim
  stage: test
  before_script:
    - pip install poetry
    - poetry install
  script:
    - poetry run ruff check src/ tests/
    - poetry run black --check src/ tests/
    - poetry run mypy src/
    - poetry run pytest
```
