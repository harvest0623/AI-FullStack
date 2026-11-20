# Day09 - Shell 脚本基础

## 本章简介

如果说前八天的命令行学习是“用一把把单兵武器逐个击破问题”，那么 Shell 脚本就是把这些武器组合成“自动化作战系统”的关键能力。一个运维工程师每天可能要重复执行几十次相同的命令序列：检查服务状态、备份日志、清理临时文件、重启进程……把这些步骤写进一个 `.sh` 文件，让机器自己按需执行，就是 Shell 脚本的价值所在。它是 Linux 运维的标配技能，也是后续定时任务、自动化部署、CI/CD 流水线的底层载体。

本章从零开始讲解 Shell 脚本的基础语法：脚本的 shebang 与三种执行方式、变量的各种类型与作用域、字符串与数组的操作技巧、命令替换、算术运算、输入输出格式化。掌握这些原子能力后，Day10 的条件判断、循环和函数才能真正组合出复杂的自动化逻辑。本章所有脚本围绕电商项目 `/opt/ecommerce/` 的运维场景展开，可在 Ubuntu 22.04+ 直接执行。

## 学习目标

- 理解 Shell 脚本的本质：命令的集合、可重复执行、实现自动化
- 掌握 shebang 的三种写法及其可移植性差异
- 区分 `bash` / `chmod +x` / `source` 三种脚本执行方式及子 Shell 与当前 Shell 的差别
- 熟练使用自定义变量、环境变量、位置参数变量与特殊变量
- 掌握单引号、双引号、无引号在变量解析上的区别
- 掌握字符串的长度、截取、替换、删除、大小写、默认值操作
- 掌握普通数组与关联数组（`declare -A`）的定义、访问、遍历、切片
- 熟练使用命令替换 `$()` 与算术运算 `$(())`
- 掌握 `read` 读取用户输入与 `echo` / `printf` 格式化输出

## 理论知识讲解

### 1. Shell 脚本基础

#### 1.1 什么是 Shell 脚本

Shell 既是命令解释器（把用户输入的命令翻译给内核执行），也是一种脚本语言。Shell 脚本就是把一组命令按顺序写进一个文本文件，由 Shell 逐行解释执行。它的核心价值有三点：

- **命令的集合**：把多条相关命令组织成一个整体，避免反复手动输入。
- **可重复执行**：同一套逻辑可对多台机器、多个对象反复执行，结果一致。
- **自动化**：配合定时任务（cron）可实现无人值守的自动化运维。

电商运维场景中常见的脚本用途：每天凌晨备份 MySQL、每小时检查 Nginx 是否存活、新机器初始化时批量创建目录与用户、部署时依次拉代码 → 安装依赖 → 重启服务。

#### 1.2 Shebang：脚本的第一行

脚本第一行以 `#!` 开头，告诉内核用哪个解释器执行本脚本，称为 shebang（也叫 hashbang）。

| 写法 | 含义 | 适用场景 |
| --- | --- | --- |
| `#!/bin/bash` | 明确用系统的 bash | Ubuntu/CentOS 通用，最常见 |
| `#!/bin/sh` | 用系统默认的 POSIX Shell（Ubuntu 下指向 dash） | 追求 POSIX 兼容、极简脚本 |
| `#!/usr/bin/env bash` | 在 PATH 中查找 bash | 跨发行版/跨平台可移植（macOS、BSD） |

> 注意：Ubuntu 的 `/bin/sh` 实际是 `dash`，语法比 bash 严格（不支持 `[[ ]]`、数组等）。若脚本用了 bash 特性，shebang 必须写 `#!/bin/bash`，否则用 `sh script.sh` 执行会报错。

#### 1.3 脚本的三种执行方式

| 方式 | 命令 | 是否需要可执行权限 | 执行的 Shell | 对当前环境的影响 |
| --- | --- | --- | --- | --- |
| 解释器执行 | `bash script.sh` | 否 | 新开子 Shell | 不影响当前 Shell |
| 可执行文件执行 | `chmod +x script.sh && ./script.sh` | 是 | 新开子 Shell | 不影响当前 Shell |
| source 执行 | `source script.sh` 或 `. script.sh` | 否 | 当前 Shell | 影响当前环境（变量、函数、cd 等） |

