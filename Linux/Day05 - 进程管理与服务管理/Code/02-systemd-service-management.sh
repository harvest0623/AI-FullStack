#!/bin/bash
# ============================================================
# 文件名：02-systemd-service-management.sh
# 用途：演示 systemd 服务管理核心命令：systemctl 生命周期管理、
#       状态查询、列表查询、开机自启、journalctl 日志查询
# 适用：Ubuntu 22.04 LTS
# 注意：本脚本含 sudo 命令，请以具备 sudo 权限的用户执行
# 场景：电商项目服务器（部署 Nginx + MySQL + Redis + Node.js）
# ============================================================

cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day05 - 02 systemd 服务管理演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"
echo "提示：本脚本含 sudo 命令，请以具备 sudo 权限的用户执行"
echo ""

# ---------- 1. systemd 基础信息 ----------

echo "[1] 验证 systemd 是否为系统初始化进程（PID 1）"
echo "命令：ps -p 1 -o pid,comm"
ps -p 1 -o pid,comm
echo ""
echo "命令：systemctl --version | head -n 1"
systemctl --version | head -n 1

# ---------- 2. systemctl 生命周期管理（以 nginx 为例） ----------

echo -e "\n[2] 服务生命周期管理（以 nginx 为例，未安装时跳过）"
if systemctl list-unit-files | grep -q '^nginx\.service'; then
    echo "命令：sudo systemctl status nginx        # 查看状态（不强加管道，避免状态码非 0 中断）"
    sudo systemctl status nginx --no-pager || true
    echo ""
    echo "命令：sudo systemctl is-active nginx      # 是否运行"
    sudo systemctl is-active nginx || true
    echo ""
    echo "命令：sudo systemctl is-enabled nginx     # 是否开机自启"
    sudo systemctl is-enabled nginx || true
else
    echo "nginx 服务未安装，可执行：sudo apt install -y nginx"
fi

echo -e "\n[3] 启动 / 停止 / 重启 / 重载 示例（仅打印命令，不真实执行以免影响环境）"
cat <<'EOF'
sudo systemctl start nginx          # 启动
sudo systemctl stop nginx           # 停止
sudo systemctl restart nginx        # 重启（中断服务）
sudo systemctl reload nginx         # 重载配置（不中断，推荐）
sudo systemctl enable --now nginx   # 启动并设置开机自启
sudo systemctl disable --now nginx  # 停止并禁用开机自启
EOF

# ---------- 3. 列表查询 ----------

echo -e "\n[4] 查看正在运行的服务（取前 10 个）"
echo "命令：systemctl list-units --type=service --state=running --no-pager | head -n 12"
systemctl list-units --type=service --state=running --no-pager | head -n 12

echo -e "\n[5] 查看失败的服务（运维巡检常用）"
echo "命令：systemctl list-units --type=service --state=failed --no-pager"
systemctl list-units --type=service --state=failed --no-pager || echo "（无失败服务，状态健康）"

echo -e "\n[6] 查看所有服务单元文件（取前 10 个）"
echo "命令：systemctl list-unit-files --type=service --no-pager | head -n 12"
systemctl list-unit-files --type=service --no-pager | head -n 12

echo -e "\n[7] 查看服务的依赖关系"
echo "命令：systemctl list-dependencies nginx --no-pager 2>/dev/null | head -n 15"
if systemctl list-unit-files | grep -q '^nginx\.service'; then
    systemctl list-dependencies nginx --no-pager 2>/dev/null | head -n 15
else
    echo "（nginx 未安装，跳过依赖展示）"
fi

# ---------- 4. 开机自启管理 ----------

echo -e "\n[8] 开机自启状态查询"
echo "命令：systemctl is-enabled nginx mysql redis-server 2>/dev/null"
for svc in nginx mysql redis-server; do
    if systemctl list-unit-files | grep -q "^${svc}\.service"; then
        state=$(systemctl is-enabled "$svc" 2>/dev/null || echo "not-found")
        printf "  %-15s %s\n" "$svc" "$state"
    fi
done

echo -e "\n[9] daemon-reload 说明"
echo "重要：每次修改 /etc/systemd/system/ 下的 .service 文件后必须执行"
echo "命令：sudo systemctl daemon-reload"
echo "否则 systemd 不会识别新配置"

echo -e "\n[10] mask / unmask —— 彻底禁用某服务"
cat <<'EOF'
sudo systemctl mask nginx       # 彻底禁用（即使被其他服务依赖也无法启动）
sudo systemctl unmask nginx     # 取消彻底禁用
说明：mask 会把单元文件软链到 /dev/null，优先级高于 enable
EOF

