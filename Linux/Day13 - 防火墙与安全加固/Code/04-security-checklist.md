# 安全加固清单

> 本文档是 Day13 防火墙与安全加固的综合参考，涵盖系统安全检查清单、端口扫描方法、服务最小化建议、自动安全更新配置、auditd 审计配置、nmap 自检步骤、生产环境安全建议汇总。

---

## 一、系统安全检查清单

### 1.1 检查清单总表

| 类别 | 检查项 | 命令 | 期望状态 |
|------|--------|------|---------|
| **防火墙** | ufw 已启用 | `ufw status` | Status: active |
| **防火墙** | 默认拒绝入站 | `ufw status verbose` | Default: deny (incoming) |
| **防火墙** | 只开放必要端口 | `ufw status` | 仅 22/80/443 等 |
| **防火墙** | 数据库端口拒绝外部 | `ufw status` | 3306/6379 DENY |
| **SSH** | 非默认端口 | `grep Port /etc/ssh/sshd_config` | Port 2222 |
| **SSH** | 禁止 root 登录 | `grep PermitRootLogin /etc/ssh/sshd_config` | no |
| **SSH** | 禁用密码 | `grep PasswordAuthentication /etc/ssh/sshd_config` | no |
| **SSH** | 用户白名单 | `grep AllowUsers /etc/ssh/sshd_config` | deploy |
| **入侵防护** | fail2ban 运行中 | `systemctl is-active fail2ban` | active |
| **系统更新** | 已安装安全补丁 | `apt list --upgradable` | 无安全更新 |
| **服务最小化** | 关闭无用服务 | `systemctl list-unit-files --state=enabled` | 仅必要服务 |
| **权限** | 应用非 root 运行 | `ps aux \| grep nginx` | www-data |
| **权限** | sudo 仅必要用户 | `grep sudo /etc/group` | 仅 deploy |
| **文件** | 配置文件权限 | `ls -l /etc/ssh/sshd_config` | 600 |
| **审计** | auditd 运行中 | `systemctl is-active auditd` | active |

### 1.2 一键检查脚本

```bash
#!/bin/bash
# 系统安全快速检查脚本

echo "========== 系统安全检查 =========="

# 1. 防火墙状态
echo "[1] 防火墙状态："
ufw status 2>/dev/null || firewall-cmd --state 2>/dev/null || echo "  未安装防火墙"

# 2. SSH 配置
echo "[2] SSH 配置："
echo "  端口：$(grep -E '^Port' /etc/ssh/sshd_config 2>/dev/null || echo '22 (默认)')"
echo "  Root 登录：$(grep -E '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo 'yes (默认)')"
echo "  密码认证：$(grep -E '^PasswordAuthentication' /etc/ssh/sshd_config 2>/dev/null || echo 'yes (默认)')"

# 3. fail2ban 状态
echo "[3] fail2ban 状态："
systemctl is-active fail2ban 2>/dev/null && fail2ban-client status sshd 2>/dev/null || echo "  fail2ban 未运行"

# 4. 监听端口
echo "[4] 监听端口："
ss -tlnp | head -20

# 5. 系统更新
echo "[5] 可更新包数量：$(apt list --upgradable 2>/dev/null | wc -l)"

# 6. 登录失败记录
echo "[6] 最近登录失败（前 10 条）："
lastb 2>/dev/null | head -10 || echo "  无失败记录"

# 7. 当前登录用户
echo "[7] 当前登录用户："
who

echo "========== 检查完成 =========="
```

---

## 二、端口扫描方法

### 2.1 nmap 安装与使用

```bash
# 安装 nmap
sudo apt install -y nmap

# 扫描本机所有 TCP 端口（1-65535）
sudo nmap -sT -p- localhost

# 扫描指定端口
sudo nmap -sT -p 22,80,443,3306,6379 localhost

# 扫描 UDP 端口（需 root）
sudo nmap -sU -p 53,161 localhost

# 服务版本探测
sudo nmap -sV -p 80,443 localhost

# 操作系统探测
sudo nmap -O localhost

# 全功能扫描（慢但全面）
sudo nmap -A -p- localhost
```

