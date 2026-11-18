# Day03 - 文本处理三剑客（grep/sed/awk）

## 本章简介

grep、sed、awk 是 Linux 文本处理的三把利器，是运维和数据分析的核心技能。grep 负责快速搜索匹配的行，sed 负责流式编辑与批量替换，awk 负责结构化文本的字段提取与统计分析。三者通过管道（pipe）组合，能在命令行完成许多本需要写脚本或导入 Excel 才能完成的任务——分析 Nginx 访问日志找出 Top 10 IP、批量修改配置文件中的端口号、统计服务器错误率、生成报表等。

本章还将讲解管道与重定向（`|`、`>`、`>>`、`2>`、`2>&1`、`<`、`<<EOF`），这是 Linux 命令组合的灵魂。掌握本章后，你将能像资深运维一样，用一行命令完成复杂的文本处理任务，为后续 Shell 脚本编写与日志分析打下坚实基础。

## 学习目标

- 理解管道 `|` 的本质：前一个命令的输出作为后一个命令的输入
- 掌握输出重定向（`>` 覆盖、`>>` 追加）、错误重定向（`2>`、`2>&1`、`&>`）、输入重定向（`<`）
- 理解 `/dev/null` 黑洞设备与 Here Document（`<<EOF`）
- 熟练使用 grep 搜索文本：基本用法、`-r` 递归、`-v` 反选、`-c` 计数、`-n` 行号、`-o` 仅匹配、`-i` 忽略大小写、`-w` 全词匹配、`-A/-B/-C` 上下文
- 使用 grep 扩展正则（`-E`）与 Perl 正则（`-P`），掌握正则元字符 `. ^ $ * + ? [] () | {} \d \w \s`
- 理解 sed 流编辑器的工作原理（模式空间），掌握地址定界、`s` 替换、`d` 删除、`a` 追加、`i` 插入、`p` 打印、`-i` 原地修改
- 理解 awk 的工作原理（逐行分字段），掌握 `$0`/`$1`/`$NF`、`NR`/`NF`/`FS`/`OFS`、`BEGIN`/`END` 块、模式匹配、数组统计、`printf` 格式化
- 用 awk 分析 Nginx 访问日志（统计 IP 访问量、状态码分布、流量统计）
- 掌握 xargs 参数传递、`column -t` 对齐、`paste`、`comm`、`diff` 等辅助工具

## 理论知识讲解

### 1. 管道与重定向

管道与重定向是 Linux 命令组合的核心机制，理解它们才能写出强大的命令行。

#### 1.1 标准输入输出（STDIO）

每个进程默认打开三个文件描述符：

| 文件描述符 | 名称 | 默认指向 | 说明 |
| --- | --- | --- | --- |
| 0 | stdin（标准输入） | 键盘 | 程序读取输入 |
| 1 | stdout（标准输出） | 屏幕 | 程序正常输出 |
| 2 | stderr（标准错误） | 屏幕 | 程序错误输出 |

#### 1.2 管道 `|`

管道把前一个命令的**标准输出**作为后一个命令的**标准输入**：

```
命令1 的 stdout → 管道 → 命令2 的 stdin
```

```bash
ls -l /etc | grep "conf"           # 列出 /etc 中含 conf 的文件
cat access.log | grep "404"        # 查找 404 请求
ps aux | grep nginx | grep -v grep # 查找 nginx 进程（排除 grep 自身）
ls -l | wc -l                      # 统计文件数
cat /etc/passwd | cut -d: -f1      # 提取所有用户名
```

> 管道只传递 stdout，不传递 stderr。要传递 stderr 需先 `2>&1` 合并。

#### 1.3 输出重定向