#### 1.4 bash vs source 的区别

这是初学者最容易混淆的点：

- **bash script.sh**： fork 一个子 Shell 进程执行脚本，脚本里定义的变量、`cd` 切换的目录、`export` 的环境变量，在脚本结束后**全部消失**，不影响你当前终端。
- **source script.sh**：在**当前 Shell** 中逐行执行脚本，脚本里定义的变量、函数、`cd` 都会**保留**到当前终端。这就是为什么 `~/.bashrc` 修改后要用 `source ~/.bashrc` 才能立即生效。

```bash
# 演示：在 demo.sh 中写 export FOO=bar
bash demo.sh
echo $FOO        # 空，子 Shell 的变量带不出来

source demo.sh
echo $FOO        # bar，当前 Shell 拿到了变量
```

#### 1.5 注释

Shell 只支持单行注释，以 `#` 开头，从 `#` 到行末都是注释。

```bash
# 这是单行注释
name="ecommerce"   # 行尾注释也可以
```

> Shell 没有原生多行注释。若需大段注释，可临时用 `:<<'EOF' ... EOF` 把内容包起来当无用字符串丢弃，但不推荐在正式脚本中滥用。

### 2. 变量

#### 2.1 自定义变量

```bash
name="ecommerce"     # 等号两边不能有空格！
version=2.4
echo $name           # 输出：ecommerce
echo ${name}v${version}  # 输出：ecommercev2.4，花括号界定变量边界
```

> **新手最大的坑**：`name = "value"`（带空格）会被 Shell 解释成执行命令 `name` 并传两个参数 `=` 和 `value`，报错 `command not found`。等号两边必须紧贴。

#### 2.2 变量命名规则

- 只能包含字母、数字、下划线
- 不能以数字开头
- 区分大小写（`Name` 与 `name` 是两个变量）
- 见名知义，建议全大写表示环境变量或常量

#### 2.3 单引号 vs 双引号 vs 无引号

| 引号 | 变量解析 | 命令替换 | 转义字符 | 适用场景 |
| --- | --- | --- | --- | --- |
| 单引号 `'...'` | 不解析 | 不解析 | 不生效（原样输出） | 输出含 `$` 的字面字符串 |
| 双引号 `"..."` | 解析 | 解析 | 生效（`\n` 需配合 `echo -e`） | 大多数场景，推荐 |
| 无引号 | 解析 | 解析 | 不能含空格、`*`、`?` 等 | 简单无空格值 |

```bash
project="ecommerce"
echo 'project is $project'      # project is $project（原样）
echo "project is $project"      # project is ecommerce（解析）
echo "today is $(date +%F)"     # today is 2026-07-29（命令替换）
echo 'today is $(date +%F)'     # today is $(date +%F)（不解析）
```

> **建议**：只要值里有可能出现空格或变量，就用双引号包起来，能避免 90% 的字符串分词坑。

#### 2.4 环境变量

环境变量可被子进程继承，普通变量只在当前 Shell 有效。

```bash
export DB_HOST="192.168.1.100"   # 导出为环境变量
env | grep DB_HOST               # 查看
printenv DB_HOST                 # 直接查单个

# 常见内置环境变量
echo $PATH     # 命令搜索路径
echo $HOME     # 当前用户家目录
echo $USER     # 当前用户名
echo $SHELL    # 当前 Shell 路径
echo $PWD      # 当前工作目录
```

> 持久化环境变量：写入 `~/.bashrc`（当前用户）或 `/etc/profile.d/*.sh`（全局），然后 `source` 生效。

#### 2.5 只读变量

```bash
PI=3.14
readonly PI          # 标记为只读
declare -r E=2.71    # 等价写法
PI=3.15              # 报错：bash: PI: readonly variable
```

> 只读变量不能修改也不能 unset，常用于脚本中的常量定义，防止误改。

#### 2.6 变量删除

