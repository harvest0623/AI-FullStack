# Day14 - 实战运维与自动化部署

本章是 Linux 学习模块的收官之战，综合运用前 13 天的全部知识，完成从一台空白服务器到全栈服务部署的完整运维流程。你将拿到一台全新的 Ubuntu 22.04 服务器，通过服务器初始化、安全加固、性能调优、服务部署、自动备份等步骤，最终搭建起 Nginx + Node.js + MySQL + Redis 的电商全栈服务。这一天的脚本不是零散的命令演示，而是生产环境可直接参考的自动化部署方案，体现了"基础设施即代码"（IaC）的运维理念。

---

## 学习目标

完成本章学习后，你应能够：

- 掌握新服务器初始化的标准流程（更新、时区、用户、安全、调优）
- 编写幂等可重复执行的服务器初始化脚本
- 配置 Nginx 反向代理与负载均衡（upstream 多实例）
- 部署 MySQL 并配置自动备份脚本（mysqldump + 压缩 + 保留策略）
- 部署 Redis 并完成安全配置（bind/requirepass）
- 使用 PM2 管理 Node.js 多实例并实现零停机部署
- 设计一键部署脚本（颜色输出、日志记录、错误处理、幂等性）
- 了解 Docker 与传统部署的差异
- 建立完整的运维最佳实践体系（日常运维、故障排查、备份恢复、CI/CD、IaC）

---

## 理论知识讲解

### 一、服务器初始化流程

#### 1.1 标准操作步骤

拿到一台新服务器后的标准初始化流程：

```
┌─────────────────────────────────────────────────────────────┐
│                    服务器初始化流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: 系统更新                                           │
│    apt update && apt upgrade                                │
│                                                             │
│  Step 2: 时区与时间同步                                     │
│    timedatectl set-timezone Asia/Shanghai                   │
│    配置 chrony/ntp                                          │
│                                                             │
│  Step 3: 基础工具安装                                       │
│    vim git curl wget htop iostat sysstat                    │
│                                                             │
│  Step 4: 创建部署用户                                       │
│    useradd deploy, 配置 sudo, SSH 密钥                      │
│                                                             │
│  Step 5: 安全加固                                           │
│    防火墙(ufw) + SSH 加固 + fail2ban                       │
│                                                             │
│  Step 6: 内核参数调优                                       │
│    ulimit + sysctl 网络参数                                 │
│                                                             │
│  Step 7: 创建项目目录结构                                   │
│    /opt/ecommerce/{backend,logs,scripts,backup}             │
│                                                             │
│  Step 8: 部署服务                                           │
│    Nginx + MySQL + Redis + Node.js                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 目录规划

```
/opt/ecommerce/              → 项目根目录
├── backend/                 → 后端代码（Node.js）
├── logs/                    → 应用日志
├── scripts/                 → 运维脚本
├── backup/                  → 数据备份
└── config/                  → 配置文件

/etc/nginx/sites-available/  → Nginx 站点配置
/etc/nginx/sites-enabled/    → Nginx 启用站点（软链接）
/var/log/ecommerce/          → 系统日志
```

---

### 二、Nginx 反向代理与负载均衡

#### 2.1 反向代理原理

```
正向代理（代理客户端）：
  客户端 → 代理服务器 → 目标服务器
  场景：VPN、爬虫代理

反向代理（代理服务端）：
  客户端 → Nginx（反向代理） → 后端服务（Node.js/Python/Java）
  场景：负载均衡、SSL 终止、静态缓存
```

#### 2.2 upstream 负载均衡策略

| 策略 | 配置 | 说明 |
|------|------|------|
| **轮询（默认）** | `upstream backend { server 127.0.0.1:3000; server 127.0.0.1:3001; }` | 按顺序轮流分配 |
| **权重** | `server 127.0.0.1:3000 weight=3;` | 按权重比例分配 |
| **ip_hash** | `ip_hash;` | 同一 IP 固定到同一后端（会话保持） |
| **least_conn** | `least_conn;` | 分配给连接数最少的后端 |
| **fair（第三方）** | `fair;` | 按响应时间分配 |

#### 2.3 HTTPS 配置（Let's Encrypt）

```bash
# 安装 certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（自动修改 Nginx 配置）
sudo certbot --nginx -d example.com -d www.example.com

# 自动续期（certbot 已自动配置 cron）
sudo certbot renew --dry-run  # 测试续期
```

#### 2.4 Nginx 性能调优

| 参数 | 默认值 | 建议值 | 说明 |
|------|--------|--------|------|
| `worker_processes` | 1 | auto | 工作进程数（auto=CPU核数） |
| `worker_connections` | 1024 | 10240 | 每个进程最大连接数 |
| `gzip` | off | on | 开启压缩 |
| `client_max_body_size` | 1m | 20m | 上传文件大小限制 |
| `keepalive_timeout` | 65 | 65 | keepalive 超时 |
| `sendfile` | off | on | 零拷贝传输 |

---

### 三、MySQL 部署与自动备份

#### 3.1 安装与安全初始化

```bash
# 安装 MySQL 8.0
sudo apt install -y mysql-server

