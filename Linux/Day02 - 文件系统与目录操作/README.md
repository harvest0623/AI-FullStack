# Day02 - 文件系统与目录操作

## 本章简介

理解 Linux 文件系统层次结构（FHS），是高效操作服务器的基础。与 Windows 用盘符（C: D:）分隔不同，Linux 采用单一的树形目录结构，所有文件和设备都挂载在根目录 `/` 之下。这种设计简洁而强大——一块磁盘、一个 U 盘、一个网络文件系统，挂载后都表现为普通目录，可以用统一的命令操作。

本章深入讲解 FHS 标准下各核心目录的用途，理清绝对路径与相对路径的区别，掌握 `cat`、`less`、`head`、`tail`、`wc`、`sort`、`uniq`、`cut`、`tr`、`tee`、`stat` 等文件操作命令，学会用 `find` 强大的条件查找文件，理解软链接与硬链接的本质区别，并能用 `tar`、`gzip`、`zip` 完成文件压缩与解压。掌握本章后，你将能像资深运维一样高效地浏览、查找、整理服务器上的各类文件，为后续文本处理与脚本编写打下基础。

## 学习目标

- 熟记 FHS（文件系统层次标准）下各核心目录的用途：`/bin`、`/etc`、`/var`、`/home`、`/opt`、`/tmp`、`/usr`、`/proc`、`/sys`、`/dev`、`/root`、`/lib`、`/boot`
- 区分绝对路径与相对路径，理解 `.`、`..`、`~`、`-` 的含义
- 熟练使用文件查看命令：`cat`、`less`/`more`、`head`、`tail`（含 `-f` 实时追踪）、`nl`、`wc`、`stat`、`file`
- 掌握文本处理命令：`sort`、`uniq`、`cut`、`tr`、`tee`
- 用 `mkdir -p` 创建目录树，用 `tree` 可视化目录结构
- 熟练使用 `find` 按名称、类型、大小、时间、权限、用户等条件查找文件，并用 `-exec` 执行操作
- 理解 `locate` 与 `find` 的差异（速度 vs 实时性）
- 用 `which`、`whereis` 查找命令位置
- 深入理解 inode 概念，区分软链接与硬链接的本质差异
- 掌握 `tar`、`gzip`、`zip`、`xz` 等压缩解压命令
- 熟练使用通配符 `*`、`?`、`[]`、`[!]`

## 理论知识讲解

### 1. FHS 文件系统层次标准

FHS（Filesystem Hierarchy Standard）是 Linux 目录结构的规范，定义了各目录的用途与内容。理解 FHS 后，在任何 Linux 发行版上都能快速找到所需文件。

```
/
├── bin/      基本命令（所有用户可用，如 ls/cat/cp，Ubuntu 已软链接到 /usr/bin）
├── sbin/     系统管理命令（需 root，如 fdisk/reboot，软链接到 /usr/sbin）
├── etc/      配置文件（系统级与应用配置，如 /etc/passwd、/etc/nginx/）
├── var/      可变数据（日志、缓存、邮件、数据库数据）
│   ├── log/      系统与应用日志（/var/log/syslog、/var/log/nginx/）
│   ├── lib/      应用状态数据（/var/lib/mysql、/var/lib/docker/）
│   ├── cache/    缓存数据
│   ├── spool/    队列数据（邮件、打印）
│   └── tmp/      临时文件（重启可能保留）
├── home/     普通用户家目录（/home/deploy、/home/alice）
├── opt/      第三方软件安装目录（如 /opt/ecommerce、/opt/google/chrome）
├── tmp/      临时文件（所有用户可写，重启可能清空）
├── usr/      用户程序与资源（只读数据，可共享）
│   ├── bin/      用户命令（大部分命令在此，如 /usr/bin/python3）
│   ├── sbin/     管理员命令
│   ├── lib/      库文件
│   ├── local/    本地编译安装的软件（/usr/local/bin/、/usr/local/nginx/）
│   └── share/    共享数据（文档、图标、man 手册）
├── proc/     进程信息虚拟文件系统（内核运行时数据，不占磁盘）
├── sys/      设备与内核信息虚拟文件系统（sysfs，比 proc 更结构化）
├── dev/      设备文件（/dev/null、/dev/sda、/dev/tty）
├── root/     root 用户的家目录
├── lib/      系统库文件（.so 动态库，软链接到 /usr/lib）
├── lib64/    64 位库文件
└── boot/     启动文件（内核 vmlinuz、GRUB 引导 /boot/grub/）
```