```bash
temp_var="hello"
unset temp_var
echo $temp_var       # 空
```

#### 2.7 位置参数变量与特殊变量

| 变量 | 含义 |
| --- | --- |
| `$0` | 脚本名（含路径，取决于调用方式） |
| `$1` ~ `$9` | 第 1~9 个参数 |
| `${10}` | 第 10 个及以后的参数（必须用花括号） |
| `$#` | 参数总个数 |
| `$@` | 所有参数，每个独立（推荐用 `"$@"`） |
| `$*` | 所有参数，合为一个字符串（用 `"$*"` 时以 IFS 第一个字符连接） |
| `$?` | 上一条命令的退出码（0 成功，非 0 失败） |
| `$$` | 当前 Shell 的 PID |
| `$!` | 最近一个后台进程的 PID |
| `$_` | 上一条命令的最后一个参数 |

**`$@` vs `$*` 在循环中的区别**（经典面试题）：

```bash
# 假设脚本以 ./test.sh "a b" c d 调用（注意第一个参数含空格）
for arg in "$@"; do echo "[$arg]"; done
# 输出：[a b] [c] [d]   ← 每个参数独立，含空格也保留

for arg in "$*"; do echo "[$arg]"; done
# 输出：[a b c d]        ← 全部合成一个字符串
```

> **结论**：遍历参数几乎永远用 `"$@"`（带引号），`$*` 仅在需要把所有参数拼成一个字符串时使用。

### 3. 字符串操作

Bash 内置了强大的字符串操作语法，无需调用 `awk` / `sed`。

```bash
str="Hello, ecommerce World, hello Shell"
```

| 操作 | 语法 | 示例结果 |
| --- | --- | --- |
| 长度 | `${#str}` | `36` |
| 截取（从 0 取 5） | `${str:0:5}` | `Hello` |
| 截取（从 7 到末尾） | `${str:7}` | `ecommerce World, hello Shell` |
| 替换第一个 | `${str/hello/Hi}` | `Hello, ecommerce World, Hi Shell`（小写 h） |
| 替换全部 | `${str//hello/Hi}` | `Hello, ecommerce World, Hi Shell` |
| 从头部删最短匹配 | `${str#H*o}` | `, ecommerce World, hello Shell` |
| 从头部删最长匹配 | `${str##H*o}` | `, hello Shell` |
| 从尾部删最短匹配 | `${str%Shell}` | `Hello, ecommerce World, hello ` |
| 从尾部删最长匹配 | `${str%%l*}` | `He` |
| 全大写 | `${str^^}` | `HELLO, ECOMMERCE WORLD, HELLO SHELL` |
| 全小写 | `${str,,}` | `hello, ecommerce world, hello shell` |
| 首字母大写 | `${str^}` | `Hello, ecommerce World, hello Shell` |

**默认值操作**（在配置脚本里极其常用）：

```bash
# 若 LOG_DIR 为空或未设置，则使用 /var/log，但不赋值
LOG_DIR=""
echo "${LOG_DIR:-/var/log}"     # /var/log
echo "$LOG_DIR"                 # 仍是空

# 若 LOG_DIR 为空，则赋值 /var/log 并使用
echo "${LOG_DIR:=/var/log}"     # /var/log
echo "$LOG_DIR"                 # /var/log（已赋值）
```

### 4. 数组

#### 4.1 普通数组（索引数组）

```bash
# 定义
services=("nginx" "mysql" "redis")
services[3]="pm2"           # 追加

# 访问
echo ${services[0]}         # nginx
echo ${services[@]}         # nginx mysql redis pm2（所有元素）
echo ${#services[@]}        # 4（长度）
echo ${services[@]:1:2}     # mysql redis（切片，从索引1取2个）

# 遍历
for svc in "${services[@]}"; do
    echo "service: $svc"
done
```

#### 4.2 关联数组（键值对，类似字典）

关联数组必须用 `declare -A` 声明，否则会被当作索引数组。