# 安全初始化（设置 root 密码、移除匿名用户等）
sudo mysql_secure_installation

# 验证安装
sudo mysql -u root -p
```

#### 3.2 配置文件优化

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf 关键配置
[mysqld]
# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# InnoDB 缓冲池（物理内存的 50-70%）
innodb_buffer_pool_size = 2G

# 连接数
max_connections = 200

# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# binlog（主从复制/数据恢复）
log_bin = /var/log/mysql/binlog
binlog_expire_logs_seconds = 604800  # 7 天
```

#### 3.3 mysqldump 备份策略

```bash
# 全量备份（压缩）
mysqldump -u root -p --all-databases --single-transaction --quick \
  --routines --triggers | gzip > backup_$(date +%Y%m%d).sql.gz

# 备份指定数据库
mysqldump -u root -p ecommerce --single-transaction | gzip > ecommerce_$(date +%Y%m%d).sql.gz

# 保留最近 30 天
find /backup -name "backup_*.sql.gz" -mtime +30 -delete
```

---

### 四、Redis 部署与配置

```bash
# 安装 Redis
sudo apt install -y redis-server

# 安全配置
sudo vim /etc/redis/redis.conf
# bind 127.0.0.1                    # 只监听本地
# requirepass YourStrongPassword     # 设置密码
# maxmemory 512mb                   # 内存上限
# maxmemory-policy allkeys-lru      # 淘汰策略

# 重启并设置开机自启
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

---

### 五、Node.js + PM2 部署

#### 5.1 nvm 安装 Node.js

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# 安装 Node.js LTS
nvm install --lts
nvm use --lts

# 设置默认版本
nvm alias default lts/*
```

#### 5.2 PM2 进程管理

```bash
# 安装 PM2
npm install -g pm2

# 启动应用
pm2 start app.js --name ecommerce

# 多实例启动（集群模式）
pm2 start app.js -i 4 --name ecommerce

# 零停机重载
pm2 reload ecommerce

# 查看状态
pm2 status
pm2 logs ecommerce

# 开机自启
pm2 startup
pm2 save
```

#### 5.3 ecosystem.config.js 多实例配置

```javascript
module.exports = {
  apps: [{
    name: 'ecommerce',
    script: './backend/app.js',
    instances: 4,              // 4 个实例（或 'max' 用所有 CPU）
    exec_mode: 'cluster',      // 集群模式
    max_memory_restart: '500M',// 内存超限自动重启
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    error_file: '/opt/ecommerce/logs/error.log',
    out_file: '/opt/ecommerce/logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
}
```

---

### 六、一键部署脚本设计

#### 6.1 脚本设计原则

| 原则 | 说明 |
|------|------|
| **幂等性** | 可重复执行，已安装的跳过，不会报错 |
| **错误处理** | `set -euo pipefail`，任何错误立即停止 |
| **日志记录** | 所有操作记录到日志文件 |
| **颜色输出** | 不同级别用不同颜色，便于阅读 |
| **模块化** | 按功能分函数，结构清晰 |
| **可配置** | 关键参数用变量，便于修改 |

#### 6.2 脚本结构

```bash
#!/bin/bash
set -euo pipefail

# 1. 颜色输出函数
# 2. 日志记录函数
# 3. 错误处理函数
# 4. 检查函数（是否已安装/已配置）
# 5. 安装函数（幂等）
# 6. 配置函数
# 7. 验证函数
# 8. 主流程
```

---

### 七、Docker 与 Docker Compose 简介

#### 7.1 Docker 解决了什么问题

| 问题 | 传统部署 | Docker 部署 |
|------|---------|------------|
| 环境一致性 | "在我机器上能跑" | 镜像一致，处处可跑 |
| 依赖冲突 | 多应用依赖版本冲突 | 容器隔离，互不影响 |
| 部署速度 | 装依赖几分钟到几小时 | 拉镜像秒级启动 |
| 扩缩容 | 手动配置新机器 | docker-compose scale |
| 回滚 | 难 | 切换镜像版本即可 |

#### 7.2 传统部署 vs Docker 对比

| 对比项 | 传统部署 | Docker 部署 |
|--------|---------|------------|
| 环境搭建 | 手动装依赖 | 镜像即环境 |
| 隔离性 | 进程级隔离 | 容器级隔离 |
| 资源占用 | 直接用系统资源 | 有额外开销（小） |
| 学习成本 | 低（纯命令） | 中（需学 Dockerfile） |
| 适合场景 | 简单/单机 | 复杂/微服务/CI/CD |
| 运维复杂度 | 高（依赖管理麻烦） | 低（镜像管理） |

