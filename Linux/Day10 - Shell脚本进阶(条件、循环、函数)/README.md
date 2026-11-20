# Day10 - Shell 脚本进阶（条件 / 循环 / 函数）

## 本章简介

Day09 学会的变量、字符串、数组、算术运算，让 Shell 脚本具备了“存数据、算数据”的能力，但还只是顺序执行的流水账。要让脚本具备真正的编程能力，需要三大结构：**条件判断**让脚本学会“做选择”，**循环**让脚本学会“重复劳动”，**函数**让脚本学会“封装复用”。三者结合，Shell 脚本才能胜任备份、巡检、批量部署等真实运维场景。

本章深入讲解 Shell 的条件测试（`test` / `[ ]` / `[[ ]]`）、分支语句（`if` / `case`）、循环结构（`for` / `while` / `until` / `select`）、函数定义与调用、正则匹配、信号处理 `trap`、脚本调试与严格模式 `set -euo pipefail`。最后通过三个实战脚本（数据库备份、服务健康检查、批量用户创建）把所学知识串起来，产出可直接用于生产的运维工具。本章所有脚本围绕电商项目 `/opt/ecommerce/` 的运维场景展开，可在 Ubuntu 22.04+ 直接执行。

## 学习目标

- 区分 `test` / `[ ]` / `[[ ]]` 三种条件测试的差异与适用场景
- 掌握文件测试、字符串测试、数值测试的全部常用操作符
- 熟练使用 `if-elif-else` 与 `case-esac` 分支结构
- 掌握 `for`（列表/C 风格）、`while`、`until`、`select` 四种循环
- 熟练使用 `break` / `continue` 与 `while read line` 遍历文件
- 掌握函数的定义、调用、参数传递、返回值与局部变量 `local`
- 理解函数返回字符串的 `echo + $()` 模式与递归调用
- 掌握 `[[ =~ ]]` 正则匹配与 `BASH_REMATCH` 捕获组
- 掌握 `trap` 信号处理与脚本退出清理
- 熟练使用 `bash -x/-n/-v` 调试与 `set -euo pipefail` 严格模式

## 理论知识讲解

### 1. 条件判断

#### 1.1 test 命令与 `[ ]`

`test` 是 POSIX 标准的测试命令，`[ ]` 是它的语法糖。注意 `[` 后面和 `]` 前面必须有空格，这是新手最容易踩的坑。

```bash
# 两种写法等价
test -f /etc/hostname
[ -f /etc/hostname ]

# 常见错误：[ -f /etc/hostname]   # ] 前没空格，报错
```

#### 1.2 `[[ ]]` 增强测试（bash 扩展）

`[[ ]]` 是 bash 的关键字，比 `[ ]` 更强大、更安全，**推荐优先使用**：

| 特性 | `[ ]` | `[[ ]]` |
| --- | --- | --- |
| 逻辑运算 | `-a` / `-o` | `&&` / `||` |
| 字符串比较 | `=` / `!=`，`<` `>` 需转义 | `==` / `!=`，`<` `>` 无需转义 |
| 模式匹配 | 不支持 | `==` 支持 glob 通配符 |
| 正则匹配 | 不支持 | `=~` 支持 ERE |
| 变量为空 | `[ $x = "" ]` 报错 | `[[ $x == "" ]]` 安全 |
| POSIX 兼容 | 是 | 否（仅 bash/ksh/zsh） |

```bash
# 模式匹配（glob）
[[ "nginx.conf" == *.conf ]] && echo "配置文件"

# 正则匹配
[[ "192.168.1.100" =~ ^[0-9.]+$ ]] && echo "纯数字和点"

# 逻辑组合
if [[ -f /etc/hostname && $USER == "root" ]]; then
    echo "root 用户且文件存在"
fi
```

#### 1.3 文件测试

| 操作符 | 含义 |
| --- | --- |
| `-e` | 文件/目录存在 |
| `-f` | 存在且为普通文件 |
| `-d` | 存在且为目录 |
| `-r` / `-w` / `-x` | 可读 / 可写 / 可执行 |
| `-s` | 文件存在且非空 |
| `-L` | 符号链接 |
| `-b` / `-c` | 块设备 / 字符设备 |
| `-p` | 命名管道 |
| `-S` | socket 文件 |
| `file1 -nt file2` | file1 比 file2 新（mtime） |
| `file1 -ot file2` | file1 比 file2 旧 |

