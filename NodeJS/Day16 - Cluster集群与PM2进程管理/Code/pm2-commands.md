# PM2 常用命令速查

> 配合 `ecosystem.config.js` 使用。假设应用名为 `ai-api`。
> 全局安装：`npm install -g pm2`

---

## 一、生命周期命令

| 命令 | 作用 | 示例 |
|------|------|------|
| `pm2 start` | 启动应用 | `pm2 start app.js` <br> `pm2 start ecosystem.config.js` <br> `pm2 start ecosystem.config.js --env production` |
| `pm2 stop` | 停止应用（保留进程记录，不删除） | `pm2 stop ai-api` <br> `pm2 stop all` |
| `pm2 restart` | 重启应用（杀掉再起，**有短暂不可用**） | `pm2 restart ai-api` <br> `pm2 restart ecosystem.config.js --env production` |
| `pm2 reload` | **零停机重载**（逐个重启 worker，仅 cluster 模式） | `pm2 reload ai-api` <br> `pm2 reload ecosystem.config.js --update-env` |
| `pm2 delete` | 删除应用（从进程列表移除，stop + 清记录） | `pm2 delete ai-api` <br> `pm2 delete all` |

> `restart` vs `reload`：发布新代码用 `reload`（零停机）；配置大改、紧急恢复用 `restart`。`reload` 仅对 `exec_mode: 'cluster'` 生效，`fork` 模式会回退成 `restart`。

---

## 二、查看与监控

| 命令 | 作用 | 示例 |
|------|------|------|
| `pm2 status` / `pm2 ls` / `pm2 list` | 查看进程列表与状态 | `pm2 status` |
| `pm2 describe` | 查看某应用详细信息（脚本、重启次数、日志路径等） | `pm2 describe ai-api` |
| `pm2 monit` | 终端面板，实时看 CPU / 内存 / 日志 | `pm2 monit` |
| `pm2 logs` | 查看日志（实时滚动） | `pm2 logs` <br> `pm2 logs ai-api` <br> `pm2 logs ai-api --lines 200` |
| `pm2 flush` | 清空所有日志文件内容（文件保留） | `pm2 flush` <br> `pm2 flush ai-api` |
| `pm2 env` | 查看某应用的环境变量 | `pm2 env 0`（按 id） |

---

## 三、持久化与开机自启

| 命令 | 作用 | 示例 |
|------|------|------|
| `pm2 save` | 保存当前进程列表到 `~/.pm2/dump.pm2` | `pm2 save` |
| `pm2 resurrect` | 从 dump 文件恢复进程列表（机器重启后用） | `pm2 resurrect` |
| `pm2 startup` | 生成开机自启脚本（systemd / upstart / launchd） | `pm2 startup` <br> `pm2 startup systemd` |
| `pm2 unstartup` | 移除开机自启脚本 | `pm2 unstartup` |

**开机自启两步走：**

```bash
# 1. 生成并安装开机自启脚本（会提示用 sudo 执行一条命令）
pm2 startup
# 复制它打印的 sudo 命令执行，例如：
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u youruser --hp /home/youruser

# 2. 保存当前进程列表（开机时用 resurrect 恢复）
pm2 save
```

> 每次新增 / 删除应用后都要重新 `pm2 save`，否则重启后恢复的是旧列表。

---

## 四、日志管理

| 命令 | 作用 |
|------|------|
| `pm2 logs` | 实时查看所有应用日志 |
| `pm2 logs ai-api` | 只看某应用 |
| `pm2 logs ai-api --lines 200` | 看最近 200 行 |
| `pm2 logs --err` | 只看错误日志 |
| `pm2 logs --out` | 只看输出日志 |
| `pm2 flush` | 清空日志内容（文件保留） |
| `pm2 install pm2-logrotate` | 安装日志切割模块 |
| `pm2 reload pm2-logrotate` | 重载 logrotate 配置 |

**日志切割配置：**

```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M              # 单文件超 10M 切割
pm2 set pm2-logrotate:retain 30                 # 保留 30 个历史文件
pm2 set pm2-logrotate:compress true             # 旧文件 gzip 压缩
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss
pm2 set pm2-logrotate:rotateInterval '0 0 * * *'  # 每天 0 点切割
```

日志默认路径：`~/.pm2/logs/<app-name>-out.log` 与 `<app-name>-error.log`。

---

## 五、常用组合流程

### 5.1 首次部署（裸机）

```bash
pm2 start ecosystem.config.js --env production   # 启动
pm2 save                                          # 保存进程列表
pm2 startup                                       # 生成开机自启（按提示 sudo 执行）
pm2 logs                                          # 观察启动日志是否正常
```

### 5.2 发布新版本（零停机）

```bash
git pull                                          # 拉新代码
npm install --omit=dev                            # 装依赖（若有变更）
pm2 reload ecosystem.config.js --env production   # 零停机重载
pm2 logs                                          # 观察是否正常
```

### 5.3 紧急回滚

```bash
git checkout <prev-tag>                           # 回退代码
pm2 restart ecosystem.config.js --env production  # 完全重启（reload 可能新旧混杂）
```

### 5.4 查看某应用为何频繁重启

```bash
pm2 describe ai-api      # 看 restart 次数、uptime
pm2 logs ai-api --err --lines 500   # 看错误日志
pm2 monit                # 实时看内存是否被 max_memory_restart 触发
```

---

## 六、其他常用

| 命令 | 作用 |
|------|------|
| `pm2 kill` | 杀掉 PM2 daemon（所有应用一起停，慎用） |
| `pm2 ping` | 检查 daemon 是否存活 |
| `pm2 reset` | 重置某应用的重启计数（不影响运行） |
| `pm2 jlist` | 以 JSON 输出进程列表（脚本消费用） |
| `pm2 scale ai-api +2` | cluster 模式动态扩容 2 个 worker |
| `pm2 scale ai-api 8` | 把 worker 数量调整为 8（增减都行） |

---

## 七、reload 期间的"版本混杂"现象

`pm2 reload` 是逐个替换 worker，新旧 worker 会短暂并存。期间：

- 部分请求打到新 worker（返回新版本）
- 部分请求打到尚未被替换的旧 worker（返回旧版本）
- **不会出现连接拒绝 / 502**（这是"零停机"的真正含义）

若业务对版本强一致敏感（如 API 字段结构变更、DB schema 变更），单纯 reload 可能导致客户端解析出错。此时应：

1. 用 `restart` 一次性切换（接受短暂停机），或
2. 做版本协商（客户端带版本号，服务端兼容多版本响应），或
3. 灰度发布（先 reload 部分实例，观察后再全量）。

> "零停机" ≠ "零版本混杂"。reload 保证的是"连接不中断"，不保证"所有请求同一版本"。
