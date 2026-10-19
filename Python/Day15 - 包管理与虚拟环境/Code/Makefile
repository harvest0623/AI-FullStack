# Makefile - 常用命令快捷方式
# 适用于 eshop 电商数据处理 CLI 工具
# 用法：make <target>
# 帮助：make 或 make help

# ============================================================
# 变量定义
# ============================================================
PYTHON := python
POETRY := poetry
PACKAGE := eshop
SRC_DIR := src
TEST_DIR := tests

# 颜色定义（终端输出）
COLOR_RESET := \033[0m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_CYAN := \033[36m

# ============================================================
# 默认目标：显示帮助
# ============================================================
.PHONY: help
help:
	@echo "$(COLOR_CYAN)eshop - Make 命令清单$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)环境管理:$(COLOR_RESET)"
	@echo "  make install       安装项目依赖（含开发依赖）"
	@echo "  make dev           安装开发依赖并配置 pre-commit"
	@echo "  make venv          创建虚拟环境"
	@echo ""
	@echo "$(COLOR_GREEN)开发运行:$(COLOR_RESET)"
	@echo "  make run           运行 eshop CLI"
	@echo "  make shell         进入 Poetry 虚拟环境 shell"
	@echo ""
	@echo "$(COLOR_GREEN)代码质量:$(COLOR_RESET)"
	@echo "  make lint          代码检查（ruff）"
	@echo "  make format        代码格式化（black + ruff）"
	@echo "  make typecheck     类型检查（mypy）"
	@echo "  make check         一键检查（lint + typecheck）"
	@echo ""
	@echo "$(COLOR_GREEN)测试:$(COLOR_RESET)"
	@echo "  make test          运行所有测试"
	@echo "  make test-cov      运行测试并生成覆盖率报告"
	@echo "  make test-fast     只运行快速测试（跳过 slow 标记）"
	@echo ""
	@echo "$(COLOR_GREEN)构建与部署:$(COLOR_RESET)"
	@echo "  make build         构建包（wheel + sdist）"
	@echo "  make docker-build  构建 Docker 镜像"
	@echo "  make docker-run     运行 Docker 容器"
	@echo ""
	@echo "$(COLOR_GREEN)清理:$(COLOR_RESET)"
	@echo "  make clean         清理临时文件"
	@echo "  make clean-all     清理所有（含虚拟环境）"

# ============================================================
# 环境管理
# ============================================================
.PHONY: venv
venv:
	@echo "$(COLOR_YELLOW)创建虚拟环境...$(COLOR_RESET)"
	$(PYTHON) -m venv .venv
	@echo "$(COLOR_GREEN)虚拟环境已创建，请执行: source .venv/bin/activate$(COLOR_RESET)"

.PHONY: install
install:
	@echo "$(COLOR_YELLOW)安装项目依赖（含开发依赖）...$(COLOR_RESET)"
	$(POETRY) install
	@echo "$(COLOR_GREEN)✅ 依赖安装完成$(COLOR_RESET)"

.PHONY: dev
dev:
	@echo "$(COLOR_YELLOW)配置开发环境...$(COLOR_RESET)"
	$(POETRY) install
	$(POETRY) run pre-commit install
	@echo "$(COLOR_GREEN)✅ 开发环境配置完成$(COLOR_RESET)"
	@echo "  - Poetry 虚拟环境已就绪"
	@echo "  - pre-commit 钩子已安装"

# ============================================================
# 开发运行
# ============================================================
.PHONY: run
run:
	$(POETRY) run eshop $(ARGS)

.PHONY: shell
shell:
	$(POETRY) shell

# ============================================================
# 代码质量
# ============================================================
.PHONY: lint
lint:
	@echo "$(COLOR_YELLOW)代码检查（ruff）...$(COLOR_RESET)"
	$(POETRY) run ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "$(COLOR_GREEN)✅ 代码检查通过$(COLOR_RESET)"

.PHONY: format
format:
	@echo "$(COLOR_YELLOW)代码格式化...$(COLOR_RESET)"
	$(POETRY) run black $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run ruff format $(SRC_DIR) $(TEST_DIR)
	$(POETRY) run isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(COLOR_GREEN)✅ 格式化完成$(COLOR_RESET)"

.PHONY: typecheck
typecheck:
	@echo "$(COLOR_YELLOW)类型检查（mypy）...$(COLOR_RESET)"
	$(POETRY) run mypy $(SRC_DIR)
	@echo "$(COLOR_GREEN)✅ 类型检查通过$(COLOR_RESET)"

.PHONY: check
check: lint typecheck
	@echo "$(COLOR_GREEN)✅ 全部检查通过$(COLOR_RESET)"

# ============================================================
# 测试
# ============================================================
.PHONY: test
test:
	@echo "$(COLOR_YELLOW)运行测试...$(COLOR_RESET)"
	$(POETRY) run pytest $(TEST_DIR) -v

.PHONY: test-cov
test-cov:
	@echo "$(COLOR_YELLOW)运行测试并生成覆盖率报告...$(COLOR_RESET)"
	$(POETRY) run pytest $(TEST_DIR) --cov=$(PACKAGE) --cov-report=term-missing --cov-report=html

.PHONY: test-fast
test-fast:
	@echo "$(COLOR_YELLOW)运行快速测试（跳过 slow）...$(COLOR_RESET)"
	$(POETRY) run pytest $(TEST_DIR) -v -m "not slow"

# ============================================================
# 构建与部署
# ============================================================
.PHONY: build
build:
	@echo "$(COLOR_YELLOW)构建包...$(COLOR_RESET)"
	$(POETRY) build
	@echo "$(COLOR_GREEN)✅ 构建完成，产物在 dist/ 目录$(COLOR_RESET)"

.PHONY: publish
publish:
	@echo "$(COLOR_YELLOW)发布到 PyPI...$(COLOR_RESET)"
	$(POETRY) publish
	@echo "$(COLOR_GREEN)✅ 发布完成$(COLOR_RESET)"

.PHONY: docker-build
docker-build:
	@echo "$(COLOR_YELLOW)构建 Docker 镜像...$(COLOR_RESET)"
	docker build -t $(PACKAGE):latest -f docker/Dockerfile .
	@echo "$(COLOR_GREEN)✅ 镜像构建完成: $(PACKAGE):latest$(COLOR_RESET)"

.PHONY: docker-run
docker-run:
	@echo "$(COLOR_YELLOW)运行 Docker 容器...$(COLOR_RESET)"
	docker run --rm $(PACKAGE):latest

# ============================================================
# 清理
# ============================================================
.PHONY: clean
clean:
	@echo "$(COLOR_YELLOW)清理临时文件...$(COLOR_RESET)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov 2>/dev/null || true
	rm -f .coverage coverage.xml 2>/dev/null || true
	@echo "$(COLOR_GREEN)✅ 临时文件已清理$(COLOR_RESET)"

.PHONY: clean-all
clean-all: clean
	@echo "$(COLOR_YELLOW)清理所有（含构建产物和虚拟环境）...$(COLOR_RESET)"
	rm -rf dist build .venv poetry.lock 2>/dev/null || true
	@echo "$(COLOR_GREEN)✅ 全部清理完成$(COLOR_RESET)"
