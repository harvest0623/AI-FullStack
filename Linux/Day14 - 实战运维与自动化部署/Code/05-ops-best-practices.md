# 运维最佳实践

> 本文档是 Day14 实战运维与自动化部署的综合参考，涵盖日常运维流程、故障排查方法论、备份恢复策略、监控告警体系、CI/CD 流程、IaC 理念、Docker 对比传统部署、生产环境检查清单、常用运维命令速查卡。

---

## 一、日常运维流程

### 1.1 每日巡检清单

| 巡检项 | 命令 | 正常状态 |
|--------|------|---------|
| 系统负载 | `uptime` | load < CPU 核数 |
| CPU 使用率 | `top -b -n 1 \| head -5` | %id > 20% |
| 内存使用 | `free -h` | available > 20% |
| 磁盘空间 | `df -h` | 使用率 < 85% |
| 磁盘 IO | `iostat -x 1 3` | %util < 90% |
| 网络连接 | `ss -s` | 连接数正常 |
| Nginx 状态 | `systemctl status nginx` | active (running) |
| MySQL 状态 | `systemctl status mysql` | active (running) |
| Redis 状态 | `systemctl status redis-server` | active (running) |
| Node.js 状态 | `pm2 status` | online |
| 错误日志 | `tail -100 /var/log/nginx/error.log` | 无异常错误 |
| 登录失败 | `lastb \| head -20` | 无大量失败 |
| 备份状态 | `ls -lt /opt/ecommerce/backup/` | 有今日备份 |

### 1.2 每日巡检脚本

```bash
#!/bin/bash
# 日常巡检脚本 - 放在 /opt/ecommerce/scripts/daily-check.sh

REPORT="/var/log/daily-check-$(date +%Y%m%d).log"
echo "========== 日常巡检 $(date) ==========" > "${REPORT}"

echo "[1] 系统负载：" >> "${REPORT}"
uptime >> "${REPORT}"

echo -e "\n[2] 内存使用：" >> "${REPORT}"
free -h >> "${REPORT}"

echo -e "\n[3] 磁盘空间：" >> "${REPORT}"
df -h >> "${REPORT}"

echo -e "\n[4] 服务状态：" >> "${REPORT}"
systemctl is-active nginx mysql redis-server >> "${REPORT}"

echo -e "\n[5] PM2 状态：" >> "${REPORT}"
su - deploy -c 'source ~/.nvm/nvm.sh && pm2 status' >> "${REPORT}" 2>&1

echo -e "\n[6] 监听端口：" >> "${REPORT}"
ss -tlnp >> "${REPORT}"

echo -e "\n[7] 最近登录失败：" >> "${REPORT}"
lastb 2>/dev/null | head -10 >> "${REPORT}"

echo -e "\n[8] Nginx 错误日志（最近 20 条）：" >> "${REPORT}"
tail -20 /var/log/nginx/error.log >> "${REPORT}" 2>/dev/null

echo "巡检报告已生成：${REPORT}"
```

### 1.3 巡检任务自动化

```bash
# 配置 cron 每天早上 8 点执行巡检
echo "0 8 * * * root /opt/ecommerce/scripts/daily-check.sh" | sudo tee /etc/cron.d/daily-check
```

### 1.4 运维周期表

| 周期 | 任务 |
|------|------|
| **每日** | 巡检监控告警、服务状态、磁盘空间、日志异常 |
| **每周** | 系统安全补丁、备份恢复测试、日志归档、性能趋势分析 |
| **每月** | 容量评估、安全审计、架构优化、灾备演练 |
| **每季** | 灾难恢复演练、权限审查、SSL 证书更新、版本升级评估 |

---

## 二、故障排查方法论

