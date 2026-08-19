# Day01 环境配置详细指南

本文件提供 Redis 7.0+ 环境的完整搭建步骤，覆盖 Docker、本地安装、redis-cli 配置、图形客户端配置四种方式。任选一种完成即可。

---

## 一、Docker 部署（推荐，零安装）

### 1.1 前置条件

已安装 Docker Desktop（Windows/Mac）或 Docker Engine（Linux）。验证：

```bash
docker --version
docker ps
```

### 1.2 启动 Redis 容器

**学习用（无密码）**：

```bash
docker run -d \
  --name redis-learn \
  -p 6379:6379 \
  -v redis-learn-data:/data \
  --restart=unless-stopped \
  redis:7
```

**生产推荐（带密码 + AOF 持久化）**：

```bash
docker run -d \
  --name redis-learn \
  -p 6379:6379 \
  -v redis-learn-data:/data \
  --restart=unless-stopped \
  redis:7 \
  --requirepass yourpassword \
  --appendonly yes
```

参数说明：

| 参数 | 说明 |
|------|------|
| `-d` | 后台运行 |
| `--name redis-learn` | 容器名 |
| `-p 6379:6379` | 端口映射（宿主机:容器） |
| `-v redis-learn-data:/data` | 数据卷挂载，避免容器删除后数据丢失 |
| `--restart=unless-stopped` | 开机自启，除非手动停止 |
| `--requirepass` | 设置访问密码 |
| `--appendonly yes` | 开启 AOF 持久化 |

### 1.3 连接与操作

```bash
# 进入容器内 redis-cli
docker exec -it redis-learn redis-cli

# 带密码连接
docker exec -it redis-learn redis-cli -a yourpassword

# 在宿主机执行单条命令
docker exec -it redis-learn redis-cli PING

# 管道执行脚本文件
docker exec -i redis-learn redis-cli < "Day01 - Redis基础与环境安装/Code/00-environment-check.redis"
```

### 1.4 容器管理

```bash
docker ps                       # 查看运行中的容器
docker logs redis-learn         # 查看日志
docker stop redis-learn         # 停止
docker start redis-learn        # 启动
docker restart redis-learn      # 重启
docker rm -f redis-learn        # 删除容器（保留数据卷）
docker volume rm redis-learn-data  # 删除数据卷（彻底清数据）
```

---

## 二、本地安装

### 2.1 Linux（Ubuntu/Debian）

```bash
# 1. 通过 apt 安装（版本可能略旧）
sudo apt update
sudo apt install redis-server

# 2. 启动服务
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 3. 验证
redis-server --version
redis-cli ping
```

### 2.2 Linux（源码编译，获取最新版）

```bash
# 1. 安装编译依赖
sudo apt install build-essential tcl

# 2. 下载源码
wget https://download.redis.io/releases/redis-7.2.5.tar.gz
tar xzf redis-7.2.5.tar.gz
cd redis-7.2.5

# 3. 编译并安装
make
sudo make install

# 4. 前台启动（默认端口 6379）
redis-server

# 5. 后台启动（指定配置）
redis-server --daemonize yes
redis-cli ping
```

### 2.3 macOS（Homebrew）

```bash
# 1. 安装
brew install redis

# 2. 启动服务（开机自启）
brew services start redis

# 3. 或前台启动
redis-server /opt/homebrew/etc/redis.conf

# 4. 验证
redis-cli ping
```

### 2.4 Windows

Redis 官方**不直接支持 Windows**，推荐方案：

1. **WSL2（首选）**：在 WSL2 的 Ubuntu 中按 2.1 步骤安装，性能接近原生 Linux。
2. **Docker Desktop**：按第一部分 Docker 方式部署。
3. 旧版 Microsoft 移植（已停止维护，不建议使用）。

WSL2 安装示例（在 PowerShell 中）：

```powershell
wsl --install -d Ubuntu
# 重启后进入 Ubuntu，按 Linux apt 方式安装 Redis
```

---

## 三、redis-cli 配置与使用

### 3.1 连接方式

```bash
redis-cli                          # 默认连接 127.0.0.1:6379
redis-cli -h 127.0.0.1 -p 6379     # 指定地址端口
redis-cli -a yourpassword          # 带密码连接（会有安全警告）
redis-cli --no-auth-warning -a yourpassword  # 带密码连接且不警告
redis-cli -n 1                     # 直接选择 DB 1
redis-cli -u redis://:yourpassword@127.0.0.1:6379/0  # URI 形式
```

