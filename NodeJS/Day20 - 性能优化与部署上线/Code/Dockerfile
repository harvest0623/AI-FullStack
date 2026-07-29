# Dockerfile - 多阶段构建示例
# ------------------------------------------------------------
# 目标: 构建一个体积小、非 root、自带健康检查的生产镜像
# 构建: docker build -t day20-app:1.0 .
# 运行: docker run --rm -p 3000:3000 --env-file .env.production day20-app:1.0
# ------------------------------------------------------------

# ============ 阶段 1: builder ============
# 用完整镜像安装依赖、(可选)执行构建步骤
FROM node:18-alpine AS builder

WORKDIR /app

# 先单独拷贝依赖清单, 利用 Docker 层缓存: 源码改动不会重装 node_modules
COPY package.json package-lock.json* ./

# 安装生产依赖 (CI 环境推荐 npm ci, 它要求 lock 文件且严格按其安装)
# 若没有 lock 文件, 这里会失败 —— 提交代码时务必把 package-lock.json 一起入库
RUN npm ci --omit=dev || npm install --omit=dev

# ============ 阶段 2: runner ============
# 最终镜像只保留运行所需文件, 不带 dev 依赖与构建工具, 体积更小
FROM node:18-alpine AS runner

WORKDIR /app

# 安装 wget 用于 HEALTHCHECK (alpine 默认没有 curl)
RUN apk add --no-cache wget

# 创建非 root 用户: node 镜像内置了 node 用户 (uid 1000), 直接复用
# 以非 root 运行是容器安全基线: 即使被攻破, 攻击者也拿不到 root 权限
USER node

# 从 builder 拷贝生产依赖与源码 (注意 --chown 确保属主正确)
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --chown=node:node package.json ./
COPY --chown=node:node *.js ./

# 声明端口 (文档作用, 真正发布需 docker run -p)
EXPOSE 3000

# 设置生产环境变量 (运行时仍可用 --env-file 覆盖)
ENV NODE_ENV=production \
    PORT=3000

# 健康检查: 每 30 秒访问 /health, 连续 3 次失败标记为 unhealthy
# --interval 间隔 / --timeout 单次超时 / --start-period 启动宽限 / --retries 重试次数
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

# 用 CMD 的 exec 形式, 让 node 进程成为 PID 1, 正确接收 SIGTERM 做优雅退出
# (呼应 Day16 优雅停机: PM2/k8s 发 SIGTERM -> Node 监听 'SIGTERM' 关闭连接后退出)
CMD ["node", "health-check.js"]