### 2.1 故障处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                    故障处理流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 发现故障                                                 │
│     └─ 来源：监控告警 / 用户反馈 / 巡检发现                  │
│                                                             │
│  2. 确认影响                                                 │
│     └─ 什么服务？什么时间？影响范围？严重程度？              │
│                                                             │
│  3. 快速止血（先恢复，再定位）                               │
│     ├─ 重启服务：systemctl restart xxx                      │
│     ├─ 回滚：切回上一个版本                                  │
│     ├─ 扩容：加机器/加资源                                   │
│     └─ 降级：关闭非核心功能                                  │
│                                                             │
│  4. 定位根因                                                 │
│     ├─ 看监控：CPU/内存/磁盘/网络哪个异常？                  │
│     ├─ 看日志：systemctl status / journalctl / 应用日志     │
│     ├─ 用 Day12 方法论：load→CPU→内存→IO→网络               │
│     └─ 复现问题：测试环境复现                                │
│                                                             │
│  5. 修复故障                                                 │
│     └─ 修复代码 / 调整配置 / 扩容资源                       │
│                                                             │
│  6. 验证恢复                                                 │
│     └─ 服务可用 / 性能正常 / 监控正常                       │
│                                                             │
│  7. 复盘总结                                                 │
│     ├─ 根因分析（5 Why）                                    │
│     ├─ 改进措施（监控/流程/代码）                            │
│     └─ 文档记录                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 常见故障排查

| 故障现象 | 排查方向 | 常用命令 |
|---------|---------|---------|
| 服务无法访问 | Nginx 是否运行、端口是否监听 | `systemctl status nginx` / `ss -tlnp` |
| 502 Bad Gateway | 后端 Node.js 挂了或端口不对 | `pm2 status` / 检查 nginx upstream |
| 504 Gateway Timeout | 后端响应太慢 | 查 Node.js 日志、MySQL 慢查询 |
| 响应变慢 | CPU/内存/IO/网络瓶颈 | Day12 四维度排查 |
| 数据库连接失败 | MySQL 是否运行、密码对不对 | `systemctl status mysql` / `mysql -u root -p` |
| Redis 连接失败 | Redis 是否运行、密码对不对 | `redis-cli ping` |
| 磁盘满 | 日志/数据/临时文件 | `df -h` / `du -sh /*` |
| 内存不足 | OOM、swap 频繁 | `dmesg \| grep oom` / `free -h` |
| SSH 连不上 | 防火墙、sshd、网络 | `ufw status` / `systemctl status sshd` |

### 2.3 日志查看技巧

```bash
# systemd 服务日志
journalctl -u nginx -f              # 实时跟踪 Nginx 日志
journalctl -u mysql --since today   # 今天的 MySQL 日志
journalctl -p err                   # 错误级别日志

# Nginx 日志
tail -f /var/log/nginx/error.log    # 实时错误日志
tail -f /var/log/nginx/access.log   # 实时访问日志
grep "500\|502\|503\|504" /var/log/nginx/access.log  # 5xx 错误

# MySQL 日志
tail -f /var/log/mysql/error.log    # MySQL 错误日志
tail -f /var/log/mysql/slow.log     # 慢查询日志

# Node.js 日志（PM2）
pm2 logs ecommerce -f               # 实时日志
pm2 logs ecommerce --lines 100      # 最近 100 行
pm2 logs ecommerce --err            # 只看错误日志

# 系统日志
tail -f /var/log/syslog             # 系统日志
tail -f /var/log/auth.log           # 认证日志
dmesg -T                            # 内核日志（带时间戳）
```

---

## 三、备份恢复策略（3-2-1 原则）

### 3.1 3-2-1 原则详解

| 原则 | 说明 | 实现方式 |
|------|------|---------|
| **3** 份数据 | 至少保留 3 份数据 | 生产数据 + 本地备份 + 异地备份 |
| **2** 种介质 | 存储在 2 种不同介质 | 本地磁盘 + 对象存储（OSS/S3） |
| **1** 份异地 | 至少 1 份在异地 | 云存储 / 异地机房 |

### 3.2 电商场景备份策略

| 数据类型 | 备份方式 | 频率 | 保留时间 | 存储 |
|---------|---------|------|---------|------|
| MySQL 全量 | mysqldump | 每天凌晨 2 点 | 30 天 | 本地 + OSS |
| MySQL binlog | binlog 复制 | 实时 | 7 天 | 本地 |
| Redis RDB | redis BGSAVE | 每 6 小时 | 7 天 | 本地 |
| Nginx 日志 | logrotate + 归档 | 每天 | 90 天 | 本地 + OSS |
| 应用代码 | Git 仓库 | 每次提交 | 永久 | Git 服务器 |
| 配置文件 | 版本控制 | 每次修改 | 永久 | Git 仓库 |

### 3.3 备份恢复演练

**定期恢复测试（每月一次）**：