```bash
# 标准输出重定向
echo "hello" > file.txt            # 覆盖写入（文件不存在则创建）
echo "world" >> file.txt           # 追加写入
ls -l > listing.txt                # 把目录列表写入文件
date > /tmp/timestamp              # 记录时间戳

# 错误重定向
ls /nonexistent 2> error.log       # 错误信息写入文件
ls /etc /nonexistent 2> error.log  # 正常输出到屏幕，错误写入文件

# 合并标准输出与错误
ls /etc /nonexistent > all.log 2>&1    # 顺序：先重定向 stdout，再把 stderr 指向 stdout 的去向
ls /etc /nonexistent &> all.log        # Bash 4+ 简写（等同 > all.log 2>&1）
ls /etc /nonexistent 2>&1 | grep "ls"  # 合并后通过管道

# 丢弃输出
ls /nonexistent 2> /dev/null      # 错误丢弃（不显示）
command > /dev/null 2>&1          # 所有输出丢弃（常用于 cron）
command &> /dev/null              # 等同上一行
```

#### 1.4 输入重定向

```bash
# 从文件读取输入（替代键盘）
wc -l < /etc/passwd               # 统计行数（等同 cat /etc/passwd | wc -l）
sort < unsorted.txt               # 从文件读取并排序
mail -s "Test" user@example.com < body.txt   # 邮件正文从文件读取

# Here Document（多行输入）
cat <<'EOF' > /tmp/config.conf
server {
    listen 80;
    server_name example.com;
}
EOF
# 'EOF' 加引号表示内容中的变量不展开
# EOF 不加引号则变量会展开

# Here String（单行输入）
grep "error" <<< "this is an error message"
bc <<< "3 + 5"                    # 输出 8
```

#### 1.5 `/dev/null` 黑洞设备

`/dev/null` 是一个特殊设备文件，写入的内容全部丢弃，读取返回 EOF：

```bash
# 丢弃输出
command > /dev/null               # 丢弃 stdout
command 2> /dev/null              # 丢弃 stderr
command &> /dev/null              # 丢弃所有输出

# 清空文件
cat /dev/null > /var/log/app.log  # 清空文件内容（保留文件）
> /var/log/app.log                # 简写：清空文件

# 测试读取（返回 EOF）
cat /dev/null                     # 无输出，直接返回
```

#### 1.6 重定向速查表

| 语法 | 含义 |
| --- | --- |
| `command > file` | stdout 覆盖写入 file |
| `command >> file` | stdout 追加到 file |
| `command 2> file` | stderr 写入 file |
| `command 2>> file` | stderr 追加到 file |
| `command > file 2>&1` | stdout 和 stderr 都写入 file |
| `command &> file` | 同上（Bash 4+ 简写） |
| `command 2>&1` | stderr 重定向到 stdout（常用于管道） |
| `command > /dev/null` | 丢弃 stdout |
| `command 2> /dev/null` | 丢弃 stderr |
| `command &> /dev/null` | 丢弃所有输出 |
| `command < file` | 从 file 读取 stdin |
| `command <<EOF` | Here Document 多行输入 |
| `command <<< "string"` | Here String 单行输入 |
| `cmd1 | cmd2` | 管道：cmd1 的 stdout → cmd2 的 stdin |
| `cmd1 |& cmd2` | 管道：cmd1 的 stdout+stderr → cmd2（Bash 4+） |

### 2. grep 文本搜索

grep（Global Regular Expression Print）是 Linux 最常用的文本搜索工具，按行搜索匹配模式的文本。

#### 2.1 基本用法

```bash
grep "pattern" file               # 在 file 中搜索 pattern
grep "error" /var/log/syslog      # 在系统日志中搜索 error
echo "hello world" | grep "world" # 从管道搜索
grep "root" /etc/passwd           # 搜索含 root 的行
```

#### 2.2 常用选项