### 3.2 常用启动参数

| 参数 | 说明 |
|------|------|
| `-h` | 主机地址 |
| `-p` | 端口 |
| `-a` | 密码 |
| `-n` | 数据库编号（0-15） |
| `--stat` | 实时监控统计信息 |
| `--latency` | 测量客户端到服务器的延迟 |
| `--bigkeys` | 扫描发现大 Key |
| `--hotkeys` | 扫描发现热 Key（需开启 LFU） |
| `--pipe` | 管道模式批量执行命令 |
| `--rdb` | 导出 RDB 文件 |
| `--scan` | 扫描所有 Key（替代 KEYS *） |

### 3.3 交互模式常用元命令

进入 `redis-cli` 后，可用以下命令：

```bash
127.0.0.1:6379> HELP                # 查看帮助
127.0.0.1:6379> HELP SET            # 查看某命令帮助
127.0.0.1:6379> SELECT 0            # 切换数据库
127.0.0.1:6379> EXIT                # 退出（或 quit / Ctrl+D）
127.0.0.1:6379> CLEAR               # 清屏
127.0.0.1:6379> SCAN 0              # 渐进扫描
```

### 3.4 单条命令直接执行

```bash
redis-cli SET mykey "hello"
redis-cli GET mykey
redis-cli INCR counter
redis-cli --no-raw GET mykey        # 不解析，显示原始类型
```

---

## 四、图形客户端配置

### 4.1 RedisInsight（官方推荐，免费）

- 下载：https://redis.io/insight/
- 跨平台（Windows/Mac/Linux）
- 支持 CLI、内存分析、Stream 查看、慢查询监控

**连接配置**：

| 字段 | 学习环境值 |
|------|-----------|
| Host | 127.0.0.1 |
| Port | 6379 |
| Name | redis-learn |
| Password | 空（无密码时）/ yourpassword |

### 4.2 Another Redis Desktop Manager（开源免费）

- 下载：https://github.com/qishibo/AnotherRedisDesktopManager
- 跨平台，界面简洁，适合入门

### 4.3 Redis Commander（Web 界面）

```bash
# Docker 一键启动
docker run -d --name redis-commander \
  -p 8081:8081 \
  -e REDIS_HOSTS=local:127.0.0.1:6379 \
  rediscommander/redis-commander:latest

# 浏览器访问 http://localhost:8081
```

### 4.4 DataGrip / IntelliJ（JetBrains）

- 已使用 JetBrains 全家桶可直接用 DataGrip
- 新建 Redis 数据源，配置 Host/Port/Password
- 支持命令补全、结果分页

---

## 五、验证环境是否就绪

完成任一安装方式后，执行以下命令确认环境合格：

```bash
# 1. 连通性
redis-cli PING
# 预期：PONG

# 2. 版本（需 >= 7.0）
redis-cli INFO server | grep redis_version
# 预期：redis_version:7.2.x

# 3. 数据库数量
redis-cli CONFIG GET databases
# 预期：16

# 4. 简单读写
redis-cli SET hello "world"
redis-cli GET hello
# 预期：world
```

全部通过后，即可开始执行本目录下的 `.redis` 脚本。

---

## 六、常见问题

**Q1：`redis-cli ping` 返回 `Could not connect to Redis at 127.0.0.1:6379: Connection refused`？**
- 服务未启动：`docker ps` 看容器是否在运行；本地安装用 `systemctl status redis` 检查。
- 端口被占用：`netstat -ano | findstr 6379`（Windows）/ `lsof -i:6379`（Mac/Linux）。

**Q2：连接带密码的 Redis 提示 `NOAUTH Authentication required`？**
- 未带密码：`redis-cli -a yourpassword`。

**Q3：Windows 下 `.redis` 文件含中文，管道执行报错？**
- 确保文件编码为 UTF-8 无 BOM。
- 路径含中文或空格时用双引号包裹。

**Q4：Docker 容器重启后数据丢失？**
- 未挂载数据卷：启动时加 `-v redis-learn-data:/data`。
- 未开启持久化：启动时加 `--appendonly yes`。