#### 1.4 字符串测试

| 操作符 | 含义 |
| --- | --- |
| `-z str` | 字符串长度为 0（空） |
| `-n str` | 字符串长度非 0 |
| `str1 = str2` | 相等 |
| `str1 != str2` | 不等 |
| `str1 < str2` | 字典序小于（`[ ]` 中需 `\<` 转义） |
| `str1 > str2` | 字典序大于 |

```bash
# 安全判断字符串为空：用 [[ ]] 或加引号
[[ -z "$VAR" ]] && echo "VAR 为空"
[ -z "$VAR" ] && echo "VAR 为空"   # 也可，但变量必须加引号
```

#### 1.5 数值测试

| 操作符 | 含义 | 等价数学 |
| --- | --- | --- |
| `-eq` | 相等 | `==` |
| `-ne` | 不等 | `!=` |
| `-lt` | 小于 | `<` |
| `-le` | 小于等于 | `<=` |
| `-gt` | 大于 | `>` |
| `-ge` | 大于等于 | `>=` |

> 注意：`[ ]` 中比较数值用 `-eq` 等，比较字符串用 `=` / `!=`，**不要混用**。`[[ ]]` 中可以直接用 `>` `<` `>=` `<=` 比较数值（按算术比较）。

#### 1.6 逻辑运算

| 上下文 | 与 | 或 | 非 |
| --- | --- | --- | --- |
| `[ ]` 内 | `-a` | `-o` | `!` |
| `[[ ]]` 内 / 命令间 | `&&` | `\|\|` | `!` |

```bash
# [] 内用 -a/-o
[ -f file -a -r file ]      # 文件存在且可读

# [[ ]] 内用 &&/||
[[ -f file && -r file ]]

# 命令间用 &&/||
[ -f file ] && echo "存在" || echo "不存在"
```

#### 1.7 if 语句

```bash
if [[ condition1 ]]; then
    echo "条件1成立"
elif [[ condition2 ]]; then
    echo "条件2成立"
else
    echo "都不成立"
fi
```

#### 1.8 case 语句

`case` 适合多分支匹配，比层层 `if-elif` 清晰：

```bash
case "$1" in
    start)
        echo "启动服务"
        ;;
    stop)
        echo "停止服务"
        ;;
    restart|reload)
        echo "重启/重载服务"
        ;;
    *)
        echo "用法：$0 {start|stop|restart|reload}"
        exit 1
        ;;
esac
```

> `;;` 类似 C 的 `break`；`|` 表示或匹配；`*)` 是默认分支。

### 2. 循环

#### 2.1 for 循环（列表遍历）

```bash
# 1. 空格分隔的值列表
for svc in nginx mysql redis; do
    echo "服务：$svc"
done

# 2. 命令替换
for f in $(ls /opt/ecommerce/*.sh); do
    echo "脚本：$f"
done

# 3. 数组
services=("nginx" "mysql" "redis")
for svc in "${services[@]}"; do
    echo "服务：$svc"
done

# 4. seq 生成序列
for i in $(seq 1 5); do
    echo "第 $i 次"
done
```

#### 2.2 C 风格 for

```bash
for ((i=0; i<5; i++)); do
    echo "i = $i"
done

# 倒序
for ((i=10; i>=0; i-=2)); do
    echo "i = $i"
done
```

#### 2.3 while 循环

```bash
# 条件为真时循环
count=0
while [[ $count -lt 5 ]]; do
    echo "count = $count"
    ((count++))
done

# 死循环（用 break 退出）
while true; do
    echo "运行中..."
    sleep 1
    break
done
```

#### 2.4 until 循环

`until` 与 `while` 相反，条件为假时循环，直到条件为真才停止：

```bash
count=0
until [[ $count -ge 5 ]]; do
    echo "count = $count"
    ((count++))
done
```

#### 2.5 break 与 continue

```bash
# break 跳出整个循环
for i in {1..10}; do
    [[ $i -eq 5 ]] && break
    echo "i=$i"
done
# 输出 1 2 3 4

# continue 跳过本次，进入下一次
for i in {1..5}; do
    [[ $((i % 2)) -eq 0 ]] && continue
    echo "奇数：$i"
done
# 输出 1 3 5
```