**核心目录详解**：

| 目录 | 用途 | 示例内容 | 谁可写 |
| --- | --- | --- | --- |
| `/bin` | 基本用户命令 | `ls`、`cat`、`cp`、`bash` | root |
| `/sbin` | 系统管理命令 | `fdisk`、`reboot`、`iptables` | root |
| `/etc` | 配置文件 | `passwd`、`nginx/nginx.conf`、`ssh/sshd_config` | root |
| `/var` | 可变数据 | `log/`、`lib/mysql/`、`cache/` | root/对应服务用户 |
| `/home` | 普通用户家目录 | `deploy/`、`alice/` | 对应用户 |
| `/opt` | 第三方软件 | `ecommerce/`、`google/` | root/部署用户 |
| `/tmp` | 临时文件 | 任何用户临时文件 | 所有用户 |
| `/usr` | 只读用户数据 | `bin/`、`lib/`、`share/` | root |
| `/proc` | 进程虚拟 FS | `cpuinfo`、`meminfo`、`1/`（PID 1） | root（部分只读） |
| `/sys` | 设备虚拟 FS | `class/net/`、`block/` | root |
| `/dev` | 设备文件 | `null`、`sda`、`tty`、`random` | root |
| `/root` | root 家目录 | root 的配置文件 | root |
| `/lib` | 系统库 | `x86_64-linux-gnu/libc.so` | root |
| `/boot` | 启动文件 | `vmlinuz-5.15.0`、`grub/` | root |

> Ubuntu 20.04+ 开始，`/bin`、`/sbin`、`/lib` 已被软链接到 `/usr/bin`、`/usr/sbin`、`/usr/lib`，这是为了支持只读 `/usr` 与原子升级。命令路径不变，但 `ls -l /bin` 会看到它是符号链接。

### 2. 绝对路径与相对路径

| 概念 | 说明 | 示例 |
| --- | --- | --- |
| 绝对路径 | 从根目录 `/` 开始的完整路径，与当前目录无关 | `/opt/ecommerce/backend/app.js` |
| 相对路径 | 从当前目录开始的路径，依赖当前所在位置 | `../logs/access.log`、`./scripts/deploy.sh` |

**特殊目录符号**：

| 符号 | 含义 | 示例 |
| --- | --- | --- |
| `.` | 当前目录 | `./script.sh`（执行当前目录的脚本） |
| `..` | 上级目录 | `cd ..`（回到上级） |
| `~` | 当前用户家目录 | `cd ~`（回家）、`~/scripts`（家目录下的 scripts） |
| `~user` | 指定用户的家目录 | `cd ~mysql`（进入 mysql 用户家目录） |
| `-` | 上一次所在目录 | `cd -`（在两个目录间切换） |

```bash
# 当前在 /opt/ecommerce/backend/src
cd /opt/ecommerce/logs         # 绝对路径
cd ../../logs                  # 相对路径（backend/src → backend → ecommerce → logs）
cd ~/scripts                   # 家目录下的 scripts
cd -                           # 回到上一次的 /opt/ecommerce/backend/src
```

### 3. 文件操作命令

#### 3.1 cat - 查看文件内容

```bash
cat file.txt                   # 输出整个文件
cat -n file.txt                # 显示行号
cat -b file.txt                # 只对非空行编号
cat -s file.txt                # 压缩连续空行为一行
cat -A file.txt                # 显示特殊字符（行尾$、Tab^I）
cat file1 file2 > merged       # 合并多个文件
cat > newfile.txt              # 从标准输入创建文件（Ctrl+D 结束）
```

#### 3.2 less / more - 分页查看

`less` 比 `more` 功能更强（支持向前翻页），是查看大文件的首选：

```bash
less /var/log/syslog           # 分页查看
less -N file.txt               # 显示行号
less -S file.txt               # 不换行（长行截断）

# less 内部快捷键：
#   Space / f    向下翻页
#   b            向上翻页
#   g            跳到文件首
#   G            跳到文件尾
#   /keyword     向下搜索
#   ?keyword     向上搜索
#   n / N        下一个 / 上一个匹配
#   q            退出

more file.txt                  # 简单分页（只能向下翻）
```

#### 3.3 head / tail - 查看头部/尾部