#### 7.3 Dockerfile 与 docker-compose.yml 简介

```dockerfile
# Dockerfile 示例
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
EXPOSE 3000
CMD ["node", "app.js"]
```

```yaml
# docker-compose.yml 示例
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]
    depends_on: [app]
  app:
    build: .
    deploy:
      replicas: 4
    environment:
      - NODE_ENV=production
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    volumes: ["mysql_data:/var/lib/mysql"]
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
volumes:
  mysql_data:
```

---

### 八、运维最佳实践总结

#### 8.1 日常运维流程

```
每日检查：
  - 监控告警是否正常
  - 服务状态是否健康
  - 磁盘空间是否充足
  - 日志是否有异常

每周维护：
  - 系统安全补丁
  - 备份验证（恢复测试）
  - 日志归档清理
  - 性能趋势分析

每月规划：
  - 容量评估
  - 安全审计
  - 架构优化
  - 灾备演练
```

#### 8.2 故障排查方法论

```
1. 确认故障现象（什么服务、什么时间、什么影响）
2. 查看监控告警（CPU/内存/磁盘/网络/服务状态）
3. 查看日志（systemctl status / journalctl / 应用日志）
4. 定位根因（Day12 性能排查方法论）
5. 修复故障（重启/回滚/扩容/修复代码）
6. 验证恢复（服务可用、性能正常）
7. 复盘总结（根因分析、预防措施、改进计划）
```

#### 8.3 备份恢复策略（3-2-1 原则）

| 原则 | 说明 |
|------|------|
| **3** 份数据 | 至少保留 3 份数据 |
| **2** 种介质 | 存储在 2 种不同介质（本地磁盘 + 对象存储） |
| **1** 份异地 | 至少 1 份在异地（云存储/异地机房） |

#### 8.4 CI/CD 简介

```
开发 → 代码提交 → CI（自动构建测试） → CD（自动部署）
         │              │                  │
      Git 仓库      Jenkins/GitHub      自动化部署
                   Actions/GitLab CI    到测试/生产环境
```

#### 8.5 Infrastructure as Code（IaC）理念

| 工具 | 说明 |
|------|------|
| **Shell 脚本** | 最基础的 IaC（本章内容） |
| **Ansible** | 无 Agent 的配置管理工具 |
| **Terraform** | 基础设施编排（云资源） |
| **Docker Compose** | 容器编排 |
| **Kubernetes** | 容器编排平台 |

---

## 代码文件说明

| 文件 | 说明 | 权限要求 |
|------|------|---------|
| `Code/01-server-init.sh` | 服务器初始化综合脚本（更新/用户/SSH/防火墙/调优/目录） | sudo |
| `Code/02-deploy-nginx-reverse-proxy.conf` | Nginx 反向代理完整配置（负载均衡/HTTPS/gzip/WebSocket） | 参考 |
| `Code/03-deploy-full-stack.sh` | 全栈一键部署脚本（Nginx/MySQL/Redis/Node.js/PM2） | sudo |
| `Code/04-mysql-backup.sh` | MySQL 自动备份脚本（压缩/保留/恢复说明） | sudo |
| `Code/05-ops-best-practices.md` | 运维最佳实践文档（日常运维/故障排查/CI/CD/IaC） | 参考 |

---

## 关键知识点总结

### 服务器初始化清单

| 步骤 | 命令 | 状态 |
|------|------|------|
| 系统更新 | `apt update && apt upgrade` | [ ] |
| 时区设置 | `timedatectl set-timezone Asia/Shanghai` | [ ] |
| 基础工具 | `apt install -y vim git curl htop sysstat` | [ ] |
| 创建用户 | `useradd -m -s /bin/bash deploy` | [ ] |
| 配置 sudo | `usermod -aG sudo deploy` | [ ] |
| SSH 密钥 | `ssh-keygen + ssh-copy-id` | [ ] |
| 防火墙 | `ufw enable + allow 80/443/22` | [ ] |
| SSH 加固 | 修改 sshd_config | [ ] |
| fail2ban | `apt install fail2ban` | [ ] |
| ulimit | `nofile 65535` | [ ] |
| sysctl | 内核网络参数调优 | [ ] |
| 目录结构 | `/opt/ecommerce/{backend,logs,scripts,backup}` | [ ] |

### Nginx 配置速查