### 2.2 nmap 输出解读

```
PORT     STATE    SERVICE      VERSION
22/tcp   open     ssh          OpenSSH 8.9p1 Ubuntu 3ubuntu0.1
80/tcp   open     http         nginx 1.18.0
443/tcp  open     https        nginx 1.18.0
3306/tcp filtered mysql        ← filtered 表示被防火墙过滤
6379/tcp filtered redis
```

| STATE | 含义 |
|-------|------|
| `open` | 端口开放，服务在监听 |
| `closed` | 端口关闭，无服务监听 |
| `filtered` | 被防火墙过滤，无法确定 |

### 2.3 不用 nmap 的端口检查

```bash
# 查看所有监听的 TCP 端口
ss -tlnp

# 查看所有监听的 UDP 端口
ss -ulnp

# 查看指定端口是否在监听
ss -tlnp | grep :80

# 查看某个端口被哪个进程占用
sudo lsof -i :80
sudo fuser 80/tcp
```

---

## 三、服务最小化建议

### 3.1 常见可关闭的服务

```bash
# 查看已启用的服务
systemctl list-unit-files --state=enabled

# 桌面环境相关（服务器不需要）
sudo systemctl disable bluetooth
sudo systemctl disable cups          # 打印服务
sudo systemctl disable avahi-daemon  # mDNS 服务发现
sudo systemctl disableModemManager   # 调制解调器管理
sudo systemctl disable gdm           # 图形登录

# 网络相关（按需）
sudo systemctl disable nfs-server    # NFS 文件共享（如不用）
sudo systemctl disable rpcbind       # RPC 服务（如不用 NFS）
sudo systemctl disable smbd          # Samba 文件共享（如不用）

# 其他
sudo systemctl disable snapd         # Snap 包管理（如不用）
sudo systemctl disable apport        # 崩溃报告
```

### 3.2 卸载不需要的软件

```bash
# 查看已安装的软件包数量
dpkg -l | wc -l

# 自动清理不需要的依赖
sudo apt autoremove --purge

# 清理缓存
sudo apt clean

# 卸载特定软件（示例）
sudo apt purge -y samba samba-common
sudo apt purge -y nfs-kernel-server
sudo apt purge -y rpcbind
```

### 3.3 必须保留的服务

| 服务 | 说明 |
|------|------|
| `sshd` | SSH 远程管理 |
| `ufw` / `firewalld` | 防火墙 |
| `fail2ban` | 入侵防护 |
| `nginx` | Web 服务 |
| `mysql` | 数据库 |
| `redis` | 缓存 |
| `systemd-resolved` | DNS 解析 |
| `cron` | 定时任务 |
| `rsyslog` | 系统日志 |
| `unattended-upgrades` | 自动安全更新 |

---

## 四、自动安全更新配置

### 4.1 安装与配置

```bash
# 安装自动更新工具
sudo apt install -y unattended-upgrades apt-listchanges

# 启用自动更新（交互式配置）
sudo dpkg-reconfigure -plow unattended-upgrades

# 或直接创建配置文件
sudo tee /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF
```

### 4.2 配置更新策略

```bash
sudo tee /etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
// 自动更新的来源
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

// 自动移除无用的依赖
Unattended-Upgrade::Remove-Unused-Dependencies "true";

// 自动重启（如需要）
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";

// 邮件通知（可选）
// Unattended-Upgrade::Mail "ops@example.com";
// Unattended-Upgrade::MailOnlyOnError "true";

// 不自动更新的包（黑名单）
Unattended-Upgrade::Package-Blacklist {
    // "nginx";
    // "mysql-server";
};
EOF
```

### 4.3 手动测试自动更新

```bash
# 模拟运行（dry-run）
sudo unattended-upgrade --dry-run -v

# 手动执行一次
sudo unattended-upgrade -v

# 查看更新日志
cat /var/log/unattended-upgrades/unattended-upgrades.log
```

---

## 五、auditd 审计配置

### 5.1 安装与启动

```bash
# 安装 auditd
sudo apt install -y auditd

# 启动并设置开机自启
sudo systemctl enable auditd
sudo systemctl start auditd
```