```bash
head file.txt                  # 默认前 10 行
head -n 20 file.txt            # 前 20 行
head -c 100 file.txt           # 前 100 字节
head -n -5 file.txt            # 除最后 5 行外的所有内容

tail file.txt                  # 默认后 10 行
tail -n 20 file.txt            # 后 20 行
tail -c 100 file.txt           # 后 100 字节
tail -n +5 file.txt            # 从第 5 行开始到末尾
tail -f /var/log/syslog        # 实时追踪文件新增内容（运维必备）
tail -F /var/log/syslog        # -F 比 -f 更强：文件被轮转后继续追踪新文件
tail -f access.log | grep 404  # 实时监控并过滤 404 请求
```

#### 3.4 nl - 显示行号

```bash
nl file.txt                    # 显示行号（默认不编号空行）
nl -ba file.txt                # 所有行都编号（包括空行）
nl -bt file.txt                # 只对非空行编号（默认）
```

#### 3.5 wc - 统计行/词/字符

```bash
wc file.txt                    # 行数 单词数 字节数 文件名
wc -l file.txt                 # 仅行数
wc -w file.txt                 # 仅单词数
wc -c file.txt                 # 仅字节数
wc -m file.txt                 # 仅字符数（多字节字符与字节数不同）
wc -L file.txt                 # 最长行的长度
ls -l /etc | wc -l             # 统计 /etc 下文件数（管道组合）
```

#### 3.6 sort - 排序

```bash
sort file.txt                  # 默认按字典序升序
sort -r file.txt               # 降序
sort -n file.txt               # 按数值排序（10 排在 2 之后）
sort -rn file.txt              # 数值降序
sort -u file.txt               # 排序并去重
sort -k 2 file.txt             # 按第 2 列排序
sort -k 2 -n file.txt          # 按第 2 列数值排序
sort -t: -k 3 -n /etc/passwd   # 以 : 分隔，按第 3 列（UID）数值排序
sort -k 2,2 -k 1,1 file.txt    # 先按第 2 列排，再按第 1 列排
```

#### 3.7 uniq - 去重

`uniq` 只能去除**相邻**的重复行，通常先 `sort` 再 `uniq`：

```bash
sort file.txt | uniq           # 排序后去重
sort file.txt | uniq -c        # 去重并统计每行出现次数
sort file.txt | uniq -d        # 仅显示重复的行
sort file.txt | uniq -u        # 仅显示唯一的行（不重复的）
sort file.txt | uniq -c | sort -rn   # 出现次数排序（热门统计）
```

#### 3.8 cut - 分列提取

```bash
cut -d: -f1 /etc/passwd        # 以 : 分隔，取第 1 列（用户名列表）
cut -d: -f1,3 /etc/passwd      # 取第 1 和第 3 列
cut -d: -f3- /etc/passwd       # 取第 3 列到末尾
cut -c 1-10 file.txt           # 按字符位置：每行前 10 个字符
cut -c 5- file.txt             # 每行第 5 个字符到末尾
```

#### 3.9 tr - 替换/删除/压缩字符

```bash
echo "Hello World" | tr 'a-z' 'A-Z'           # 小写转大写
echo "Hello World" | tr 'A-Z' 'a-z'           # 大写转小写
echo "hello   world" | tr -s ' '              # 压缩重复空格为单个
echo "hello world" | tr -d ' '                # 删除所有空格
echo "hello world" | tr -dc 'a-z\n'           # 删除非小写字母（保留换行）
cat file.txt | tr '\t' ' '                    # Tab 转空格
echo "192.168.1.100" | tr '.' '-'             # 点号转横线
```

#### 3.10 tee - 双向输出

`tee` 把输入同时输出到屏幕和文件，常用于管道中保存中间结果：

```bash
ls -l | tee files.txt          # 输出到屏幕同时写入 files.txt
ls -l | tee -a files.txt       # 追加而非覆盖
ls -l | tee a.txt b.txt        # 同时写入多个文件
ls -l | tee files.txt | wc -l  # 保存列表同时统计行数
sudo tee /etc/file <<< "content"   # 用 tee 写入需 root 权限的文件
```

#### 3.11 file / stat - 文件类型与元信息

```bash
file /etc/passwd               # /etc/passwd: ASCII text
file /usr/bin/ls               # /usr/bin/ls: ELF 64-bit LSB shared object
file archive.tar.gz            # archive.tar.gz: gzip compressed data
file -i file.txt               # 显示 MIME 类型（text/plain; charset=utf-8）

stat file.txt                  # 完整元信息：大小/块/IO块/设备/Inode/链接数/权限/UID/GID/访问/修改/变更/出生时间
stat -c '%n %s %y' file.txt    # 自定义格式：文件名 大小 修改时间
stat -c '%a' file.txt          # 仅权限数字（如 644）
```