```bash
declare -A ports
ports["nginx"]=80
ports["mysql"]=3306
ports["redis"]=6379

echo ${ports["nginx"]}                  # 80

# 遍历所有 key
for key in "${!ports[@]}"; do
    echo "$key -> ${ports[$key]}"
done

# 遍历所有 value
for val in "${ports[@]}"; do
    echo "port: $val"
done

echo ${#ports[@]}    # 3
```

> `${!arr[@]}` 取所有 key，`${arr[@]}` 取所有 value，初学者常混淆。

### 5. 命令替换

把命令的输出赋值给变量，有两种写法：

```bash
# 反引号（旧，不推荐，不可嵌套，难读）
today=`date +%F`

# $()（推荐，可嵌套，可读性好）
today=$(date +%F)
file_count=$(ls /opt/ecommerce | wc -l)
nested=$(echo "today is $(date +%F)")
```

### 6. 算术运算

| 语法 | 示例 | 说明 |
| --- | --- | --- |
| `$((expr))` | `a=$((1+2))` | 推荐，支持 `+ - * / % **` |
| `$[expr]` | `a=$[1+2]` | 旧语法，已不推荐 |
| `expr` | `expr 1 + 2` | 需空格，乘号需转义 `\*` |
| `let` | `let a=1+2` | 直接修改变量 |

```bash
a=10
b=3
echo $((a + b))     # 13
echo $((a - b))     # 7
echo $((a * b))     # 30
echo $((a / b))     # 3（整数除法，截断小数）
echo $((a % b))     # 1（取余）
echo $((a ** 2))    # 100（幂）

# 自增自减
count=0
((count++))         # 等同 count=$((count+1))
echo $count         # 1
((count--))
echo $count         # 0
```

> 浮点运算 Bash 原生不支持，需借助 `bc`：`echo "scale=2; 10/3" | bc` 输出 `3.33`。

### 7. read 读取输入

```bash
read name                              # 读一行到 name
read -p "请输入项目名: " project         # 带提示
read -s -p "请输入密码: " password      # 静默输入（不回显，适合密码）
read -t 5 -p "5秒内回答: " answer       # 5秒超时，超时返回非0

# 读多个字段
echo -e "nginx 80\nmysql 3306" | while read svc port; do
    echo "$svc 监听 $port"
done
```

### 8. echo 与 printf

#### 8.1 echo

```bash
echo "hello"               # 默认换行
echo -n "hello"            # 不换行
echo -e "line1\nline2"     # 解析转义：\n \t \\
echo -e "tab\tseparated"   # 制表符
```

#### 8.2 printf（更强大，建议格式化输出用 printf）

```bash
# 格式符：%s 字符串  %d 整数  %f 浮点  %x 十六进制
# 宽度对齐：%-10s 左对齐宽度10  %10s 右对齐  %.2f 保留2位小数
printf "%-10s %s\n" "Name" "Port"
printf "%-10s %d\n" "nginx" 80
printf "%-10s %d\n" "mysql" 3306
printf "%-10s %d\n" "redis" 6379

# 浮点
printf "PI = %.2f\n" 3.14159   # PI = 3.14
```

> `printf` 不像 `echo` 默认换行，需手动加 `\n`。生产脚本里输出表格/对齐内容建议用 `printf`。

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01-hello-shell.sh` | 第一个 Shell 脚本：echo 输出、注释、变量使用、三种执行方式对比 |
| `Code/02-variables.sh` | 变量练习：自定义/环境变量、位置参数、单引号 vs 双引号、readonly、unset、特殊变量 `$? $$ $!` |
| `Code/03-string-array.sh` | 字符串与数组：长度/截取/替换/删除/大小写、普通数组、关联数组 |
| `Code/04-arithmetic-read.sh` | 算术运算与输入：`$(())`/`$[]`/`expr`/`let`、自增自减、`read -p/-s/-t`、`printf` |
| `Code/README.md` | 脚本执行说明与环境准备 |

执行方式：

```bash
cd /opt/ecommerce/scripts/   # 或代码所在目录

# 方式一：bash 执行（无需权限，推荐调试时用）
bash 01-hello-shell.sh

