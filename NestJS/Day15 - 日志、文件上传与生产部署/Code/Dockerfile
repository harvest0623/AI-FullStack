# ============================================================
# NestJS Day15 多阶段构建 Dockerfile
# 阶段一：deps    安装生产依赖（缓存层）
# 阶段二：builder 编译 TypeScript -> dist
# 阶段三：runner  仅拷贝 dist + node_modules，体积最小化
# ============================================================

# ---------- 阶段 1：安装依赖 ----------
FROM node:18-alpine AS deps
WORKDIR /app

# 利用 Docker 缓存：仅当 package*.json 变化时才重新 npm ci
COPY package*.json ./
# 使用 npm ci 而非 install：严格按 package-lock.json 安装，更稳更快
RUN npm ci

# ---------- 阶段 2：编译构建 ----------
FROM node:18-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 构建产物输出到 dist/
RUN npm run build

# 生产依赖单独安装（剔除 devDependencies，缩小镜像体积）
RUN npm ci --only=production && npm cache clean --force

# ---------- 阶段 3：运行时镜像 ----------
FROM node:18-alpine AS runner
WORKDIR /app

# 安装 dumb-init：作为 PID 1 处理信号转发，确保 SIGTERM 优雅退出
RUN apk add --no-cache dumb-init

# 创建非 root 用户运行应用，遵循最小权限原则
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nestjs -u 1001 -G nodejs

# 仅拷贝运行所需文件
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nestjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nestjs:nodejs /app/package.json ./package.json

# 创建上传目录（如使用 diskStorage）
RUN mkdir -p /app/uploads && chown -R nestjs:nodejs /app/uploads

USER nestjs

EXPOSE 3000

# 健康检查：每 30s 探活一次 /api/v1/health
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://localhost:3000/api/v1/health || exit 1

# dumb-init 转发 SIGTERM/SIGINT 给 node 进程，触发 enableShutdownHooks
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