| 选项 | 含义 | 示例 |
| --- | --- | --- |
| `-r` | 递归搜索目录 | `grep -r "error" /var/log/` |
| `-R` | 递归（含软链接） | `grep -R "conf" /etc/` |
| `-v` | 反选（不匹配的行） | `grep -v "^#" file` |
| `-c` | 计数（仅输出匹配行数） | `grep -c "error" app.log` |
| `-n` | 显示行号 | `grep -n "error" app.log` |
| `-o` | 仅输出匹配部分 | `grep -o "[0-9]\+" file` |
| `-i` | 忽略大小写 | `grep -i "ERROR" app.log` |
| `-w` | 全词匹配 | `grep -w "cat" file`（不匹配 category） |
| `-x` | 整行匹配 | `grep -x "hello" file` |
| `-l` | 仅显示含匹配的文件名 | `grep -rl "error" /var/log/` |
| `-L` | 仅显示不含匹配的文件名 | `grep -rL "error" /var/log/` |
| `-A n` | 匹配行后 n 行 | `grep -A 3 "error" app.log` |
| `-B n` | 匹配行前 n 行 | `grep -B 2 "error" app.log` |
| `-C n` | 匹配行前后各 n 行 | `grep -C 3 "error" app.log` |
| `-E` | 扩展正则（等同 egrep） | `grep -E "a\|b" file` |
| `-P` | Perl 正则（支持 `\d` `\w`） | `grep -P "\d+" file` |
| `-F` | 固定字符串（不做正则） | `grep -F ".*" file` |
| `--color` | 高亮匹配 | `grep --color "error" app.log` |
| `--include` | 仅搜索指定类型文件 | `grep -r --include="*.log" "error" /var/log/` |
| `--exclude` | 排除指定类型文件 | `grep -r --exclude="*.gz" "error" /var/log/` |

#### 2.3 正则表达式基础

grep 支持基本正则（BRE）与扩展正则（ERE，用 `-E`）：

| 元字符 | 含义 | 示例 | 匹配 |
| --- | --- | --- | --- |
| `.` | 任意单个字符 | `a.c` | abc、a1c、aXc |
| `^` | 行首 | `^error` | 以 error 开头的行 |
| `$` | 行尾 | `\.log$` | 以 .log 结尾的行 |
| `*` | 前一个字符 0 次或多次 | `ab*c` | ac、abc、abbc |
| `+` | 前一个字符 1 次或多次（需 -E） | `ab+c` | abc、abbc（不匹配 ac） |
| `?` | 前一个字符 0 次或 1 次（需 -E） | `ab?c` | ac、abc |
| `[]` | 字符集 | `[aeiou]` | 任一元音 |
| `[^]` | 取反字符集 | `[^0-9]` | 非数字 |
| `[a-z]` | 字符范围 | `[A-Za-z]` | 任一字母 |
| `()` | 分组（需 -E） | `(ab)+` | ab、abab |
| `\|` | 或（需 -E） | `cat\|dog` | cat 或 dog |
| `{n}` | 恰好 n 次（需 -E） | `a{3}` | aaa |
| `{n,}` | 至少 n 次（需 -E） | `a{2,}` | aa、aaa、aaaa |
| `{n,m}` | n 到 m 次（需 -E） | `a{2,4}` | aa、aaa、aaaa |
| `\d` | 数字（需 -P） | `\d+` | 123 |
| `\w` | 单词字符（需 -P） | `\w+` | hello_123 |
| `\s` | 空白（需 -P） | `\s+` | 空格/Tab |
| `\b` | 单词边界 | `\bcat\b` | cat（不匹配 category） |

**示例**：

```bash
# 基本正则（BRE，默认）
grep "^error" app.log                    # 以 error 开头
grep "error$" app.log                    # 以 error 结尾
grep "[0-9]\+" app.log                   # 含数字（+ 需转义）
grep "ab*c" file                         # ac、abc、abbc

# 扩展正则（ERE，-E）
grep -E "error|warning" app.log          # error 或 warning
grep -E "[0-9]+" app.log                 # 含数字（+ 不需转义）
grep -E "ab+c" file                      # abc、abbc
grep -E "(error|warning)" app.log        # 分组

# Perl 正则（-P）
grep -P "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" access.log  # IP 地址
grep -P "\bword\b" file                  # 全词匹配

# 实用场景
grep -E "^[0-9]+" file                   # 以数字开头的行
grep -v "^#" /etc/ssh/sshd_config        # 排除注释行
grep -v "^$" file                        # 排除空行
grep -v "^#\|^$" /etc/ssh/sshd_config    # 排除注释和空行
grep -E "404|500" access.log             # 404 或 500 请求
```

### 3. sed 流编辑器