```bash
# 1. 在测试环境恢复备份
mysql -u root -p -e 'CREATE DATABASE ecommerce_test'
gunzip < /opt/ecommerce/backup/mysql/ecommerce_20260101.sql.gz | \
  mysql -u root -p ecommerce_test

# 2. 验证数据完整性
mysql -u root -p -e 'SELECT COUNT(*) FROM ecommerce_test.users'
mysql -u root -p -e 'SELECT COUNT(*) FROM ecommerce_test.orders'

# 3. 对比生产数据
PROD_COUNT=$(mysql -u root -p ecommerce -e 'SELECT COUNT(*) FROM users' -s)
TEST_COUNT=$(mysql -u root -p ecommerce_test -e 'SELECT COUNT(*) FROM users' -s)
echo "生产：${PROD_COUNT}，测试：${TEST_COUNT}"

# 4. 清理测试数据
mysql -u root -p -e 'DROP DATABASE ecommerce_test'
```

---

## 四、监控告警体系

### 4.1 监控分层

```
┌─────────────────────────────────────────────────────────────┐
│                      监控告警体系                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  采集   ┌─────────────┐  告警   ┌───────┐ │
│  │  被监控节点  │ ────→  │ Prometheus  │ ────→  │ 运维  │ │
│  │             │        │             │        │       │ │
│  │ Node Exporter│       │ (时序数据库) │        │ 邮件  │ │
│  │ MySQL Exporter│      │             │        │ 短信  │ │
│  │ Redis Exporter│      │  PromQL     │        │ 钉钉  │ │
│  │ Nginx Exporter│      │  查询       │        │ 飞书  │ │
│  └─────────────┘        └──────┬──────┘        └───────┘ │
│                                │                            │
│                                ▼                            │
│                         ┌─────────────┐                    │
│                         │   Grafana   │                    │
│                         │  (可视化)   │                    │
│                         │  仪表盘     │                    │
│                         └─────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 告警规则示例

| 指标 | 条件 | 持续时间 | 级别 |
|------|------|---------|------|
| 服务存活 | down | 立即 | P0 紧急 |
| CPU 使用率 | > 90% | 5 分钟 | P1 重要 |
| 内存可用 | < 10% | 5 分钟 | P1 重要 |
| 磁盘使用率 | > 85% | 立即 | P1 重要 |
| 磁盘使用率 | > 95% | 立即 | P0 紧急 |
| HTTP 5xx 错误率 | > 1% | 5 分钟 | P1 重要 |
| 响应时间 | > 2s | 5 分钟 | P2 一般 |
| MySQL 连接数 | > 80% | 5 分钟 | P1 重要 |
| Redis 内存 | > 90% | 立即 | P1 重要 |
| 备份失败 | 失败 | 立即 | P0 紧急 |

### 4.3 告警通知渠道

```yaml
# Alertmanager 配置示例
route:
  receiver: default
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: default
    webhook_configs:
      - url: 'https://oapi.dingtalk.com/robot/send?access_token=xxx'
    # 或邮件
    email_configs:
      - to: 'ops@example.com'
        from: 'alert@example.com'
        smarthost: 'smtp.example.com:587'
```

---

## 五、CI/CD 流程简介

### 5.1 CI/CD 概念

| 概念 | 全称 | 说明 |
|------|------|------|
| **CI** | Continuous Integration | 持续集成：代码提交后自动构建+测试 |
| **CD** | Continuous Delivery | 持续交付：自动部署到测试/预发布环境 |
| **CD** | Continuous Deployment | 持续部署：自动部署到生产环境 |

### 5.2 CI/CD 流程

```
开发人员 → Git Push → CI 服务器 → 构建 → 测试 → 部署
  │          │          │         │      │      │
  │          │          │         │      │      ├─ 测试环境
  │          │          │         │      │      ├─ 预发布环境
  │          │          │         │      │      └─ 生产环境
  │          │          │         │      │
  │          │          │         │      ├─ 单元测试
  │          │          │         │      ├─ 集成测试
  │          │          │         │      └─ E2E 测试
  │          │          │         │
  │          │          │         ├─ npm install
  │          │          │         ├─ npm run build
  │          │          │         └─ Docker build
  │          │          │
  │          │          ├─ Jenkins
  │          │          ├─ GitHub Actions
  │          │          └─ GitLab CI
  │          │
  │          ├─ GitHub
  │          ├─ GitLab
  │          └─ Gitea
  │
  └─ 编写代码