### 4. 目录操作

```bash
mkdir -p a/b/c                 # 递归创建多级目录
mkdir -m 700 secret            # 创建时指定权限
mkdir -v test                  # 显示创建信息
mkdir project/{backend,frontend,docs}   # 花括号批量创建

rmdir emptydir                 # 仅删空目录
rm -r dir                      # 删除非空目录

tree -L 2 /opt/ecommerce       # 显示 2 层目录树
tree -d /opt/ecommerce         # 仅显示目录
tree -a /opt/ecommerce         # 显示隐藏文件
tree -L 2 -h /opt/ecommerce    # 显示文件大小
tree --dirsfirst /opt/ecommerce # 目录排在前面
```

### 5. 文件查找

#### 5.1 find - 强大的查找工具

`find` 是 Linux 最强大的文件查找命令，支持按名称、类型、大小、时间、权限、用户等多种条件组合查找：

```bash
# 基本语法：find <路径> <条件> <动作>
find /path -name "*.log"                   # 按名称（区分大小写）
find /path -iname "*.LOG"                  # 按名称（不区分大小写）
find /path -type f                         # 仅普通文件
find /path -type d                         # 仅目录
find /path -type l                         # 仅符号链接

# 按大小
find /path -size +100M                     # 大于 100MB 的文件
find /path -size -1k                       # 小于 1KB 的文件
find /path -size 1M                        # 恰好 1MB（很少用）

# 按时间（mmin 分钟，mtime 天）
find /path -mtime -7                       # 7 天内修改过
find /path -mtime +30                      # 30 天前修改过
find /path -mmin -60                       # 60 分钟内修改过
find /path -atime -1                       # 1 天内访问过
find /path -ctime -1                       # 1 天内状态变更

# 按用户与权限
find /path -user deploy                    # 属于 deploy 用户
find /path -group www-data                 # 属于 www-data 组
find /path -perm 644                       # 权限恰好 644
find /path -perm -644                      # 权限至少包含 644（u+rw,g+r,o+r）
find /path -perm /644                      # 权限包含 644 任一位（u 或 g 或 o 有 r 或 w）
find /path -empty                          # 空文件或空目录

# 逻辑组合
find /path -name "*.log" -a -size +10M     # AND（默认）
find /path -name "*.log" -o -name "*.txt"  # OR
find /path -not -name "*.log"              # NOT
find /path \( -name "*.log" -o -name "*.txt" \) -size +1M   # 括号分组

# 动作
find /path -name "*.log" -print            # 打印路径（默认动作）
find /path -name "*.log" -ls               # 详细信息（等同 ls -l）
find /path -name "*.log" -delete           # 删除（危险！先 -print 确认）
find /path -name "*.log" -exec wc -l {} \;           # 对每个文件执行命令
find /path -name "*.log" -exec wc -l {} +            # 批量执行（性能更好）
find /path -name "*.log" -exec cp {} /backup/ \;     # 复制到 /backup
find /path -name "*.log" -ok rm {} \;                # 交互式执行（每次确认）
```

**find 常用场景**：

```bash
# 找出 7 天前的日志并压缩归档
find /opt/ecommerce/logs -name "*.log" -mtime +7 -exec gzip {} \;

# 找出大于 100MB 的文件（排查磁盘占用）
find / -type f -size +100M 2>/dev/null

# 找出所有属于 deploy 的文件
find /opt/ecommerce -user deploy -type f

# 删除所有 .tmp 文件（先预览再执行）
find /tmp -name "*.tmp" -print           # 先预览
find /tmp -name "*.tmp" -delete          # 确认后删除

# 找出最近 1 小时修改过的 .js 文件
find /opt/ecommerce/backend -name "*.js" -mmin -60
```

#### 5.2 locate - 快速查找

`locate` 通过查询预建的文件名数据库实现毫秒级查找，但结果不是实时的：

```bash
sudo updatedb                  # 手动更新数据库（通常 cron 每天自动更新）
locate nginx.conf              # 查找名为 nginx.conf 的文件
locate -i nginx.conf           # 忽略大小写
locate -c nginx                # 仅统计匹配数量
locate -r '\.log$'             # 使用正则
locate -n 10 nginx             # 限制结果数量
```