sed（Stream Editor）是流式文本编辑器，逐行读取输入、执行编辑命令、输出结果。sed 常用于批量替换、删除、插入文本。

#### 3.1 工作原理

```
输入流 → 逐行读取 → 模式空间 → 执行命令 → 输出 → 下一行
                       ↑
                    保持空间（hold space，高级用法）
```

- **模式空间（Pattern Space）**：当前处理的行，命令在此执行
- **保持空间（Hold Space）**：辅助存储，用于跨行操作（高级用法）

#### 3.2 地址定界

指定命令作用于哪些行：

```bash
sed '1d' file                # 删除第 1 行
sed '1,3d' file              # 删除第 1-3 行
sed '1,$d' file              # 删除第 1 到最后一行（全部）
sed '2,5p' file              # 打印第 2-5 行（需 -n）
sed '$d' file                # 删除最后一行
sed '/error/d' file          # 删除含 error 的行
sed '/^$/d' file             # 删除空行
sed '/start/,/end/d' file    # 删除 start 到 end 之间的行
sed '0~2d' file              # 删除偶数行（步长 2）
sed '1~2p' file              # 打印奇数行（步长 2）
```

#### 3.3 替换命令 `s`

`s/pattern/replacement/flags` 是 sed 最常用的命令：

```bash
sed 's/old/new/' file            # 每行第一个 old 替换为 new
sed 's/old/new/g' file           # 全局替换（每行所有 old）
sed 's/old/new/2' file           # 替换每行第 2 个 old
sed 's/old/new/gi' file          # 全局替换 + 忽略大小写
sed 's/old/new/p' file           # 替换并打印（需 -n）
sed 's/old/new/Ip' file          # 忽略大小写 + 打印
sed 's/old/&new/' file           # & 引用匹配内容（oldnew）
sed 's/\(old\)/\1new/' file      # \1 引用分组（需 BRE）
sed -E 's/(old)/\1new/' file     # ERE 分组引用
sed 's|/usr/local|/opt|g' file   # 用 | 作为分隔符（避免转义 /）
sed 's/^/    /' file             # 行首加 4 空格缩进
sed 's/$/;/' file                # 行尾加分号
sed 's/[ \t]*$//' file           # 删除行尾空格
```

#### 3.4 其他命令

| 命令 | 含义 | 示例 |
| --- | --- | --- |
| `s` | 替换 | `s/old/new/g` |
| `d` | 删除行 | `1,3d` |
| `p` | 打印行（需 -n） | `2,5p` |
| `a` | 行后追加 | `a\newline` |
| `i` | 行前插入 | `i\newline` |
| `c` | 整行替换 | `c\new content` |
| `y` | 字符转换 | `y/abc/ABC/` |
| `=` | 打印行号 | `1,3=` |
| `n` | 读取下一行 | |
| `q` | 退出 | `10q` |

#### 3.5 常用选项

| 选项 | 含义 |
| --- | --- |
| `-n` | 安静模式（不自动输出，配合 `p` 使用） |
| `-i` | 原地修改文件 |
| `-i.bak` | 原地修改并备份原文件为 .bak |
| `-e` | 多命令组合 |
| `-f` | 从文件读取命令 |
| `-r` 或 `-E` | 扩展正则 |
| `-s` | 多文件分别处理 |

**示例**：

```bash
# -n 安静模式 + p 打印
sed -n '2,5p' file               # 仅打印第 2-5 行（等同 head -n 5 | tail -n 4）
sed -n '/error/p' file           # 仅打印含 error 的行（等同 grep error）
sed -n '1p' file                 # 仅打印第 1 行

# -i 原地修改
sed -i 's/old/new/g' file        # 直接修改文件
sed -i.bak 's/old/new/g' file    # 修改并备份原文件为 file.bak
sed -i 's/port=8080/port=3000/' config.ini  # 修改配置

# -e 多命令
sed -e 's/foo/bar/g' -e 's/baz/qux/g' file
sed -e 's/a/A/g' -e 's/b/B/g' -e 's/c/C/g' file

# -r 扩展正则
sed -r 's/[0-9]+/N/g' file       # 数字替换为 N
sed -E 's/(error|warning)/LOG: \1/g' file

# 实用技巧
sed '/^$/d' file                 # 删除空行
sed '/^#/d' file                 # 删除注释行
sed '/^#\|^$/d' file             # 删除注释和空行
sed -i 's/\r$//' file            # 删除 Windows 换行符 \r
sed 's/^ *//' file               # 删除行首空格
sed 's/ *$//' file               # 删除行尾空格
sed 's/  */ /g' file             # 多个空格压缩为一个
```