| 配置 | 说明 |
|------|------|
| `worker_processes auto` | 工作进程数=CPU核数 |
| `worker_connections 10240` | 每进程最大连接数 |
| `upstream backend {}` | 定义后端服务器组 |
| `proxy_pass http://backend` | 反向代理到后端 |
| `proxy_set_header Host $host` | 传递原始 Host 头 |
| `proxy_set_header X-Real-IP $remote_addr` | 传递真实客户端 IP |
| `gzip on` | 开启压缩 |
| `client_max_body_size 20m` | 上传大小限制 |

### 部署流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    全栈部署流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  01-server-init.sh（服务器初始化）                          │
│    ↓                                                        │
│  03-deploy-full-stack.sh（一键部署）                        │
│    ├─ 安装 Nginx                                            │
│    ├─ 安装 MySQL                                            │
│    ├─ 安装 Redis                                            │
│    ├─ 安装 Node.js + nvm                                    │
│    ├─ 安装 PM2                                              │
│    ├─ 配置 Nginx 反向代理（02-deploy-nginx-reverse-proxy.conf）│
│    ├─ 启动 Node.js 应用（PM2 多实例）                       │
│    ├─ 配置开机自启                                          │
│    └─ 验证服务状态                                          │
│    ↓                                                        │
│  04-mysql-backup.sh（定时备份）                             │
│    ↓                                                        │
│  日常运维（05-ops-best-practices.md）                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 传统部署 vs Docker 对比表

| 对比项 | 传统部署 | Docker 部署 |
|--------|---------|------------|
| 环境一致性 | 差（依赖系统环境） | 好（镜像即环境） |
| 隔离性 | 弱（进程级） | 强（容器级） |
| 部署速度 | 慢（装依赖） | 快（拉镜像） |
| 资源开销 | 无额外 | 少量额外 |
| 学习成本 | 低 | 中 |
| 适合场景 | 简单/单机 | 复杂/微服务 |
| 回滚难度 | 难 | 易（切镜像） |
| 扩缩容 | 手动 | 容易（scale） |

### 运维最佳实践清单

| 实践 | 说明 |
|------|------|
| 监控告警 | 部署 Prometheus + Grafana，关键指标告警 |
| 日志管理 | 集中收集（ELK），logrotate 轮转 |
| 备份恢复 | 3-2-1 原则，定期恢复测试 |
| 自动化 | 脚本/Ansible 自动化部署 |
| CI/CD | 自动构建测试部署 |
| 安全加固 | 防火墙+SSH+fail2ban+审计 |
| 性能调优 | 四维度排查，内核参数调优 |
| 容量规划 | 监控趋势，提前扩容 |
| 灾备方案 | 异地备份，故障切换 |
| 文档管理 | 运维手册，操作记录 |

---

## 实战练习

### 练习 1：服务器初始化实战

**场景**：拿到一台全新的 Ubuntu 22.04 服务器，完成初始化。

**任务**：

1. 执行 `01-server-init.sh` 完成服务器初始化
2. 验证 deploy 用户创建成功且具有 sudo 权限
3. 验证 SSH 密钥登录可用、密码登录被拒绝
4. 验证防火墙规则正确（80/443/SSH 放行，3306/6379 拒绝）
5. 验证 ulimit 和 sysctl 参数已调优

**验收**：所有初始化项检查通过，服务器处于安全可用状态。

### 练习 2：全栈服务部署

**场景**：在初始化完成的服务器上部署电商全栈服务。

**任务**：

1. 执行 `03-deploy-full-stack.sh` 完成一键部署
2. 验证 Nginx 正常运行，访问 `http://192.168.1.100` 返回正常
3. 验证 MySQL 运行，能登录并创建数据库
4. 验证 Redis 运行，能连接并设置密码
5. 验证 Node.js 应用通过 PM2 运行多实例
6. 验证 Nginx 反向代理到 Node.js 正常工作
7. 配置 MySQL 自动备份并验证

**验收**：所有服务运行正常，通过 Nginx 访问能看到应用响应。

### 练习 3：运维流程设计

**场景**：为电商项目设计完整的运维流程。

**任务**：

1. 编写每日巡检脚本（检查服务状态、磁盘空间、日志异常）
2. 配置 MySQL 每日凌晨 2 点自动备份，保留 30 天
3. 设计故障应急响应流程（服务挂掉 → 排查 → 恢复 → 复盘）
4. 编写一份运维文档，包含：部署步骤、日常巡检清单、故障处理预案
5. 思考：如果要用 Docker 改造现有部署，需要哪些步骤？

**验收**：巡检脚本可执行，备份任务已配置，运维文档完整。

---

> **恭喜！** 完成 Day14 即完成了 Linux 学习模块的全部 14 天内容。你已具备从空白服务器到全栈服务部署的完整运维能力。后续推荐学习 Docker、Kubernetes、CI/CD 等进阶主题，将运维能力提升到新的高度。