```

### 5.3 GitHub Actions 示例

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci --production

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build

      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: deploy
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          port: 2222
          script: |
            cd /opt/ecommerce/backend
            git pull origin main
            npm install --production
            pm2 reload ecommerce
```

---

## 六、IaC（Infrastructure as Code）理念

### 6.1 什么是 IaC

**Infrastructure as Code**（基础设施即代码）是用代码（声明式或命令式）来定义、部署和管理基础设施的方式。

| 传统方式 | IaC 方式 |
|---------|---------|
| 手动在控制台操作 | 代码定义基础设施 |
| 不可复现 | 可重复执行 |
| 难以追踪变更 | 版本控制 |
| 环境不一致 | 环境一致 |
| 难以审计 | 代码可审查 |

### 6.2 IaC 工具对比

| 工具 | 类型 | 适用场景 | 示例 |
|------|------|---------|------|
| **Shell 脚本** | 命令式 | 单机配置、简单部署 | 本章脚本 |
| **Ansible** | 声明式 | 多机配置管理 | `apt: name=nginx state=present` |
| **Terraform** | 声明式 | 云资源编排 | `resource "aws_instance" "web"` |
| **Docker Compose** | 声明式 | 容器编排 | `services: nginx: image: nginx` |
| **Kubernetes** | 声明式 | 容器编排平台 | `Deployment` / `Service` |
| **Pulumi** | 命令式 | 云资源（用编程语言） | TypeScript/Python 定义 |

### 6.3 从 Shell 脚本到 Ansible 的演进

**Shell 脚本（本章方式）**：
```bash
apt install -y nginx
systemctl start nginx
systemctl enable nginx
```

**Ansible Playbook**：
```yaml
- name: Install and configure Nginx
  hosts: webservers
  tasks:
    - name: Install Nginx
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Start and enable Nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
```

---

## 七、Docker 对比传统部署

### 7.1 传统部署优劣

| 优势 | 劣势 |
|------|------|
| 直接用系统资源，无额外开销 | 环境依赖管理麻烦 |
| 学习成本低 | 环境不一致（开发≠生产） |
| 调试方便 | 部署慢（装依赖） |
| 无容器隔离开销 | 多应用依赖冲突 |
| 适合简单架构 | 扩缩容慢 |

### 7.2 Docker 部署优劣

| 优势 | 劣势 |
|------|------|
| 环境一致性（镜像即环境） | 有额外开销（虽小） |
| 隔离性好（容器级） | 需学习 Docker |
| 部署快（拉镜像秒级） | 持久化需额外管理 |
| 扩缩容容易 | 网络配置较复杂 |
| 回滚简单（切镜像） | 监控调试需适配 |
| 适合微服务架构 | 容器安全需关注 |

### 7.3 传统部署 vs Docker 完整对比

| 对比项 | 传统部署（本章） | Docker 部署 |
|--------|-----------------|------------|
| **环境搭建** | 手动装依赖 | 镜像即环境 |
| **隔离性** | 进程级 | 容器级 |
| **资源占用** | 直接用系统 | 少量额外 |
| **部署速度** | 慢（装依赖） | 快（拉镜像） |
| **环境一致性** | 差 | 好 |
| **回滚** | 难 | 易 |
| **扩缩容** | 手动 | 容易 |
| **学习成本** | 低 | 中 |
| **适合场景** | 简单/单机 | 复杂/微服务 |
| **监控** | 系统工具 | 需适配容器 |
| **日志** | 直接读文件 | docker logs / 收集 |
| **网络** | 直接用系统网络 | 容器网络 |

### 7.4 Docker 改造步骤

如果要将本章的传统部署改造为 Docker 部署：

```bash
# 1. 编写 Dockerfile（每个服务一个）
# backend/Dockerfile
# FROM node:18-alpine
# COPY . /app
# RUN npm ci --production
# CMD ["node", "app.js"]

# 2. 编写 docker-compose.yml
# version: '3.8'
# services:
#   nginx:
#     image: nginx:alpine
#     ports: ["80:80"]
#     volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]
#   app:
#     build: ./backend
#     deploy:
#       replicas: 4
#   mysql:
#     image: mysql:8.0
#     volumes: ["mysql_data:/var/lib/mysql"]
#   redis:
#     image: redis:7-alpine

# 3. 一键启动
# docker-compose up -d

# 4. 扩容
# docker-compose up -d --scale app=6
```