### 4. awk 文本分析

awk 是强大的文本分析工具，尤其擅长处理结构化文本（如日志、CSV）。它是一种完整的编程语言，支持变量、条件、循环、数组、函数。

#### 4.1 工作原理

```
awk 'BEGIN { 初始化 }
     /pattern/ { 动作 }
     END { 收尾 }' file

执行流程：
1. 执行 BEGIN 块（读取文件前）
2. 逐行读取文件：
   a. 按分隔符分割字段到 $1 $2 $3 ...
   b. 检查是否匹配 pattern
   c. 匹配则执行动作
3. 读取完毕后执行 END 块
```

#### 4.2 字段与记录

| 变量 | 含义 |
| --- | --- |
| `$0` | 整行（当前记录） |
| `$1` `$2` ... | 第 1、2... 个字段 |
| `$NF` | 最后一个字段 |
| `$(NF-1)` | 倒数第二个字段 |
| `NF` | 字段数（Number of Fields） |
| `NR` | 当前行号（Number of Record，所有文件累计） |
| `FNR` | 当前文件中的行号 |
| `FILENAME` | 当前文件名 |
| `FS` | 字段分隔符（默认空格/Tab），可用 `-F` 指定 |
| `OFS` | 输出字段分隔符（默认空格） |
| `RS` | 记录分隔符（默认换行） |
| `ORS` | 输出记录分隔符（默认换行） |

```bash
# 基本用法
awk '{print}' file                  # 打印每行（等同 cat）
awk '{print $1}' file               # 打印第 1 列
awk '{print $1, $3}' file           # 打印第 1 和第 3 列
awk '{print $NF}' file              # 打印最后一列
awk '{print NR, $0}' file           # 带行号打印
awk '{print NF}' file               # 打印每行字段数

# 指定分隔符
awk -F: '{print $1}' /etc/passwd    # 以 : 分隔，打印用户名
awk -F: '{print $1, $3}' /etc/passwd  # 用户名 + UID
awk -F, '{print $1, $2}' data.csv   # CSV 文件
awk 'BEGIN{FS=":"} {print $1}' /etc/passwd  # 等同 -F:
awk 'BEGIN{FS=":"; OFS=" | "} {print $1, $3, $6}' /etc/passwd  # 自定义输出分隔符
```

#### 4.3 模式匹配

```bash
# 正则模式
awk '/error/' file                  # 打印含 error 的行（等同 grep）
awk '/error/{print $1, $2}' file    # 含 error 的行只打印前两列
awk '$1 ~ /^192/' file              # 第 1 列以 192 开头的行
awk '$1 !~ /^192/' file             # 第 1 列不以 192 开头的行

# 关系表达式
awk 'NR==1' file                    # 仅第 1 行
awk 'NR>1' file                     # 第 2 行起（跳过标题）
awk 'NR<=10' file                   # 前 10 行
awk '$3 > 100' file                 # 第 3 列大于 100 的行
awk '$NF == "error"' file           # 最后一列等于 error
awk 'NF > 5' file                   # 字段数大于 5 的行

# 范围模式
awk '/start/,/end/' file            # start 到 end 之间的行
```

#### 4.4 BEGIN / END 块

```bash
# BEGIN：读取文件前执行（常用于初始化变量、设置分隔符）
awk 'BEGIN{FS=":"; print "用户名 UID"} {print $1, $3}' /etc/passwd

# END：读取完毕后执行（常用于汇总统计）
awk '{sum += $1} END {print "总计:", sum}' numbers.txt
awk '{sum += $1; count++} END {print "平均:", sum/count}' numbers.txt
awk 'END {print "总行数:", NR}' file
```