#### 2.6 遍历文件：while read line

这是处理文件最经典的写法，能保留每行的空格：

```bash
while IFS= read -r line; do
    echo "处理：$line"
done < /etc/hosts
```

> `IFS=` 防止行首尾空格被吞，`-r` 防止反斜杠被解释。这是生产脚本的标准写法。

#### 2.7 select 菜单

`select` 自动生成菜单，配合 `case` 做交互选择：

```bash
PS3="请选择服务: "
select svc in nginx mysql redis 退出; do
    case $svc in
        nginx|mysql|redis)
            echo "你选择了 $svc"
            ;;
        退出)
            break
            ;;
        *)
            echo "无效选择"
            ;;
    esac
done
```

### 3. 函数

#### 3.1 定义与调用

```bash
# 写法一：function 关键字
function greet() {
    echo "Hello, $1"
}

# 写法二：省略 function
greet() {
    echo "Hello, $1"
}

# 调用（参数用空格分隔，不加括号）
greet "ecommerce"
greet "world"
```

#### 3.2 函数参数

函数内 `$1 $2 $@` 是**函数参数**，不是脚本参数：

```bash
show_info() {
    echo "函数名：$0"          # 仍是脚本名
    echo "第1个参数：$1"
    echo "参数个数：$#"
    echo "所有参数：$@"
}

show_info nginx mysql redis
# 输出：
# 函数名：./script.sh
# 第1个参数：nginx
# 参数个数：3
# 所有参数：nginx mysql redis
```

#### 3.3 返回值

Shell 函数的“返回值”有两种概念，别混淆：

| 方式 | 语法 | 取值范围 | 取值方式 | 用途 |
| --- | --- | --- | --- | --- |
| 退出码 | `return N` | 0-255 | `$?` | 表示成功/失败状态 |
| 输出字符串 | `echo "..."` | 任意字符串 | `$(func)` | 把函数当命令用，取其输出 |

```bash
# 退出码：表示成功失败
is_root() {
    if [[ $UID -eq 0 ]]; then
        return 0      # 成功
    else
        return 1      # 失败
    fi
}

if is_root; then
    echo "是 root"
fi

# 输出字符串：用 echo + $()
get_port() {
    echo "$1 端口是 $2"
}
result=$(get_port nginx 80)
echo "$result"        # nginx 端口是 80
```

> **重要**：`return` 只能返回 0-255 的整数，不能返回字符串。要返回字符串，用 `echo` 然后命令替换 `$()` 捕获。

#### 3.4 局部变量 local

函数内默认变量是全局的，会污染外部环境。用 `local` 限定为局部：

```bash
counter=0

inc() {
    counter=100       # 没有 local，会修改全局变量！
}

inc_safe() {
    local counter     # local，只在函数内有效
    counter=200
}

inc
echo $counter        # 100（被改了）
inc_safe
echo $counter        # 100（没被改）
```

> **强烈建议**：函数内的临时变量一律加 `local`，避免难以排查的副作用。

#### 3.5 递归

```bash
# 计算阶乘
factorial() {
    local n=$1
    if [[ $n -le 1 ]]; then
        echo 1
    else
        local prev
        prev=$(factorial $((n - 1)))
        echo $((n * prev))
    fi
}

echo "5! = $(factorial 5)"   # 120
```

### 4. 正则表达式与 `=~`

`[[ $str =~ regex ]]` 使用 ERE（扩展正则）匹配，匹配结果存入 `BASH_REMATCH` 数组：

```bash
ip="192.168.1.100"

# 判断是否是合法 IPv4 格式
if [[ $ip =~ ^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$ ]]; then
    echo "合法 IP"
    echo "完整匹配：${BASH_REMATCH[0]}"      # 192.168.1.100
    echo "第一段：${BASH_REMATCH[1]}"         # 192
    echo "第二段：${BASH_REMATCH[2]}"         # 168
fi

# 判断是否纯数字
[[ "12345" =~ ^[0-9]+$ ]] && echo "纯数字"

# 判断是否邮箱
[[ "user@example.com" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]] && echo "邮箱"
```