---

## 八、生产环境检查清单

### 8.1 上线前检查清单

| 类别 | 检查项 | 状态 |
|------|--------|------|
| **安全** | 防火墙已启用，规则正确 | [ ] |
| **安全** | SSH 已加固（改端口/禁root/密钥） | [ ] |
| **安全** | fail2ban 已运行 | [ ] |
| **安全** | 数据库密码已设置且强密码 | [ ] |
| **安全** | Redis 已设密码 | [ ] |
| **安全** | 无默认密码/弱密码 | [ ] |
| **性能** | ulimit 文件描述符 65535 | [ ] |
| **性能** | sysctl 内核参数已调优 | [ ] |
| **性能** | MySQL innodb_buffer_pool_size 合理 | [ ] |
| **性能** | Redis maxmemory 已设置 | [ ] |
| **性能** | Nginx worker_connections 调优 | [ ] |
| **可用性** | 所有服务设置开机自启 | [ ] |
| **可用性** | PM2 开机自启已配置 | [ ] |
| **可用性** | 数据库主从复制（如需高可用） | [ ] |
| **备份** | MySQL 定时备份已配置 | [ ] |
| **备份** | 备份文件已上传异地 | [ ] |
| **备份** | 恢复流程已验证 | [ ] |
| **监控** | Prometheus + Node Exporter 已部署 | [ ] |
| **监控** | 关键指标告警已配置 | [ ] |
| **监控** | 告警通知渠道已测试 | [ ] |
| **日志** | 日志轮转 logrotate 已配置 | [ ] |
| **日志** | 日志保留策略合理 | [ ] |
| **网络** | HTTPS 证书已配置 | [ ] |
| **网络** | HTTP 自动重定向到 HTTPS | [ ] |
| **网络** | CDN 已配置（静态资源） | [ ] |
| **文档** | 部署文档已编写 | [ ] |
| **文档** | 运维手册已编写 | [ ] |
| **文档** | 应急预案已制定 | [ ] |

---

## 九、常用运维命令速查卡

### 9.1 服务管理

```bash
# systemd 服务管理
systemctl start nginx          # 启动
systemctl stop nginx           # 停止
systemctl restart nginx        # 重启
systemctl reload nginx         # 重载配置
systemctl status nginx         # 查看状态
systemctl enable nginx         # 开机自启
systemctl disable nginx        # 禁用开机自启
systemctl is-active nginx      # 是否运行
systemctl is-enabled nginx     # 是否开机自启

# 查看所有运行中的服务
systemctl list-units --type=service --state=running

# 查看日志
journalctl -u nginx -f         # 实时日志
journalctl -u nginx --since today
journalctl -u nginx -p err
```

### 9.2 进程管理

```bash
# 查看进程
ps aux                          # 所有进程
ps aux | grep nginx             # 过滤 nginx
top                             # 实时监控
htop                            # 增强版 top
pstree -p                       # 树形显示

# 进程控制
kill PID                        # 发送 SIGTERM
kill -9 PID                     # 强制杀死
killall nginx                   # 按名杀进程
pkill -f "node app.js"          # 按命令行匹配杀

# 后台运行
nohup command &                 # 不挂断运行
command &                       # 后台运行
jobs                            # 查看后台任务
fg                              # 调到前台
bg                              # 调到后台
```

### 9.3 网络排查

```bash
# 连接查看
ss -tlnp                        # 监听端口
ss -t -a                        # 所有 TCP 连接
ss -s                           # 连接统计

# 连通性
ping host                       # 连通测试
telnet host port                # 端口连通
nc -zv host port                # 端口连通
curl -I http://host             # HTTP 头
curl -w "@-" -o /dev/null -s URL  # 请求耗时

# 路由追踪
traceroute host
mtr host

# DNS
dig domain
nslookup domain
host domain
```

### 9.4 磁盘管理