#### 4.5 动作

```bash
# print 与 printf
awk '{print $1, $2}' file
awk '{printf "%-10s %5d\n", $1, $2}' file    # 格式化输出

# 条件
awk '{if ($3 > 100) print $1, "high"; else print $1, "low"}' file
awk '$3 > 100 {print $1, "high"} $3 <= 100 {print $1, "low"}' file

# 循环
awk '{for (i=1; i<=NF; i++) print $i}' file
awk '{for (i=NF; i>=1; i--) printf "%s ", $i; print ""}' file  # 字段倒序

# 赋值与计算
awk '{sum += $1} END {print sum}' file       # 求和
awk '{sum += $1; count++} END {print sum/count}' file  # 平均值
awk '$1 > max {max = $1} END {print max}' file  # 最大值
```

#### 4.6 数组（关联数组）

awk 的数组是关联数组（类似 Python dict），下标可以是字符串：

```bash
# 统计每个 IP 出现次数
awk '{count[$1]++} END {for (ip in count) print count[ip], ip}' access.log | sort -rn

# 统计每个状态码出现次数
awk '{count[$9]++} END {for (code in count) print code, count[code]}' access.log | sort

# 统计每个用户的进程数
ps aux | awk '{count[$1]++} END {for (u in count) print count[u], u}' | sort -rn

# 求总和与平均
awk '{sum[$1] += $2} END {for (k in sum) print k, sum[k]}' data.txt
```

#### 4.7 常用单行命令

```bash
# 打印第 N 列
awk '{print $2}' file

# 打印最后一列
awk '{print $NF}' file

# 打印行号
awk '{print NR": "$0}' file

# 过滤行
awk '$3 > 100' file              # 第 3 列大于 100
awk 'NR > 1' file                # 跳过第 1 行（标题）

# 求和
awk '{s+=$1} END {print s}' file

# 求平均
awk '{s+=$1; c++} END {print s/c}' file

# 去重计数
awk '{a[$1]++} END {for (k in a) print a[k], k}' file | sort -rn

# 统计行数
awk 'END {print NR}' file

# 替换
awk '{gsub(/old/, "new"); print}' file

# 打印指定列范围
awk '{for (i=2; i<=4; i++) printf "%s ", $i; print ""}' file

# 字段拼接
awk -F: '{print $1"@"$3}' /etc/passwd

# 条件求和
awk '$2 > 50 {s+=$2} END {print s}' file
```

### 5. 其他文本工具

#### 5.1 xargs - 参数传递

xargs 把标准输入转换为命令参数，常与 `find`、`grep` 配合：

```bash
# 基本用法
echo "a b c" | xargs mkdir        # 等同 mkdir a b c
find . -name "*.log" | xargs rm   # 删除所有 .log 文件
find . -name "*.log" | xargs grep "error"  # 在所有 .log 中搜索

# -n 指定每次参数数量
echo "1 2 3 4 5" | xargs -n 2 echo  # echo 1 2; echo 3 4; echo 5

# -I 指定占位符
find . -name "*.bak" | xargs -I {} mv {} /tmp/
find . -name "*.log" | xargs -I FILE wc -l FILE

# -0 处理含空格文件名（配合 find -print0）
find . -name "*.txt" -print0 | xargs -0 grep "hello"

# -P 并行执行
find . -name "*.jpg" | xargs -P 4 -I {} convert {} {}.thumb.jpg
```

#### 5.2 cut - 分列

```bash
cut -d: -f1 /etc/passwd           # 用户名列表
cut -d, -f1,3 data.csv            # CSV 第 1、3 列
cut -c 1-10 file                  # 每行前 10 字符
```

#### 5.3 sort 与 uniq

```bash
sort file | uniq -c | sort -rn    # 出现次数 Top
sort -t: -k3 -n /etc/passwd       # 按 UID 数值排序
sort -u file                      # 排序去重
```

#### 5.4 column - 对齐

