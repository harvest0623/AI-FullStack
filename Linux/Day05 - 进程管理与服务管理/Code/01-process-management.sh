#!/bin/bash
# ============================================================
# 文件名：01-process-management.sh
# 用途：演示 Linux 进程管理核心命令，覆盖进程查看、信号控制、
#       后台任务、优先级调整与 /proc 文件系统
# 适用：Ubuntu 22.04 LTS
# 场景：电商项目服务器（192.168.1.100，部署在 /opt/ecommerce/）
# ============================================================

# 切换到脚本所在目录，方便相对路径演示
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "  Day05 - 01 进程管理演示"
echo "  服务器：192.168.1.100 / Ubuntu 22.04"
echo "============================================================"

# ---------- 1. 进程查看 ----------

echo -e "\n[1] ps aux —— 查看所有进程（BSD 风格）"
echo "命令：ps aux | head -n 10"
ps aux | head -n 10
echo "字段说明：USER=用户 PID=进程ID %CPU=CPU占用 %MEM=内存占用"
echo "         VSZ=虚拟内存RSS=物理内存 STAT=状态 START=启动时间 COMMAND=命令"

echo -e "\n[2] ps -ef —— 查看所有进程（System V 风格，含 PPID）"
echo "命令：ps -ef | head -n 10"
ps -ef | head -n 10
echo "字段说明：PPID=父进程ID C=CPU占用率 STIME=启动时间"

echo -e "\n[3] ps -ef | grep —— 过滤特定进程"
echo "命令：ps -ef | grep -E 'sshd|nginx' | grep -v grep"
ps -ef | grep -E 'sshd|nginx' | grep -v grep || echo "（当前未运行 sshd/nginx 进程）"

echo -e "\n[4] pstree -p —— 进程树形结构（-p 显示 PID）"
echo "命令：pstree -p | head -n 20"
pstree -p | head -n 20 || echo "（需安装 psmisc：sudo apt install -y psmisc）"

echo -e "\n[5] pgrep —— 按名称查 PID"
echo "命令：pgrep -l sshd"
pgrep -l sshd || echo "（无 sshd 进程）"
echo "命令：pgrep -l -u \$(whoami)        # 当前用户的进程（取前 5 个）"
pgrep -l -u "$(whoami)" | head -n 5

echo -e "\n[6] pidof —— 按名称直接取 PID"
echo "命令：pidof systemd"
pidof systemd || echo "（无 systemd 进程，可能不在 systemd 系统）"

# ---------- 2. top 字段说明（不进入交互界面，只展示快照） ----------

echo -e "\n[7] top —— 交互式进程监控（这里只取一次快照）"
echo "命令：top -b -n 1 | head -n 15    # -b 批处理模式，-n 1 只跑一次"
top -b -n 1 | head -n 15
echo "交互按键："
echo "  P=按CPU排序  M=按内存排序  k=杀进程  1=各CPU核心  q=退出"
echo "字段含义：VIRT=虚拟内存  RES=物理内存  SHR=共享内存  TIME+=累计CPU时间"

echo -e "\n[8] htop —— top 增强版（如已安装则启动，按 q 退出）"
if command -v htop >/dev/null 2>&1; then
    echo "htop 已安装，可在交互终端运行：htop"
else
    echo "htop 未安装，安装命令：sudo apt install -y htop"
fi

# ---------- 3. 信号机制演示 ----------

echo -e "\n[9] kill -l —— 列出所有信号"
echo "命令：kill -l"
kill -l
echo ""
echo "常用信号速查："
echo "  SIGHUP(1)  = 重载配置   SIGINT(2)  = Ctrl+C 中断"
echo "  SIGKILL(9) = 强制杀死   SIGTERM(15)= 优雅终止（默认）"
echo "  SIGSTOP(19)= 停止       SIGCONT(18)= 继续"

echo -e "\n[10] 启动一个后台 sleep 进程并演示信号发送"
# 启动一个 300 秒的 sleep 进程作为靶子
sleep 300 &
SLEEP_PID=$!
echo "已启动后台 sleep 300，PID=$SLEEP_PID"
echo "命令：ps -p $SLEEP_PID -o pid,ppid,stat,cmd"
ps -p "$SLEEP_PID" -o pid,ppid,stat,cmd

echo -e "\n[11] kill -TERM（优雅终止，默认信号）"
echo "命令：kill -15 $SLEEP_PID  &&  ps -p $SLEEP_PID"
kill -15 "$SLEEP_PID"
sleep 1
ps -p "$SLEEP_PID" -o pid,stat 2>/dev/null && echo "进程仍在" || echo "进程已退出（TERM 信号已生效）"

echo -e "\n[12] 演示 kill -9 强杀（启动另一个 sleep）"
sleep 300 &
SLEEP_PID2=$!
echo "已启动 sleep 300，PID=$SLEEP_PID2"
echo "命令：kill -9 $SLEEP_PID2"
kill -9 "$SLEEP_PID2"
sleep 1
ps -p "$SLEEP_PID2" -o pid,stat 2>/dev/null && echo "进程仍在" || echo "进程已被 SIGKILL 强杀"