### 5.2 配置审计规则

```bash
# 查看当前审计规则
sudo auditctl -l

# 添加审计规则（临时，重启失效）
# -w 监控路径  -p 权限(w写/a属性/x执行/r读)  -k 关键词
sudo auditctl -w /etc/passwd -p wa -k user_modification       # 监控用户修改
sudo auditctl -w /etc/shadow -p wa -k user_modification       # 监控密码文件
sudo auditctl -w /etc/sudoers -p wa -k sudo_modification      # 监控 sudoers
sudo auditctl -w /etc/ssh/sshd_config -p wa -k ssh_config     # 监控 SSH 配置
sudo auditctl -w /etc/nginx/nginx.conf -p wa -k nginx_config  # 监控 Nginx 配置
sudo auditctl -w /etc/mysql/ -p wa -k mysql_config            # 监控 MySQL 配置
sudo auditctl -w /bin/login -p x -k login_activity            # 监控登录命令
sudo auditctl -w /var/log/auth.log -p wa -k auth_log          # 监控认证日志
```

### 5.3 永久审计规则

```bash
# 永久规则写入 /etc/audit/rules.d/audit.rules
sudo tee /etc/audit/rules.d/hardening.rules <<'EOF'
# 用户与权限文件监控
-w /etc/passwd -p wa -k user_modification
-w /etc/shadow -p wa -k user_modification
-w /etc/group -p wa -k user_modification
-w /etc/sudoers -p wa -k sudo_modification
-w /etc/sudoers.d/ -p wa -k sudo_modification

# 服务配置文件监控
-w /etc/ssh/sshd_config -p wa -k ssh_config
-w /etc/nginx/nginx.conf -p wa -k nginx_config
-w /etc/mysql/ -p wa -k mysql_config
-w /etc/redis/ -p wa -k redis_config

# 系统关键文件
-w /etc/hosts -p wa -k hosts_modification
-w /etc/resolv.conf -p wa -k dns_modification
-w /etc/crontab -p wa -k cron_modification

# 登录活动
-w /bin/login -p x -k login_activity
-w /var/log/auth.log -p wa -k auth_log

# 系统调用监控（可选，有性能影响）
# -a always,exit -F arch=b64 -S unlink -S unlinkat -S rmdir -k file_delete
# -a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k file_perm_change
EOF

# 重新加载审计规则
sudo augenrules --load
```

### 5.4 查询审计日志

```bash
# 查询指定关键词的审计记录
sudo ausearch -k user_modification
sudo ausearch -k ssh_config

# 查询今天的审计记录
sudo ausearch -ts today

# 查询指定时间范围
sudo ausearch -ts today -te now -k ssh_config

# 查询指定用户
sudo ausearch -ua deploy

# 生成审计报告
sudo aureport --summary
sudo aureport -k     # 按关键词报告
sudo aureport -f     # 按文件报告
sudo aureport -l     # 按登录报告

# 实时监控审计事件
sudo tail -f /var/log/audit/audit.log
```

---

## 六、nmap 自检步骤

### 6.1 本地自检流程

```bash
# Step 1: 查看本机监听的所有端口
echo "=== Step 1: 监听端口 ==="
sudo ss -tlnp

# Step 2: 用 nmap 扫描本机所有 TCP 端口
echo "=== Step 2: nmap 全端口扫描 ==="
sudo nmap -sT -p- localhost

# Step 3: 扫描常见高危端口
echo "=== Step 3: 高危端口检查 ==="
sudo nmap -sT -p 21,22,23,25,53,69,111,135,137,139,161,389,445,512,513,514,873,1080,1433,1521,2049,2375,2376,3306,3389,5432,5900,5984,6379,6443,7001,8000,8080,8443,8888,9000,9090,9200,9300,11211,27017 localhost

# Step 4: 服务版本探测
echo "=== Step 4: 服务版本 ==="
sudo nmap -sV -p 22,80,443 localhost

# Step 5: 对比防火墙规则
echo "=== Step 5: 防火墙规则 ==="
sudo ufw status
```

### 6.2 外部扫描验证