```bash
column -t file                    # 列对齐显示
mount | column -t                 # mount 输出对齐
cat /etc/passwd | column -t -s:   # 以 : 分隔对齐
```

#### 5.5 paste / comm / diff

```bash
# paste - 横向合并文件
paste file1 file2                 # 横向拼接（Tab 分隔）
paste -d, file1 file2             # 用 , 分隔
paste -s file1                    # 所有行合并为一行

# comm - 比较两个已排序文件
comm file1 file2                  # 三列：仅 file1、仅 file2、两者都有
comm -12 file1 file2              # 仅显示两者都有的行
comm -23 file1 file2              # 仅显示 file1 独有的行

# diff - 比较文件差异
diff file1 file2                  # 显示差异
diff -u file1 file2               # 统一格式（patch 用）
diff -q dir1 dir2                 # 仅报告是否不同
```

## 关键知识点总结

### grep/sed/awk 命令速查表

| 工具 | 定位 | 典型场景 | 核心语法 |
| --- | --- | --- | --- |
| grep | 搜索匹配的行 | 找日志中的 error | `grep -rn "error" /var/log/` |
| sed | 流式编辑 | 批量替换配置 | `sed -i 's/old/new/g' file` |
| awk | 结构化分析 | 统计 IP 访问量 | `awk '{count[$1]++} END {for (k in count) print count[k], k}' log` |

### grep 常用选项速查

| 选项 | 含义 |
| --- | --- |
| `-r` | 递归搜索 |
| `-v` | 反选 |
| `-c` | 计数 |
| `-n` | 行号 |
| `-o` | 仅匹配部分 |
| `-i` | 忽略大小写 |
| `-w` | 全词匹配 |
| `-E` | 扩展正则 |
| `-P` | Perl 正则 |
| `-A n` | 后 n 行 |
| `-B n` | 前 n 行 |
| `-C n` | 前后各 n 行 |
| `--include` | 仅搜索指定类型 |

### sed 常用命令速查

