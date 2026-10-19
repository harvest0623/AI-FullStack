# Dockerfile - Docker 打包 Python 应用最佳实践
# 适用于 eshop 电商数据处理 CLI 工具
# 多阶段构建 + slim 基础镜像 + 非 root 用户 + HEALTHCHECK
# 用法：
#   docker build -t eshop:latest -f docker/Dockerfile .
#   docker run --rm eshop:latest
#   docker run --rm eshop:latest eshop --help

# ============================================================
# 阶段 1：构建阶段（安装依赖）
# ============================================================
FROM python:3.12-slim AS builder

# 设置环境变量，优化 Python 在容器中的行为
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装构建依赖（如需编译 C 扩展）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 先复制依赖文件（利用 Docker 层缓存优化）
COPY pyproject.toml poetry.lock ./

# 安装 Poetry
RUN pip install poetry==1.7.1

# 配置 Poetry：不创建虚拟环境（直接装到系统 Python）
ENV POETRY_VIRTUALENVS_CREATE=false

# 安装生产依赖（不安装开发依赖）
RUN poetry install --no-root --no-dev

# ============================================================
# 阶段 2：运行阶段（最终镜像）
# ============================================================
FROM python:3.12-slim AS runtime

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TZ=Asia/Shanghai

# 安装运行时依赖（如有需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制已安装的 Python 包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制源码
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup README.md /app/

# 切换到非 root 用户
USER appuser

# 健康检查（如适用）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import eshop; print('ok')" || exit 1

# 默认命令
ENTRYPOINT ["eshop"]
CMD ["--help"]

# 暴露端口（如适用，Web 服务用）
# EXPOSE 8000

# ============================================================
# 构建优化说明
# ============================================================
# 1. 多阶段构建：builder 阶段装编译工具，runtime 阶段不带
# 2. 层缓存：先 copy requirements 再 copy 源码，源码变更不重新装依赖
# 3. slim 而非 alpine：alpine 用 musl，部分 Python 包需重新编译
# 4. 非 root 用户：安全最佳实践
# 5. PYTHONUNBUFFERED=1：日志实时输出，不缓冲
# 6. PYTHONDONTWRITEBYTECODE=1：不生成 .pyc，节省空间