```bash
# 从另一台机器扫描服务器（验证防火墙效果）
# 在外部机器执行：
nmap -sT -p 22,80,443,3306,6379 192.168.1.100

# 期望结果：
# 22/tcp（或 2222）  open     ← SSH 开放
# 80/tcp             open     ← HTTP 开放
# 443/tcp            open     ← HTTPS 开放
# 3306/tcp           filtered ← MySQL 被防火墙过滤
# 6379/tcp           filtered ← Redis 被防火墙过滤
```

---

## 七、登录审计

### 7.1 登录记录命令

```bash
# 查看登录成功记录（最近 20 条）
last -20

# 查看登录失败记录
sudo lastb -20

# 查看当前登录用户
who
w

# 查看每个用户最后一次登录
lastlog

# 查看 root 登录历史
last root | head -20

# 查看指定用户登录历史
last deploy | head -20
```

### 7.2 登录日志文件

| 日志文件 | 说明 |
|---------|------|
| `/var/log/auth.log` | 认证日志（SSH 登录、sudo 等） |
| `/var/log/wtmp` | 登录成功记录（`last` 读取） |
| `/var/log/btmp` | 登录失败记录（`lastb` 读取） |
| `/var/log/lastlog` | 最后登录记录（`lastlog` 读取） |

### 7.3 分析登录失败

```bash
# 统计登录失败的 IP（排查暴力破解）
sudo lastb | awk '{print $10}' | sort | uniq -c | sort -rn | head -20

# 查看 SSH 认证失败记录
sudo grep "Failed password" /var/log/auth.log | tail -20

# 统计 SSH 失败次数
sudo grep "Failed password" /var/log/auth.log | wc -l

# 查看成功登录的 IP
sudo grep "Accepted" /var/log/auth.log | tail -20
```

---

## 八、文件完整性检查（AIDE）

### 8.1 安装与初始化

```bash
# 安装 AIDE
sudo apt install -y aide

# 初始化 AIDE 数据库（首次运行，需几分钟）
sudo aideinit

# 将初始化数据库设为基准
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

### 8.2 定期检查

```bash
# 手动检查文件完整性
sudo aide --check

# 更新基准数据库（在确认变更合法后）
sudo aide --update
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# 配置 cron 定期检查（每天凌晨 3 点）
echo "0 3 * * * root /usr/bin/aide --check | mail -s 'AIDE Report' ops@example.com" | sudo tee /etc/cron.d/aide
```

### 8.3 AIDE 报告解读

```
AIDE found differences between database and filesystem!!

Summary:
  Total entries:  12345
  Added entries:  3        ← 新增文件
  Removed entries: 1       ← 删除文件
  Changed entries: 5       ← 修改文件
```

---

## 九、弱密码检查

### 9.1 john the ripper

```bash
# 安装 john
sudo apt install -y john

# 获取密码文件（合并 passwd 和 shadow）
sudo unshadow /etc/passwd /etc/shadow > /tmp/crack.txt

# 运行 john 尝试破解
john /tmp/crack.txt

# 查看已破解的密码
john --show /tmp/crack.txt

# 使用字典文件破解
john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/crack.txt
```

> **安全提示**：能被 john 快速破解的密码就是弱密码，应立即修改。强密码应至少 12 位，包含大小写字母、数字、特殊字符。

### 9.2 密码策略配置

```bash
# 安装密码质量检查工具
sudo apt install -y libpam-pwquality