| 命令 | 含义 | 示例 |
| --- | --- | --- |
| `s/old/new/g` | 全局替换 | `sed 's/port=8080/port=3000/g' config` |
| `d` | 删除行 | `sed '/^$/d' file`（删空行） |
| `p` | 打印（需 -n） | `sed -n '2,5p' file` |
| `a\` | 行后追加 | `sed '2a\new line' file` |
| `i\` | 行前插入 | `sed '2i\new line' file` |
| `c\` | 整行替换 | `sed '2c\replaced' file` |
| `=` | 打印行号 | `sed '=' file` |
| `-i` | 原地修改 | `sed -i 's/old/new/g' file` |
| `-i.bak` | 修改并备份 | `sed -i.bak 's/old/new/g' file` |
| `-n` | 安静模式 | `sed -n '/error/p' file` |
| `-e` | 多命令 | `sed -e 's/a/A/g' -e 's/b/B/g' file` |

### awk 内置变量速查

| 变量 | 含义 |
| --- | --- |
| `$0` | 整行 |
| `$1` `$2` ... `$NF` | 各字段 |
| `NF` | 字段数 |
| `NR` | 行号（全局） |
| `FNR` | 行号（当前文件） |
| `FS` | 字段分隔符 |
| `OFS` | 输出分隔符 |
| `FILENAME` | 文件名 |

### 正则表达式速查

| 元字符 | 含义 |
| --- | --- |
| `.` | 任意单字符 |
| `^` `$` | 行首/行尾 |
| `*` `+` `?` | 0+/1+/0或1 次 |
| `[]` `[^]` | 字符集/取反 |
| `()` | 分组 |
| `\|` | 或 |
| `{n,m}` | n 到 m 次 |
| `\d` `\w` `\s` | 数字/单词/空白（-P） |
| `\b` | 单词边界 |

### 管道重定向速查表

| 语法 | 含义 |
| --- | --- |
| `\|` | 管道 |
| `>` `>>` | 覆盖/追加 stdout |
| `2>` `2>>` | 覆盖/追加 stderr |
| `2>&1` `&>` | 合并 stdout 与 stderr |
| `<` | 输入重定向 |
| `<<EOF` | Here Document |
| `<<<` | Here String |
| `/dev/null` | 黑洞 |

## 代码文件说明

| 文件 | 用途 | 执行方式 |
| --- | --- | --- |
| `Code/01-grep-demo.sh` | grep 演示：搜索日志、`-r` 递归、`-v`/`-c`/`-n`/`-o`/`-A`/`-B`/`-C`、正则匹配 | `bash 01-grep-demo.sh` |
| `Code/02-sed-demo.sh` | sed 演示：替换 `s`、删除 `d`、追加 `a`、插入 `i`、打印 `p`、`-i` 原地修改 | `bash 02-sed-demo.sh` |
| `Code/03-awk-demo.sh` | awk 演示：字段提取、`BEGIN`/`END`、条件过滤、求和/平均、数组统计、分析 Nginx 日志 | `bash 03-awk-demo.sh` |
| `Code/04-pipeline-redirect.sh` | 管道与重定向演示：`\|` 管道链、`>`/`>>`/`2>`/`2>&1`、`/dev/null`、Here Document、xargs | `bash 04-pipeline-redirect.sh` |

> 所有脚本会先创建模拟的日志文件和配置文件作为处理素材，可独立执行。

## 实战练习

### 练习一：用 grep 分析 Nginx 日志

先执行 `Code/01-grep-demo.sh` 生成模拟日志，然后完成：

1. 统计 `access.log` 中 404 请求的数量：`grep -c " 404 " access.log`
2. 找出所有 500 错误的请求行：`grep " 500 " access.log`
3. 搜索所有来自 `192.168.1.10` 的请求：`grep "^192.168.1.10" access.log`
4. 排除所有静态资源请求（.js/.css/.png）：`grep -vE "\.(js|css|png)" access.log`
5. 找出所有 POST 请求：`grep '"POST' access.log`
6. 递归搜索 `/opt/ecommerce/` 下所有含 `password` 的文件：`grep -rn "password" /opt/ecommerce/`

### 练习二：用 sed 批量修改配置文件

1. 创建一个 `nginx.conf`，把 `listen 80` 改为 `listen 8080`：`sed -i 's/listen 80;/listen 8080;/' nginx.conf`
2. 删除所有注释行（以 # 开头）：`sed -i '/^#/d' nginx.conf`
3. 删除所有空行：`sed -i '/^$/d' nginx.conf`
4. 在 `server {` 行后插入一行 `root /opt/ecommerce/frontend;`：`sed -i '/server {/a\    root /opt/ecommerce/frontend;' nginx.conf`
5. 把所有 `example.com` 替换为 `myshop.com`：`sed -i 's/example.com/myshop.com/g' nginx.conf`
6. 删除 Windows 换行符：`sed -i 's/\r$//' nginx.conf`
7. 修改前先备份：`sed -i.bak 's/old/new/g' config`

### 练习三：用 awk 分析访问日志

1. 统计每个 IP 的访问次数，按次数降序：
   ```bash
   awk '{count[$1]++} END {for (ip in count) print count[ip], ip}' access.log | sort -rn | head -n 10
   ```
2. 统计各 HTTP 状态码出现次数：
   ```bash
   awk '{count[$9]++} END {for (code in count) print code, count[code]}' access.log | sort
   ```
3. 计算总流量（第 10 列字节数之和）：
   ```bash
   awk '{sum+=$10} END {print sum/1024/1024 " MB"}' access.log
   ```
4. 找出访问量最大的 5 个 IP：
   ```bash
   awk '{count[$1]++} END {for (ip in count) print count[ip], ip}' access.log | sort -rn | head -n 5
   ```
5. 统计每个请求方法的次数（GET/POST/PUT/DELETE）：
   ```bash
   awk -F'"' '{print $2}' access.log | awk '{print $1}' | sort | uniq -c
   ```
6. 找出响应时间最长的 10 个请求（假设最后一列是响应时间）：
   ```bash
   awk '{print $NF, $0}' access.log | sort -rn | head -n 10
   ```