**find vs locate 对比**：

| 维度 | find | locate |
| --- | --- | --- |
| 查找方式 | 实时遍历目录 | 查询预建数据库 |
| 速度 | 慢（取决于目录大小） | 极快（毫秒级） |
| 实时性 | 实时 | 依赖 updatedb（通常每天一次） |
| 条件 | 丰富（大小/时间/权限/用户等） | 仅文件名 |
| 资源消耗 | 高（遍历磁盘） | 低（查数据库） |
| 适用场景 | 精确查找、复杂条件 | 快速定位文件路径 |

#### 5.3 which / whereis - 查找命令位置

```bash
which python3                  # 查找命令的可执行文件路径（仅 $PATH 中）
which -a python3               # 显示所有匹配（含别名）
whereis python3                # 查找可执行文件、源码、man 手册
whereis -b python3             # 仅二进制
whereis -m python3             # 仅 man 手册
type ls                        # 查看命令类型（builtin/alias/file）
```

### 6. 软链接与硬链接

#### 6.1 inode 概念

Linux 文件系统把文件分为两部分：**inode**（索引节点）和**数据块**。

- **inode**：存储文件的元信息（权限、所有者、大小、时间戳、数据块位置），每个文件有唯一 inode 号
- **数据块**：存储文件的实际内容
- **文件名**：只是 inode 的一个别名（目录项），同一个 inode 可以有多个文件名

```bash
ls -i file.txt                 # 查看文件的 inode 号
stat file.txt                  # 查看 inode 详细信息
df -i                          # 查看文件系统 inode 使用情况
```

#### 6.2 硬链接（Hard Link）

硬链接是同一个 inode 的多个文件名，它们指向同一份数据：

```bash
ln file.txt hardlink.txt       # 创建硬链接
ls -li file.txt hardlink.txt   # 两者的 inode 号相同，链接数变为 2
```

#### 6.3 软链接（Symbolic Link / 软链接）

软链接是一个独立文件，存储的是另一个文件的路径（类似 Windows 快捷方式）：

```bash
ln -s file.txt softlink.txt    # 创建软链接
ls -li file.txt softlink.txt   # 两者的 inode 号不同
readlink softlink.txt          # 查看软链接指向
readlink -f softlink.txt       # 解析所有软链接，得到最终绝对路径
```

#### 6.4 软链接 vs 硬链接对比

| 维度 | 软链接（Symbolic Link） | 硬链接（Hard Link） |
| --- | --- | --- |
| 创建命令 | `ln -s source link` | `ln source link` |
| inode | 不同（独立 inode） | 相同（共享 inode） |
| 本质 | 存储源文件路径的独立文件 | 同一 inode 的多个文件名 |
| 跨文件系统 | 可以 | 不可以（inode 是文件系统内的） |
| 指向目录 | 可以 | 不可以（避免循环） |
| 源文件删除后 | 失效（悬空链接） | 不受影响（数据仍在，链接数 -1） |
| 源文件移动后 | 失效（路径变了） | 不受影响（inode 不变） |
| 源文件替换后 | 指向新文件 | 仍指向旧数据 |
| 占用空间 | 一个 inode + 路径字符串 | 仅增加目录项（不占额外数据块） |
| 创建后链接数变化 | 不变 | +1 |
| 适用场景 | 跨目录引用、版本切换、配置文件 | 文件备份、防误删 |

**示例**：

```bash
# 准备源文件
echo "Hello Linux" > original.txt

# 创建硬链接与软链接
ln original.txt hard.txt
ln -s original.txt soft.txt

# 查看 inode 与链接数
ls -li original.txt hard.txt soft.txt
# 1234567 -rw-r--r-- 2 deploy deploy 12 ... original.txt   ← 链接数=2
# 1234567 -rw-r--r-- 2 deploy deploy 12 ... hard.txt       ← 同 inode，链接数=2
# 1234568 lrwxrwxrwx 1 deploy deploy 12 ... soft.txt -> original.txt  ← 不同 inode

# 删除源文件
rm original.txt
cat hard.txt                   # 正常输出（数据仍在）
cat soft.txt                   # 报错：No such file or directory（悬空链接）

# 软链接的典型应用
ln -s /opt/ecommerce/backend/v2 /opt/ecommerce/backend/current
# 切换版本只需改软链接指向，无需改配置
```