# ---------- 5. journalctl 日志查询 ----------

echo -e "\n[11] journalctl —— 查看某服务的日志"
echo "命令：journalctl -u nginx --no-pager -n 20 2>/dev/null | tail -n 10"
if systemctl list-unit-files | grep -q '^nginx\.service'; then
    journalctl -u nginx --no-pager -n 20 2>/dev/null | tail -n 10
else
    echo "（nginx 未安装，演示 ssh 日志：journalctl -u ssh --no-pager -n 10 | tail -n 10）"
    journalctl -u ssh --no-pager -n 10 2>/dev/null | tail -n 10 || journalctl -u sshd --no-pager -n 10 2>/dev/null | tail -n 10
fi

echo -e "\n[12] journalctl —— 实时跟踪日志（演示命令，不真实执行）"
cat <<'EOF'
journalctl -u nginx -f                          # 实时跟踪 nginx 日志（Ctrl+C 退出）
journalctl -u ecommerce-backend -f              # 实时跟踪电商后端日志
EOF

echo -e "\n[13] journalctl —— 按时间范围过滤"
cat <<'EOF'
journalctl --since today                        # 今天的日志
journalctl --since "2026-07-29 09:00:00" --until "2026-07-29 18:00:00"
journalctl -u nginx --since "1 hour ago"        # 最近 1 小时
journalctl -u nginx --since yesterday           # 昨天至今
EOF

echo -e "\n[14] journalctl —— 按级别过滤"
echo "命令：journalctl -p err --no-pager | tail -n 10"
journalctl -p err --no-pager 2>/dev/null | tail -n 10 || echo "（近期无 error 级别日志）"
echo ""
echo "级别说明：emerg(0) alert(1) crit(2) err(3) warning(4) notice(5) info(6) debug(7)"
echo "指定某级别会包含该级别及更严重的所有日志"

echo -e "\n[15] journalctl —— 按 PID 过滤"
SELF_PID=$$
echo "命令：journalctl _PID=$SELF_PID --no-pager 2>/dev/null | tail -n 5"
journalctl "_PID=$SELF_PID" --no-pager 2>/dev/null | tail -n 5 || echo "（当前进程无 journal 记录）"

echo -e "\n[16] journalctl —— 查看内核日志"
echo "命令：journalctl -k --no-pager | tail -n 5"
journalctl -k --no-pager 2>/dev/null | tail -n 5

echo -e "\n[17] journalctl —— 日志磁盘占用与清理"
echo "命令：journalctl --disk-usage"
journalctl --disk-usage 2>/dev/null
echo ""
echo "清理命令（需 sudo）："
cat <<'EOF'
sudo journalctl --vacuum-time=7d        # 只保留最近 7 天
sudo journalctl --vacuum-size=500M      # 只保留 500MB
sudo journalctl --vacuum-files=5        # 只保留 5 个日志文件
EOF

# ---------- 6. 自定义服务上线流程 ----------

echo -e "\n[18] 自定义服务上线完整流程"
cat <<'EOF'
1. 编写单元文件 ecommerce-backend.service（参考同目录 ecommerce-backend.service）
2. 拷贝到 systemd 目录
   sudo cp ecommerce-backend.service /etc/systemd/system/
3. 重新加载 systemd 配置（必须）
   sudo systemctl daemon-reload
4. 启用并立即启动
   sudo systemctl enable --now ecommerce-backend
5. 验证运行状态
   sudo systemctl status ecommerce-backend
   journalctl -u ecommerce-backend -f
6. 后续维护
   sudo systemctl restart ecommerce-backend     # 重启
   sudo systemctl reload ecommerce-backend      # 重载（需单元文件支持 ExecReload）
   sudo systemctl disable ecommerce-backend     # 取消开机自启
   sudo systemctl stop ecommerce-backend        # 停止
EOF

# ---------- 7. service 命令（旧版兼容） ----------

echo -e "\n[19] service 命令（SysVinit 兼容）"
cat <<'EOF'
service nginx start        # 等同 systemctl start nginx
service nginx status
service nginx restart
/etc/init.d/nginx restart  # 直接调用 SysVinit 脚本

说明：新脚本与服务管理一律使用 systemctl，service 仅在旧系统或兼容脚本中见到
EOF

echo -e "\n============================================================"
echo "  Day05 - 02 systemd 服务管理演示 完成"
echo "============================================================"