> 注意：`=~` 右侧的正则**不要加引号**，加了会被当字面字符串。变量需先存入变量再传给 `=~`。

### 5. 信号处理 trap

`trap` 让脚本在收到信号时执行指定命令，常用于退出清理：

```bash
# 捕获 Ctrl+C（SIGINT），执行 echo
trap 'echo "捕获 Ctrl+C，不退出"' SIGINT

# 捕获退出，执行清理函数
cleanup() {
    echo "清理临时文件..."
    rm -f /tmp/ecommerce_*.tmp
}
trap cleanup EXIT

# 忽略 Ctrl+C
trap '' SIGINT

# 恢复默认
trap - SIGINT
```

| 常用信号 | 编号 | 含义 |
| --- | --- | --- |
| `SIGINT` | 2 | Ctrl+C 中断 |
| `SIGTERM` | 15 | 终止信号（kill 默认） |
| `SIGKILL` | 9 | 强制杀死（**不能被 trap 捕获**） |
| `EXIT` | - | 脚本退出（无论正常/异常） |

> `trap '...' EXIT` 是最常用的模式：无论脚本怎么退出，都执行清理，避免遗留临时文件。

### 6. 脚本调试

#### 6.1 命令行调试参数

| 参数 | 作用 |
| --- | --- |
| `bash -x script.sh` | 执行并打印每条命令（最常用，前面带 `+`） |
| `bash -n script.sh` | 只做语法检查，不执行 |
| `bash -v script.sh` | 执行前打印原始行（未展开变量） |

#### 6.2 set 选项（脚本内开启）

```bash
#!/bin/bash
set -e             # 遇错即退出（任何命令返回非0）
set -u             # 使用未定义变量报错
set -x             # 调试模式，打印每条命令
set -o pipefail    # 管道中任一命令失败则整体失败
```

**生产推荐：严格模式**

```bash
#!/bin/bash
set -euo pipefail
```

- `set -e`：出错立即退出，避免错误被忽略后继续执行造成更大问题
- `set -u`：拼错变量名能立即发现
- `set -o pipefail`：`cmd1 | cmd2` 中 cmd1 失败不会被 cmd2 成功掩盖

> 注意：`set -e` 对 `if` / `while` / `||` / `&&` 条件中的命令不生效，这是设计如此，便于容错判断。

#### 6.3 调试技巧

```bash
# 局部开启调试
set -x
... 需要调试的代码 ...
set +x       # 关闭调试

# 输出变量值到 stderr（不影响 stdout）
echo "DEBUG: var=$var" >&2
```

### 7. 综合实战脚本思路

一个生产级运维脚本通常包含以下结构：

```bash
#!/bin/bash
set -euo pipefail

# 1. 常量定义
APP_NAME="ecommerce"
APP_DIR="/opt/ecommerce"
LOG_FILE="/var/log/ecommerce/backup.log"

# 2. 日志函数
log() {
    echo "[$(date '+%F %T')] $1" | tee -a "$LOG_FILE"
}

# 3. 清理函数 + trap
cleanup() {
    log "清理临时文件..."
    rm -f /tmp/${APP_NAME}_*.tmp
}
trap cleanup EXIT

# 4. 参数检查
if [[ $# -lt 1 ]]; then
    echo "用法：$0 {backup|check|deploy}"
    exit 1
fi

# 5. 主逻辑（case 分发）
case "$1" in
    backup)  do_backup ;;
    check)   do_check ;;
    deploy)  do_deploy ;;
    *)       echo "未知命令：$1"; exit 1 ;;
esac
```

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-conditionals.sh` | 条件判断练习：文件/字符串/数值测试、if/case、`[[]]` vs `[]` |
| `Code/02-loops.sh` | 循环练习：for/while/until/select、break/continue、`while read line` |
| `Code/03-functions.sh` | 函数练习：定义/调用/参数/返回值/局部变量/递归/`echo+$()` |
| `Code/04-practical-scripts.sh` | 实战脚本合集：数据库备份、服务健康检查、批量用户创建 |
| `Code/README.md` | 脚本执行说明与实战脚本使用方法 |

执行方式：

```bash
cd /opt/ecommerce/scripts/