# 方式二：赋予执行权限后直接运行
chmod +x 01-hello-shell.sh
./01-hello-shell.sh

# 方式三：source 执行（影响当前 Shell，仅用于加载变量/函数）
source 02-variables.sh

# 带参数执行
bash 02-variables.sh nginx mysql redis
```

## 关键知识点总结

### 变量类型速查表

| 类型 | 定义 | 作用域 | 示例 |
| --- | --- | --- | --- |
| 自定义变量 | `name="value"` | 当前 Shell | `app="ecommerce"` |
| 环境变量 | `export VAR=value` | 当前 Shell 及子进程 | `export PATH=$PATH:/opt/bin` |
| 只读变量 | `readonly name` / `declare -r` | 当前 Shell（不可改） | `readonly PI=3.14` |
| 局部变量 | `local var`（函数内） | 当前函数 | `local count=0` |
| 位置参数 | `$1 $2 ...` | 脚本/函数内 | `bash a.sh arg1` |
| 特殊变量 | `$? $$ $! $@` | 全局 | `$?` 退出码 |

### 字符串操作速查表

| 操作 | 语法 |
| --- | --- |
| 长度 | `${#str}` |
| 截取 | `${str:start}` / `${str:start:len}` |
| 替换首个 | `${str/old/new}` |
| 替换全部 | `${str//old/new}` |
| 头部删最短 | `${str#pattern}` |
| 头部删最长 | `${str##pattern}` |
| 尾部删最短 | `${str%pattern}` |
| 尾部删最长 | `${str%%pattern}` |
| 全大写 | `${str^^}` |
| 全小写 | `${str,,}` |
| 默认值（不赋值） | `${str:-default}` |
| 默认值（赋值） | `${str:=default}` |

### 位置参数速查表

| 变量 | 含义 |
| --- | --- |
| `$0` | 脚本名 |
| `$1`~`$9` | 第1~9个参数 |
| `${10}` | 第10个及以后 |
| `$#` | 参数个数 |
| `"$@"` | 所有参数（独立，推荐） |
| `"$*"` | 所有参数（合并） |
| `$?` | 退出码 |
| `$$` | 当前 PID |
| `$!` | 后台进程 PID |
| `$_` | 上条命令最后参数 |

### 算术运算对比表

| 语法 | 推荐度 | 是否需空格 | 是否支持嵌套 | 示例 |
| --- | --- | --- | --- | --- |
| `$((expr))` | ★★★★★ | 否 | 是 | `a=$((1+2))` |
| `$[expr]` | ★★ | 否 | 是 | `a=$[1+2]` |
| `let` | ★★★ | 否 | 是 | `let a=1+2` |
| `expr` | ★★ | **是** | 难 | `expr 1 + 2` |

## 实战练习

1. **脚本执行方式对比**
   - 编写 `test_exec.sh`，内容为 `export MY_VAR="from_script"`。
   - 分别用 `bash test_exec.sh`、`./test_exec.sh`、`source test_exec.sh` 三种方式执行。
   - 每次执行后立即 `echo $MY_VAR`，观察哪种方式能让变量保留在当前 Shell，并解释原因。

2. **位置参数与字符串处理**
   - 编写脚本 `svc_info.sh`，接收脚本名、服务名、端口号三个参数（`$0 $1 $2`）。
   - 用 `${0##*/}` 取出脚本短名，用 `${#1}` 取出服务名长度，用 `${2:-80}` 设置端口默认值。
   - 用 `printf` 以对齐表格输出：`脚本名 | 服务名 | 服务名长度 | 端口`。
   - 测试：`./svc_info.sh nginx 3306` 与 `./svc_info.sh redis`（不传端口）两种调用。

3. **关联数组端口表**
   - 用 `declare -A` 定义电商项目的服务端口表：nginx→80、mysql→3306、redis→6379、node→3000。
   - 用 `for key in "${!ports[@]}"` 遍历并输出 `服务:端口` 列表。
   - 用 `read -p` 让用户输入服务名，从数组中查出端口并输出；若不存在则提示 `未找到服务`。