echo -e "\n[13] killall / pkill —— 按名称/模式杀进程"
echo "命令：killall sleep        # 杀掉所有名为 sleep 的进程"
echo "命令：pkill -f 'sleep 300' # 按完整命令行模式匹配"
# 实际执行（清理可能残留的 sleep 进程）
pkill -9 -f "sleep 300" 2>/dev/null && echo "已清理残留 sleep 进程" || echo "无残留 sleep 进程"

# ---------- 4. 后台任务管理：jobs / bg / fg / nohup ----------

echo -e "\n[14] 后台任务管理演示"
echo "启动后台任务：sleep 100 &"
sleep 100 &
JOB1=$!
echo "jobs 输出："
jobs -l

echo -e "\n把任务调回前台：fg %1（演示用，不真正阻塞）"
echo "说明：在交互终端中执行 fg %1 会把后台任务调到前台"
echo "      Ctrl+Z 挂起后用 bg 让其在后台继续，用 fg 再次调回"
echo "      nohup command & 可让任务在 SSH 断开后继续运行"

# 清理演示任务
kill %1 2>/dev/null
wait 2>/dev/null

echo -e "\n[15] nohup —— 让进程脱离终端"
echo "命令：nohup sleep 60 > /tmp/nohup-demo.log 2>&1 &"
nohup sleep 60 > /tmp/nohup-demo.log 2>&1 &
NOHUP_PID=$!
echo "已用 nohup 启动 sleep 60，PID=$NOHUP_PID"
echo "命令：ps -p $NOHUP_PID -o pid,ppid,stat,cmd"
ps -p "$NOHUP_PID" -o pid,ppid,stat,cmd
echo "查看 nohup 输出：cat /tmp/nohup-demo.log"
cat /tmp/nohup-demo.log
echo "说明：nohup 会忽略 SIGHUP，即使关闭 SSH 会话进程也不会被杀"
echo "清理：kill $NOHUP_PID"
kill "$NOHUP_PID" 2>/dev/null

# ---------- 5. 进程优先级：nice / renice ----------

echo -e "\n[16] nice —— 以指定优先级启动进程"
echo "说明：nice 值范围 -20~19，值越低优先级越高；普通用户只能调高，root 可调低"
echo "命令：nice -n 10 sleep 60 &"
nice -n 10 sleep 60 &
NICE_PID=$!
echo "查看进程 nice 值：ps -p $NICE_PID -o pid,ni,cmd"
ps -p "$NICE_PID" -o pid,ni,cmd

echo -e "\n[17] renice —— 调整已运行进程的优先级（需 sudo）"
echo "命令：sudo renice -n 5 -p $NICE_PID"
sudo renice -n 5 -p "$NICE_PID" 2>/dev/null && echo "已调整 nice 值为 5" || echo "需要 sudo 权限才能调整"
ps -p "$NICE_PID" -o pid,ni,cmd
kill "$NICE_PID" 2>/dev/null

# ---------- 6. /proc 文件系统 ----------

echo -e "\n[18] /proc 文件系统 —— 查看进程运行时信息"
# 取当前 Shell 的 PID 作为示例
SELF_PID=$$
echo "当前 Shell PID=$SELF_PID"

echo -e "\n[18.1] /proc/\$PID/cmdline —— 启动命令"
echo "命令：cat /proc/$SELF_PID/cmdline | tr '\\0' ' '"
cat /proc/$SELF_PID/cmdline | tr '\0' ' '
echo ""

echo -e "\n[18.2] /proc/\$PID/status —— 进程状态（取关键字段）"
echo "命令：grep -E '^(Name|Pid|PPid|State|Uid|VmRSS|VmSize)' /proc/$SELF_PID/status"
grep -E '^(Name|Pid|PPid|State|Uid|VmRSS|VmSize)' /proc/$SELF_PID/status

echo -e "\n[18.3] /proc/\$PID/environ —— 环境变量（前 5 个）"
echo "命令：cat /proc/$SELF_PID/environ | tr '\\0' '\\n' | head -n 5"
cat /proc/$SELF_PID/environ | tr '\0' '\n' | head -n 5

echo -e "\n[18.4] /proc/\$PID/cwd —— 当前工作目录（符号链接）"
echo "命令：ls -l /proc/$SELF_PID/cwd"
ls -l /proc/$SELF_PID/cwd

echo -e "\n[18.5] /proc/\$PID/exe —— 可执行文件路径"
echo "命令：ls -l /proc/$SELF_PID/exe"
ls -l /proc/$SELF_PID/exe

echo -e "\n[18.6] /proc/\$PID/limits —— 资源限制（取文件描述符上限）"
echo "命令：grep 'open files' /proc/$SELF_PID/limits"
grep "open files" /proc/$SELF_PID/limits

echo -e "\n[18.7] /proc/\$PID/fd/ —— 打开的文件描述符"
echo "命令：ls -l /proc/$SELF_PID/fd/ | head -n 5"
ls -l /proc/$SELF_PID/fd/ | head -n 5

echo -e "\n[18.8] /proc/loadavg —— 系统负载（1/5/15 分钟平均负载）"
echo "命令：cat /proc/loadavg"
cat /proc/loadavg

echo -e "\n[18.9] /proc/meminfo —— 内存信息（取关键字段）"
echo "命令：grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal)' /proc/meminfo"
grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal)' /proc/meminfo

echo -e "\n============================================================"
echo "  Day05 - 01 进程管理演示 完成"
echo "============================================================"