# 基础练习
bash 01-conditionals.sh
bash 02-loops.sh
bash 03-functions.sh

# 实战脚本（部分操作需 root/sudo）
sudo bash 04-practical-scripts.sh backup_db
sudo bash 04-practical-scripts.sh health_check
sudo bash 04-practical-scripts.sh create_users /path/to/userlist.txt
```

## 关键知识点总结

### 条件测试速查表

| 测试对象 | `[ ]` | `[[ ]]` |
| --- | --- | --- |
| 文件存在 | `[ -f file ]` | `[[ -f file ]]` |
| 目录存在 | `[ -d dir ]` | `[[ -d dir ]]` |
| 字符串为空 | `[ -z "$s" ]` | `[[ -z $s ]]` |
| 字符串相等 | `[ "$s1" = "$s2" ]` | `[[ $s1 == $s2 ]]` |
| 数值相等 | `[ $n -eq 5 ]` | `[[ $n -eq 5 ]]` 或 `[[ $n == 5 ]]` |
| 数值大于 | `[ $n -gt 5 ]` | `[[ $n -gt 5 ]]` 或 `[[ $n > 5 ]]` |
| 逻辑与 | `[ a -a b ]` | `[[ a && b ]]` |
| 逻辑或 | `[ a -o b ]` | `[[ a \|\| b ]]` |
| 模式匹配 | ✗ | `[[ $s == *.conf ]]` |
| 正则匹配 | ✗ | `[[ $s =~ ^[0-9]+$ ]]` |

### 循环语法速查

| 循环 | 语法 | 适用场景 |
| --- | --- | --- |
| for in | `for x in list; do ...; done` | 遍历列表/数组/命令输出 |
| C 风格 for | `for ((i=0; i<n; i++)); do ...; done` | 已知次数的计数循环 |
| while | `while cond; do ...; done` | 条件为真时循环 |
| until | `until cond; do ...; done` | 条件为假时循环（直到为真） |
| while read | `while read line; do ...; done < file` | 逐行读文件 |
| select | `select x in list; do ...; done` | 交互菜单 |

### 函数语法速查

| 操作 | 语法 |
| --- | --- |
| 定义 | `name() { ...; }` 或 `function name { ...; }` |
| 调用 | `name arg1 arg2` |
| 参数 | 函数内 `$1 $2 $@ $#` |
| 返回退出码 | `return 0` / `return 1`（0-255） |
| 返回字符串 | `echo "..."` + `result=$(name)` |
| 局部变量 | `local var=value` |
| 递归 | 函数内调用自身 |

### set 选项速查表

| 选项 | 长选项 | 作用 |
| --- | --- | --- |
| `set -e` | `set -o errexit` | 遇错即退出 |
| `set -u` | `set -o nounset` | 未定义变量报错 |
| `set -x` | `set -o xtrace` | 打印执行的命令 |
| `set -o pipefail` | - | 管道任一失败则整体失败 |
| `set +e` | - | 关闭 -e |

## 实战练习

1. **服务状态判断脚本**
   - 编写 `svc_status.sh`，接收一个服务名参数（如 `nginx`）。
   - 用 `systemctl is-active` 判断状态，用 `case` 输出：运行中/已停止/未找到。
   - 用 `[[ -d /etc/$1 ]]` 判断配置目录是否存在，组合输出完整诊断信息。
   - 测试：`./svc_status.sh nginx`、`./svc_status.sh nonexistent`。

2. **批量日志统计**
   - 用 `while read line` 逐行读取 `/var/log/syslog`（或自造测试文件）。
   - 统计其中包含 `error` / `warning` / `info` 的行数（用 `case` 分发计数）。
   - 用 `printf` 输出对齐的统计表。
   - 扩展：把脚本封装成函数 `count_log_levels <logfile>`，可在同一脚本中调用多次。

3. **递归目录大小统计**
   - 编写函数 `dir_size()`，用 `du -sb` 获取目录大小（字节）。
   - 用 `for` 遍历 `/opt/ecommerce/` 下一级子目录，对每个调用 `dir_size`。
   - 把结果存入关联数组 `declare -A sizes`，按大小降序输出。
   - 加上 `trap cleanup EXIT`，清理脚本运行中产生的临时文件。