```bash
# 磁盘使用
df -h                           # 分区使用率
du -sh /path                    # 目录大小
du -sh /* | sort -rh | head     # 根目录下最大的目录
ncdu /                          # 交互式磁盘分析

# 文件查找
find / -name "*.log" -size +100M  # 找大于 100M 的日志
find / -mtime -1 -type f          # 找最近 1 天修改的文件

# 挂载
mount /dev/sdb1 /mnt            # 挂载
umount /mnt                     # 卸载
lsblk                           # 查看块设备
```

### 9.5 性能监控

```bash
# CPU
uptime                          # 负载
top -b -n 1 | head -5           # CPU 使用率
mpstat 1 3                      # 多核 CPU

# 内存
free -h                         # 内存概览
vmstat 1 5                      # 内存与 IO
smem -r -k | head -20           # 进程内存

# 磁盘 IO
iostat -x 1 3                   # 磁盘 IO
iotop -oP                       # 进程 IO

# 网络
iftop -i eth0 -n -P             # 带宽
nethogs eth0                    # 进程网络
sar -n DEV 1                    # 网络历史

# 综合
dstat -tcmdn                    # 综合监控
glances                         # 全屏监控
```

### 9.6 文件操作

```bash
# 查找
find /path -name "*.conf"       # 按名查找
find /path -mtime -7            # 最近 7 天修改
locate filename                 # 快速查找（需 updatedb）

# 文本处理
grep "error" /var/log/syslog    # 搜索
grep -r "keyword" /path/        # 递归搜索
sed -i 's/old/new/g' file       # 替换
awk '{print $1}' file           # 提取字段
tail -f file                    # 实时跟踪
head -100 file                  # 前 100 行

# 压缩
tar -czf archive.tar.gz dir/    # 压缩
tar -xzf archive.tar.gz         # 解压
gzip file                       # 压缩
gunzip file.gz                  # 解压
zip -r archive.zip dir/         # zip 压缩
unzip archive.zip               # zip 解压
```

### 9.7 定时任务

```bash
# crontab
crontab -e                      # 编辑
crontab -l                      # 查看
crontab -r                      # 删除所有

# 系统级 cron
ls /etc/cron.d/                 # 系统定时任务
cat /etc/crontab                # 系统 cron 表

# 表达式
# */5 * * * *   → 每 5 分钟
# 0 2 * * *     → 每天凌晨 2 点
# 0 * * * 0     → 每周日凌晨
```

---

## 十、运维学习路线建议

### 10.1 进阶学习路径

```
当前位置（完成 Linux 14 天）
        │
        ▼
┌─────────────────────────────────────────────────┐
│  阶段一：容器化                                   │
│  Docker → Docker Compose → 容器化改造现有项目    │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  阶段二：CI/CD                                    │
│  Git → GitHub Actions/GitLab CI → 自动化部署     │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  阶段三：配置管理                                 │
│  Ansible → 批量管理多台服务器                     │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  阶段四：云原生                                   │
│  Kubernetes → 微服务架构 → 服务网格              │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  阶段五：可观测性                                 │
│  Prometheus → Grafana → ELK → 链路追踪          │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  阶段六：云平台                                   │
│  AWS/阿里云/腾讯云 → Terraform → 多云管理        │
└─────────────────────────────────────────────────┘
```

### 10.2 推荐资源

| 主题 | 资源 |
|------|------|
| Docker | Docker 官方文档、Docker — 从入门到实践 |
| Kubernetes | Kubernetes 官方文档、K8s 进阶实战 |
| Ansible | Ansible 官方文档、Ansible 权威指南 |
| Prometheus | Prometheus 官方文档、Prometheus 实战 |
| CI/CD | GitHub Actions 文档、GitLab CI 文档 |
| 云平台 | AWS/阿里云认证课程 |

---

> **相关文件**：
> - `01-server-init.sh` - 服务器初始化脚本
> - `02-deploy-nginx-reverse-proxy.conf` - Nginx 反向代理配置
> - `03-deploy-full-stack.sh` - 全栈一键部署脚本
> - `04-mysql-backup.sh` - MySQL 自动备份脚本
> - `05-ops-best-practices.md` - 本文档（运维最佳实践）

---

> **恭喜完成 Linux 学习模块！** 14 天的系统学习让你具备了从空白服务器到全栈部署的完整运维能力。继续学习 Docker、Kubernetes、CI/CD，将你的运维能力提升到云原生时代的新高度。