> 软链接在生产环境常用于：版本切换（current → v2.1.0）、配置统一管理（`/etc/nginx/sites-enabled/app.conf` → `/etc/nginx/sites-available/app.conf`）、跨磁盘引用。

### 7. 文件压缩与解压

#### 7.1 tar - 打包与压缩

`tar`（Tape Archive）原用于磁带备份，现是最常用的打包压缩工具。**打包**与**压缩**是两个概念：tar 默认只打包不压缩，压缩需配合 `gzip`/`bzip2`/`xz` 等：

```bash
# 基本选项：
#   c - create 创建归档
#   x - extract 解压归档
#   t - list 列出归档内容
#   v - verbose 显示过程
#   f - file 指定归档文件名（必须放最后）
#   z - gzip 压缩/解压（.tar.gz / .tgz）
#   j - bzip2 压缩/解压（.tar.bz2）
#   J - xz 压缩/解压（.tar.xz）
#   C - 指定解压目录

# 打包（不压缩）
tar -cvf archive.tar dir/              # 打包 dir/ 为 archive.tar
tar -cvf archive.tar file1 file2       # 打包多个文件

# .tar.gz（最常用，gzip 压缩，速度最快）
tar -zcvf archive.tar.gz dir/          # 压缩
tar -zxvf archive.tar.gz               # 解压
tar -ztvf archive.tar.gz               # 查看内容（不解压）

# .tar.bz2（bzip2 压缩，压缩率更高，速度更慢）
tar -jcvf archive.tar.bz2 dir/         # 压缩
tar -jxvf archive.tar.bz2              # 解压

# .tar.xz（xz 压缩，压缩率最高，速度最慢）
tar -Jcvf archive.tar.xz dir/          # 压缩
tar -Jxvf archive.tar.xz               # 解压

# 解压到指定目录
tar -zxvf archive.tar.gz -C /opt/ecommerce/backup/

# 仅解压部分文件
tar -zxvf archive.tar.gz path/to/file

# 排除某些文件
tar -zcvf archive.tar.gz dir/ --exclude="*.log" --exclude="node_modules"
```

#### 7.2 gzip / gunzip

```bash
gzip file.txt                  # 压缩为 file.txt.gz（原文件消失）
gzip -k file.txt               # 保留原文件
gzip -c file.txt > file.txt.gz # 输出到 stdout，保留原文件
gzip -d file.txt.gz            # 解压
gunzip file.txt.gz             # 等同 gzip -d
gzip -l file.txt.gz            # 查看压缩信息
gzip -9 file.txt               # 最高压缩率（1-9，默认 6）
zcat file.txt.gz               # 直接查看压缩文件内容
zgrep "error" file.txt.gz      # 在压缩文件中搜索
```

#### 7.3 zip / unzip

```bash
zip archive.zip file1 file2    # 压缩多个文件
zip -r archive.zip dir/        # 递归压缩目录
zip -e archive.zip file.txt    # 加密码
zip -r archive.zip dir/ -x "*.log"   # 排除文件
unzip archive.zip              # 解压
unzip archive.zip -d /tmp/     # 解压到指定目录
unzip -l archive.zip           # 查看内容
unzip -v archive.zip           # 详细查看
```

#### 7.4 xz / zstd

```bash
# xz - 压缩率最高
xz file.txt                   # 压缩为 file.txt.xz
xz -k file.txt                # 保留原文件
xz -d file.txt.xz             # 解压
unxz file.txt.xz              # 等同 xz -d
xzcat file.txt.xz             # 查看压缩文件内容

# zstd - 新一代压缩（Facebook 开源，速度极快）
zstd file.txt                 # 压缩为 file.txt.zst
zstd -d file.txt.zst          # 解压
tar --zstd -cvf archive.tar.zst dir/   # tar + zstd
```

#### 7.5 压缩格式对比

| 格式 | 压缩率 | 速度 | 命令 | 适用场景 |
| --- | --- | --- | --- | --- |
| `.zip` | 中 | 快 | zip/unzip | Windows 互通 |
| `.tar.gz` | 中 | 最快 | tar -z | 最常用，日志归档 |
| `.tar.bz2` | 高 | 慢 | tar -j | 大文件归档 |
| `.tar.xz` | 最高 | 最慢 | tar -J | 源码包分发 |
| `.zst` | 高 | 极快 | zstd | 新趋势，软件包 |

### 8. 通配符