# 配置密码策略
sudo tee /etc/security/pwquality.conf <<'EOF'
# 最小密码长度
minlen = 12
# 最少小写字母
minlower = 1
# 最少大写字母
minupper = 1
# 最少数字
minclass = 1
# 最少特殊字符
minclass = 1
# 新密码不能与旧密码相同
difok = 3
# 密码重用限制（/etc/pam.d/common-password 中配置 remember=5）
EOF
```

---

## 十、生产环境安全建议汇总表

| 类别 | 安全建议 | 优先级 |
|------|---------|--------|
| **网络层** | 启用防火墙，默认拒绝入站 | 高 |
| **网络层** | 只开放必要端口（80/443/SSH） | 高 |
| **网络层** | 数据库端口拒绝外部访问 | 高 |
| **网络层** | SSH 限制来源 IP | 中 |
| **SSH** | 修改默认端口 | 中 |
| **SSH** | 禁止 root 直接登录 | 高 |
| **SSH** | 禁用密码，仅密钥认证 | 高 |
| **SSH** | 配置用户白名单 | 中 |
| **SSH** | 设置登录超时断开 | 低 |
| **入侵防护** | 部署 fail2ban | 高 |
| **入侵防护** | SSH 失败封禁策略 | 高 |
| **系统更新** | 及时安装安全补丁 | 高 |
| **系统更新** | 配置自动安全更新 | 中 |
| **服务最小化** | 关闭无用服务 | 中 |
| **服务最小化** | 卸载不需要的软件 | 低 |
| **权限管理** | 应用以非 root 运行 | 高 |
| **权限管理** | sudo 仅授予必要用户 | 高 |
| **权限管理** | 关键文件权限 600 | 中 |
| **审计** | 部署 auditd 审计 | 中 |
| **审计** | 监控关键配置文件修改 | 中 |
| **审计** | 定期检查登录失败记录 | 中 |
| **文件完整性** | 部署 AIDE 文件完整性检查 | 低 |
| **密码安全** | 密码至少 12 位含大小写数字符号 | 中 |
| **密码安全** | 定期检查弱密码 | 低 |
| **备份** | 重要数据定期备份（3-2-1 原则） | 高 |
| **监控** | 服务/端口/登录异常告警 | 中 |
| **监控** | 部署 Prometheus + Grafana | 低 |
| **容器安全** | 容器以非 root 运行 | 中 |
| **容器安全** | 不使用最新标签，固定版本 | 低 |
| **SSL/TLS** | HTTPS 证书有效期监控 | 中 |
| **SSL/TLS** | 禁用旧版 TLS（1.0/1.1） | 中 |

---

## 十一、安全检查自动化

### 11.1 定期安全检查 cron

```bash
# 创建每日安全检查脚本
sudo tee /opt/ecommerce/scripts/daily-security-check.sh <<'EOF'
#!/bin/bash
# 每日安全检查脚本
REPORT="/var/log/security-check-$(date +%Y%m%d).log"

echo "========== 每日安全检查 $(date) ==========" > "${REPORT}"

# 1. 检查防火墙状态
echo "[1] 防火墙状态：" >> "${REPORT}"
ufw status >> "${REPORT}" 2>&1

# 2. 检查 fail2ban 状态
echo -e "\n[2] fail2ban 状态：" >> "${REPORT}"
fail2ban-client status sshd >> "${REPORT}" 2>&1

# 3. 检查登录失败
echo -e "\n[3] 最近 24 小时登录失败 IP Top 10：" >> "${REPORT}"
grep "Failed password" /var/log/auth.log 2>/dev/null | \
    awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10 >> "${REPORT}"

# 4. 检查监听端口
echo -e "\n[4] 当前监听端口：" >> "${REPORT}"
ss -tlnp >> "${REPORT}" 2>&1

# 5. 检查磁盘空间
echo -e "\n[5] 磁盘使用：" >> "${REPORT}"
df -h >> "${REPORT}" 2>&1

# 6. 检查可更新包
echo -e "\n[6] 可更新包数量：" >> "${REPORT}"
apt list --upgradable 2>/dev/null | wc -l >> "${REPORT}"

# 发送邮件（可选）
# mail -s "每日安全检查报告" ops@example.com < "${REPORT}"

echo "报告已生成：${REPORT}"
EOF

sudo chmod +x /opt/ecommerce/scripts/daily-security-check.sh

# 配置 cron 每天早上 8 点执行
echo "0 8 * * * root /opt/ecommerce/scripts/daily-security-check.sh" | sudo tee /etc/cron.d/daily-security-check
```

---

> **相关文件**：
> - `01-ufw-firewall.sh` - ufw 防火墙配置
> - `02-firewalld-firewall.sh` - firewalld 防火墙配置
> - `03-ssh-hardening.sh` - SSH 安全加固
> - `04-security-checklist.md` - 本文档（安全加固清单）