通配符（glob）由 Shell 解释，用于匹配文件名：

| 通配符 | 含义 | 示例 |
| --- | --- | --- |
| `*` | 匹配任意长度任意字符 | `*.log` 匹配所有 .log 文件 |
| `?` | 匹配单个任意字符 | `file?.txt` 匹配 file1.txt、fileA.txt |
| `[abc]` | 匹配方括号内任一字符 | `file[123].txt` 匹配 file1.txt、file2.txt、file3.txt |
| `[a-z]` | 匹配字符范围 | `file[a-z].txt` 匹配 filea.txt 到 filez.txt |
| `[!abc]` 或 `[^abc]` | 匹配不在括号内的字符 | `file[!0-9].txt` 匹配 filea.txt 不匹配 file1.txt |
| `{a,b,c}` | 花括号展开（不是匹配，是生成） | `file{1,2,3}.txt` 生成 file1.txt、file2.txt、file3.txt |

**示例**：

```bash
ls *.sh                        # 所有 .sh 文件
ls *.log *.txt                 # 所有 .log 和 .txt 文件
ls file?.txt                   # file1.txt、fileA.txt
ls file[0-9].txt               # file0.txt 到 file9.txt
ls [!.]*                       # 不以 . 开头的文件
mkdir {backend,frontend,docs}  # 花括号生成（不是匹配）
mkdir {2023,2024}/{01,02,03}   # 生成 2023/01、2023/02、...、2024/03
mv *.log /backup/              # 移动所有 .log 文件
```

**特殊字符与转义**：

当文件名包含特殊字符（空格、`$`、`*`、`?` 等）时，需用引号或转义：

```bash
# 文件名含空格
ls "my file.txt"               # 用双引号
ls 'my file.txt'               # 用单引号（更强，不解析变量）
ls my\ file.txt                # 用反斜杠转义空格

# 文件名以 - 开头
rm -- -file.txt                # -- 表示选项结束
rm ./-file.txt                 # 用 ./ 前缀

# 文件名含 *
ls 'file*.txt'                 # 单引号防止通配符展开
```

## 关键知识点总结

### FHS 目录速查表

| 目录 | 用途 | 关键内容 |
| --- | --- | --- |
| `/bin` `/usr/bin` | 用户命令 | ls、cat、grep |
| `/sbin` `/usr/sbin` | 管理命令 | fdisk、systemctl |
| `/etc` | 配置文件 | passwd、nginx/、ssh/ |
| `/var/log` | 日志 | syslog、nginx/access.log |
| `/var/lib` | 应用数据 | mysql/、docker/ |
| `/home` | 用户家目录 | /home/deploy |
| `/opt` | 第三方软件 | /opt/ecommerce |
| `/tmp` | 临时文件 | 重启可能清空 |
| `/usr/local` | 本地编译安装 | nginx、python |
| `/proc` | 进程虚拟 FS | /proc/cpuinfo、/proc/1/ |
| `/sys` | 设备虚拟 FS | /sys/class/net/ |
| `/dev` | 设备文件 | /dev/null、/dev/sda |
| `/root` | root 家目录 | |
| `/lib` `/usr/lib` | 库文件 | .so 动态库 |
| `/boot` | 启动文件 | vmlinuz、grub/ |

### find 常用条件速查

| 条件 | 含义 | 示例 |
| --- | --- | --- |
| `-name "*.log"` | 按名称（区分大小写） | 匹配 a.log |
| `-iname "*.LOG"` | 按名称（忽略大小写） | 匹配 a.LOG、a.log |
| `-type f/d/l` | 类型：文件/目录/链接 | `-type f` 仅文件 |
| `-size +100M` | 大于 100MB | `-size -1k` 小于 1KB |
| `-mtime -7` | 7 天内修改 | `-mtime +30` 30 天前 |
| `-mmin -60` | 60 分钟内修改 | |
| `-user deploy` | 属于 deploy | `-group www-data` |
| `-perm 644` | 权限恰好 644 | `-perm -644` 至少包含 |
| `-empty` | 空文件/空目录 | |
| `-a` | AND（默认） | `-name "*.log" -a -size +10M` |
| `-o` | OR | `-name "*.log" -o -name "*.txt"` |
| `-not` | NOT | `-not -name "*.log"` |
| `-exec cmd {} \;` | 对结果执行命令 | `-exec gzip {} \;` |
| `-delete` | 删除结果 | 先 `-print` 确认 |

### 软链接 vs 硬链接对比表

| 维度 | 软链接 | 硬链接 |
| --- | --- | --- |
| 命令 | `ln -s src link` | `ln src link` |
| inode | 不同 | 相同 |
| 跨文件系统 | 可以 | 不可以 |
| 指向目录 | 可以 | 不可以 |
| 源文件删除 | 失效 | 不受影响 |
| 链接数变化 | 不变 | +1 |
| 应用 | 版本切换、快捷方式 | 防误删、备份 |

### 压缩命令速查表

| 命令 | 压缩 | 解压 | 查看 | 格式 |
| --- | --- | --- | --- | --- |
| tar + gzip | `tar -zcvf a.tar.gz dir` | `tar -zxvf a.tar.gz` | `tar -ztvf a.tar.gz` | .tar.gz |
| tar + bzip2 | `tar -jcvf a.tar.bz2 dir` | `tar -jxvf a.tar.bz2` | `tar -jtvf a.tar.bz2` | .tar.bz2 |
| tar + xz | `tar -Jcvf a.tar.xz dir` | `tar -Jxvf a.tar.xz` | `tar -Jtvf a.tar.xz` | .tar.xz |
| gzip | `gzip file` | `gunzip file.gz` | `zcat file.gz` | .gz |
| zip | `zip -r a.zip dir` | `unzip a.zip` | `unzip -l a.zip` | .zip |
| xz | `xz file` | `unxz file.xz` | `xzcat file.xz` | .xz |
| zstd | `zstd file` | `zstd -d file.zst` | `tar --zstd -tvf` | .zst |

## 代码文件说明

| 文件 | 用途 | 执行方式 |
| --- | --- | --- |
| `Code/01-file-operations.sh` | 文件操作练习（cat/less/head/tail/wc/sort/uniq/cut/tr/tee/stat），先创建模拟日志 | `bash 01-file-operations.sh` |
| `Code/02-file-search.sh` | 文件查找练习（find 各种条件、locate、which/whereis） | `bash 02-file-search.sh` |
| `Code/03-compression.sh` | 压缩解压练习（tar/gzip/zip/xz） | `bash 03-compression.sh` |

## 实战练习

### 练习一：日志文件分析

在 `/opt/ecommerce/logs/` 下完成（先执行 `Code/01-file-operations.sh` 生成模拟日志）：

1. 用 `wc -l` 统计 `access.log` 的总行数
2. 用 `tail -f` 实时监控 `access.log` 的新增内容（按 Ctrl+C 退出）
3. 用 `cut` 提取所有访问 IP（第一列），`sort | uniq -c | sort -rn` 统计访问量 Top 10 IP
4. 用 `grep` 过滤出所有 404 状态的请求（Day03 学习 grep 后再做）
5. 用 `head -n 1 access.log` 查看日志格式，`tail -n 1` 看最后一条
6. 用 `stat` 查看 `access.log` 的大小与最后修改时间

### 练习二：find 实战

1. 在 `/opt/ecommerce/` 下找出所有 `.js` 文件：`find /opt/ecommerce -name "*.js"`
2. 找出最近 24 小时修改过的文件：`find /opt/ecommerce -mtime -1`
3. 找出大于 1MB 的日志文件：`find /opt/ecommerce/logs -size +1M`
4. 找出所有空目录：`find /opt/ecommerce -type d -empty`
5. 把 7 天前的日志压缩归档到 backup 目录：
   ```bash
   find /opt/ecommerce/logs -name "*.log" -mtime +7 -exec gzip {} \;
   find /opt/ecommerce/logs -name "*.gz" -exec mv {} /opt/ecommerce/backup/ \;
   ```
6. 用 `tree -L 3 /opt/ecommerce` 查看整个项目目录结构

### 练习三：链接与压缩

1. 创建一个软链接指向当前项目目录：`ln -s /opt/ecommerce/backend /opt/ecommerce/current`
2. 创建一个硬链接：`ln /opt/ecommerce/logs/access.log /tmp/access-hardlink`
3. 用 `ls -li` 对比软硬链接的 inode 与链接数
4. 删除原文件后观察软硬链接的状态
5. 把整个 `/opt/ecommerce/scripts/` 打包为 `scripts.tar.gz`
6. 把 `/opt/ecommerce/logs/` 打包为 `logs-$(date +%Y%m%d).tar.bz2`
7. 解压到 `/tmp/test-extract/` 目录验证内容
