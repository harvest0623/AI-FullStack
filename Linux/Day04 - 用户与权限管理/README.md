# Day04 - 用户与权限管理

## 本章简介

多用户是 Linux 的核心特性，权限管理是服务器安全的基础。从大型机的多用户分时系统到现代云服务器，Linux 一开始就是为多用户协作设计的——不同用户拥有独立的家目录、不同的文件权限、不同的系统访问能力。这种设计让多个服务（Nginx、MySQL、Redis）可以各自以独立用户身份运行，即使某个服务被攻破，攻击者也难以直接获取整个系统的控制权。

本章深入讲解 Linux 用户体系（root / 系统用户 / 普通用户）、用户与组管理命令（useradd / usermod / userdel / groupadd / gpasswd）、su 与 sudo 的差异与安全配置、文件权限模型（rwx / 数字法 / 符号法）、特殊权限位（SUID / SGID / Sticky Bit）、umask 默认权限、ACL 访问控制列表，以及 SSH 密钥认证配置。掌握本章后，你将能为电商项目的 deploy、www-data、mysql、redis 等用户合理分配权限，配置安全的 SSH 免密登录，搭建符合生产安全标准的服务器。

## 学习目标

- 理解 Linux 用户体系：root（UID 0）、系统用户（UID 1-999）、普通用户（UID 1000+）
- 读懂 `/etc/passwd`、`/etc/shadow`、`/etc/group`、`/etc/gshadow` 四大配置文件
- 熟练使用用户管理命令：`useradd`、`usermod`、`userdel`、`passwd`、`id`、`whoami`、`who`、`w`、`last`
- 熟练使用用户组管理命令：`groupadd`、`groupmod`、`groupdel`、`gpasswd`、`newgrp`
- 区分 `su` 与 `sudo`，理解 `sudoers` 语法与安全实践
- 用 `visudo` 编辑 sudoers 文件，配置最小权限的 sudo 规则
- 理解文件权限模型：`r`（读 4）、`w`（写 2）、`x`（执行 1），三组权限（所有者/组/其他）
- 熟练使用 `chmod`（数字法与符号法）、`chown`、`chgrp`
- 理解特殊权限位：SUID（4000）、SGID（2000）、Sticky Bit（1000）
- 理解 `umask` 默认权限掩码的计算方式
- 使用 ACL（`setfacl` / `getfacl`）实现更细粒度的权限控制
- 配置 SSH 密钥认证：`ssh-keygen`、`ssh-copy-id`、`authorized_keys`、禁用密码登录

## 理论知识讲解

### 1. Linux 用户体系

Linux 是多用户操作系统，每个用户有唯一的 UID（User ID），用户通过 UID 而非用户名被系统识别。

#### 1.1 用户类型

| 类型 | UID 范围 | 说明 | 示例 |
| --- | --- | --- | --- |
| root（超级用户） | 0 | 拥有系统最高权限，可访问所有文件 | root |
| 系统用户 | 1-999 | 运行系统服务，通常不允许登录，无家目录或家目录不可访问 | www-data、mysql、redis、nginx、sshd |
| 普通用户 | 1000+ | 日常使用的用户，权限受限，只能访问自己有权限的文件 | deploy、alice、bob |

```bash
# 查看当前用户
whoami                          # 当前用户名
id                              # 当前用户的 UID、GID、所属组
id deploy                       # 查看指定用户信息

# 查看所有用户
cat /etc/passwd | cut -d: -f1   # 所有用户名列表
getent passwd                   # 等同 cat /etc/passwd（但包含 LDAP 用户）

# 查看登录用户
who                             # 当前登录的用户
w                               # 登录用户及其活动
last                            # 登录历史记录
last -n 10                      # 最近 10 次登录
lastlog                         # 所有用户最后登录时间
```

#### 1.2 用户配置文件

Linux 用户信息存储在四个核心文件中：

| 文件 | 作用 | 权限 |
| --- | --- | --- |
| `/etc/passwd` | 用户基本信息（所有用户可读） | 644 |
| `/etc/shadow` | 用户密码哈希（仅 root 可读） | 640 或 600 |
| `/etc/group` | 用户组信息 | 644 |
| `/etc/gshadow` | 用户组密码（很少用） | 640 或 600 |

**`/etc/passwd` 字段解析**：

```
deploy:x:1000:1000:Deploy User:/home/deploy:/bin/bash
└──┬─┘└┬┘└──┬──┘└──┬──┘└────┬─────┘└──────┬───────┘└───┬───┘
   │   │     │       │         │              │            │
   │   │     │       │         │              │            └─ 7. 登录 Shell（/bin/bash、/sbin/nologin）
   │   │     │       │         │              └─ 6. 家目录
   │   │     │       │         └─ 5. 描述信息（GECOS）
   │   │     │       └─ 4. GID（主组 ID）
   │   │     └─ 3. UID
   │   └─ 2. 密码占位（x 表示密码在 /etc/shadow）
   └─ 1. 用户名
```

**`/etc/shadow` 字段解析**：

```
deploy:$6$xxx...:19000:0:99999:7:::
└──┬──┘└──┬───┘└─┬──┘└┬┘└─┬──┘└┬┘└┬┘└┬┘
   │      │      │    │    │    │  │  │
   │      │      │    │    │    │  │  └─ 9. 保留字段
   │      │      │    │    │    │  └─ 8. 账户过期日期
   │      │      │    │    │    └─ 7. 密码过期后宽限期
   │      │      │    │    └─ 6. 密码过期前警告天数
   │      │      │    └─ 5. 密码最大使用天数
   │      │      └─ 4. 密码最小使用天数（0 可随时改）
   │      └─ 3. 密码最后修改日期（距 1970-01-01 的天数）
   └─ 2. 密码哈希（$6$ 表示 SHA-512，$1$ MD5，$5$ SHA-256）
       1. 用户名
```

> 密码哈希算法标识：`$1$`=MD5（不安全）、`$5$`=SHA-256、`$6$`=SHA-512（默认）、`$y$`=yescrypt（新算法）。

### 2. 用户管理

#### 2.1 useradd - 创建用户

```bash
# 基本创建
sudo useradd deploy                     # 创建用户（默认无家目录）
sudo useradd -m deploy                  # -m 创建家目录
sudo useradd -m -s /bin/bash deploy     # -s 指定登录 Shell

# 完整创建
sudo useradd -m -s /bin/bash \
    -c "Deploy User" \                  # -c 备注信息
    -d /home/deploy \                   # -d 指定家目录
    -u 1000 \                           # -u 指定 UID
    -G sudo,docker \                    # -G 附加组（多个用逗号分隔）
    deploy

# 创建系统用户（运行服务，不登录）
sudo useradd -r -s /sbin/nologin \
    -d /opt/mysql \
    -M mysql                            # -M 不创建家目录
```

| 选项 | 含义 |
| --- | --- |
| `-m` | 创建家目录（`/home/用户名`） |
| `-M` | 不创建家目录 |
| `-d path` | 指定家目录路径 |
| `-s shell` | 指定登录 Shell |
| `-u UID` | 指定 UID |
| `-g group` | 指定主组（组需已存在） |
| `-G group1,group2` | 指定附加组 |
| `-c "comment"` | 备注信息 |
| `-r` | 创建系统用户（UID 1-999） |
| `-e YYYY-MM-DD` | 账户过期日期 |
| `-f days` | 密码过期后多少天禁用账户 |

#### 2.2 usermod - 修改用户

```bash
sudo usermod -aG sudo deploy            # -aG 追加到附加组（不改原组）
sudo usermod -aG docker,www-data deploy # 追加多个组
sudo usermod -s /bin/zsh deploy         # 修改 Shell
sudo usermod -c "New Name" deploy       # 修改备注
sudo usermod -L deploy                  # 锁定账户（密码前加 !）
sudo usermod -U deploy                  # 解锁账户
sudo usermod -u 1500 deploy             # 修改 UID
sudo usermod -l newname oldname         # 改用户名（不推荐，易出问题）
sudo usermod -e 2026-12-31 deploy       # 设置账户过期日期
```

> ⚠️ `usermod -G`（无 -a）会用新的附加组列表**替换**原有附加组，加 `-a` 才是追加。这是最常见的新手错误。

#### 2.3 userdel - 删除用户

```bash
sudo userdel deploy                     # 删除用户（保留家目录）
sudo userdel -r deploy                  # -r 同时删除家目录与邮箱
sudo userdel -rf deploy                 # -f 强制删除（即使登录中）
```

> 删除用户前建议先备份家目录：`tar -zcvf deploy-home.tar.gz /home/deploy`。

#### 2.4 passwd - 密码管理

```bash
sudo passwd deploy                      # 设置/修改密码
passwd                                  # 修改自己的密码
sudo passwd -l deploy                   # 锁定密码（禁用密码登录）
sudo passwd -u deploy                   # 解锁密码
sudo passwd -d deploy                   # 删除密码（变为无密码）
sudo passwd -S deploy                   # 查看密码状态
# 输出示例：deploy P 07/29/2026 0 99999 7 -1
#          P=正常, L=锁定, NP=无密码
```

### 3. 用户组管理

每个用户必须属于一个主组（primary group），还可以属于多个附加组（supplementary group）。

#### 3.1 groupadd / groupmod / groupdel

```bash
sudo groupadd developers                # 创建组
sudo groupadd -g 2000 developers        # -g 指定 GID
sudo groupmod -n devs developers        # -n 改组名
sudo groupmod -g 2500 developers        # -g 改 GID
sudo groupdel developers                # 删除组（组内不能有用户）
```

#### 3.2 gpasswd - 组成员管理

```bash
sudo gpasswd -a deploy developers       # 添加用户到组
sudo gpasswd -d deploy developers       # 从组移除用户
sudo gpasswd -A deploy developers       # 设置 deploy 为组管理员
sudo gpasswd developers                 # 设置组密码（很少用）
```

> 更常用的添加用户到组方式：`sudo usermod -aG developers deploy`。

#### 3.3 newgrp - 切换当前组

```bash
groups deploy                           # 查看 deploy 所属的组
newgrp developers                       # 临时切换当前会话的主组到 developers
# 切换后新建的文件将属于 developers 组
```

### 4. su 与 sudo

#### 4.1 su - 切换用户

```bash
su                                      # 切换到 root（需输入 root 密码）
su -                                    # 切换到 root 并加载环境变量（推荐）
su - root                               # 等同 su -
su - deploy                             # 切换到 deploy 用户
su deploy                               # 切换但不加载环境（不推荐）
```

`-` 的区别：加 `-` 会加载目标用户的环境变量（家目录、PATH、配置文件），不加则保留当前环境。

#### 4.2 sudo - 临时提权

```bash
sudo command                            # 以 root 身份执行命令
sudo -u www-data command                # 以指定用户身份执行
sudo -i                                 # 启动交互式 root Shell（等同 su -）
sudo -s                                 # 启动 Shell 但不加载环境
sudo -l                                 # 查看当前用户的 sudo 权限
sudo -ll                                # 详细查看 sudo 权限
sudo -k                                 # 清除缓存密码（下次需重新输入）
```

**sudo vs su 对比**：

| 维度 | su | sudo |
| --- | --- | --- |
| 需要的密码 | 目标用户密码（root 密码） | 当前用户自己的密码 |
| 权限粒度 | 全部切换 | 可限制具体命令 |
| 日志审计 | 不记录具体命令 | 记录每条命令（/var/log/auth.log） |
| 安全性 | 较低（root 密码多人共享） | 较高（各用户用自己密码） |
| 适用场景 | 临时切换用户身份 | 执行需特权的单条命令 |

#### 4.3 sudoers 配置

sudo 权限由 `/etc/sudoers` 文件控制，**必须用 `visudo` 编辑**（会检查语法，防止配置错误导致无法 sudo）：

```bash
sudo visudo                             # 编辑 /etc/sudoers（推荐）
sudo visudo -f /etc/sudoers.d/deploy    # 编辑独立配置文件（推荐方式）
```

**sudoers 语法**：

```
用户  主机=(运行身份) [NOPASSWD:] 命令列表
```

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| 用户 | 用户名或 %组名 | `deploy`、`%sudo` |
| 主机 | 允许的主机名 | `ALL`、`ecommerce-server` |
| 运行身份 | 以谁的身份运行 | `ALL`、`root` |
| NOPASSWD | 免密码 | `NOPASSWD:` |
| 命令列表 | 允许执行的命令 | `ALL`、`/usr/bin/systemctl restart nginx` |

**示例**：

```
# 允许 deploy 在所有主机上以任何身份执行任何命令（免密）
deploy ALL=(ALL) NOPASSWD: ALL

# 允许 deploy 仅重启 nginx 和 mysql
deploy ALL=(ALL) /usr/bin/systemctl restart nginx, /usr/bin/systemctl restart mysql

# 允许 developers 组查看系统状态
%developers ALL=(ALL) /usr/bin/systemctl status, /usr/bin/journalctl

# 允许 www-data 用户重启自己管理的服务
www-data ALL=(root) NOPASSWD: /usr/bin/systemctl reload nginx
```

> 推荐把自定义规则放在 `/etc/sudoers.d/` 目录下（如 `/etc/sudoers.d/deploy`），而不是直接修改 `/etc/sudoers`。这样便于管理与回滚。

### 5. 文件权限

#### 5.1 权限模型

Linux 文件权限分为三组，每组三个位：

```
-rwxr-xr--
└┬┘└┬┘└┬┘└┬┘
 │  │  │  │
 │  │  │  └─ 其他用户（Other）：r--（读）
 │  │  └──── 所属组（Group）：r-x（读+执行）
 │  └───────── 所有者（Owner）：rwx（读+写+执行）
 └──────────── 文件类型（- 普通文件，d 目录，l 软链接，c 字符设备，b 块设备）
```

**权限含义**：

| 权限 | 对文件 | 对目录 | 数字 |
| --- | --- | --- | --- |
| r（read） | 可查看内容（cat/less） | 可列出目录内容（ls） | 4 |
| w（write） | 可修改内容（vim/echo >） | 可在目录中创建/删除文件 | 2 |
| x（execute） | 可执行（./script.sh） | 可进入目录（cd） | 1 |

> 目录的 x 权限是进入目录的前提，没有 x 即使有 r 也无法 `cd` 进入（但可 `ls` 列出文件名）。

#### 5.2 chmod - 修改权限

**数字法**（最常用）：

```bash
chmod 755 file              # rwxr-xr-x（所有者全，组与其他读+执行）
chmod 644 file              # rw-r--r--（所有者读写，其他只读）
chmod 600 file              # rw-------（仅所有者读写，如 SSH 私钥）
chmod 777 file              # rwxrwxrwx（全开，危险！）
chmod 700 dir               # rwx------（仅所有者可访问，如 ~/.ssh）
chmod 444 file              # r--r--r--（全部只读）
chmod 000 file              # ----------（无任何权限）

# 数字计算：r=4, w=2, x=1，三组相加
# 755 = (4+2+1)(4+0+1)(4+0+1) = rwxr-xr-x
# 640 = (4+2)(4+0)(0) = rw-r-----

# 批量修改
chmod -R 755 dir/           # 递归修改目录及子文件
chmod 644 *.txt             # 所有 txt 文件
```

**符号法**：

```bash
chmod u+x file              # 所有者增加执行权限
chmod u-x file              # 所有者去除执行权限
chmod g+w file              # 组增加写权限
chmod o-w file              # 其他去除写权限
chmod o=r file              # 其他设为只读（覆盖原权限）
chmod a+r file              # 所有人增加读权限（a=all）
chmod u+x,g+w file          # 多个修改
chmod ug+x file             # 所有者和组增加执行
chmod a=rwx file            # 所有人设为 rwx
chmod +x script.sh          # 等同 a+x（所有人增加执行）
```

| 符号 | 含义 |
| --- | --- |
| `u` | 所有者（user） |
| `g` | 组（group） |
| `o` | 其他（other） |
| `a` | 所有人（all，默认） |
| `+` | 增加权限 |
| `-` | 去除权限 |
| `=` | 设置权限（覆盖） |

#### 5.3 chown / chgrp - 修改所有者与组

```bash
sudo chown deploy file              # 修改所有者为 deploy
sudo chown deploy:www-data file     # 修改所有者与组
sudo chown :www-data file           # 仅修改组
sudo chgrp www-data file            # 等同 chown :www-data
sudo chown -R deploy:deploy dir/    # 递归修改目录及内容
sudo chown deploy *.txt             # 批量修改
```

### 6. 特殊权限位

除了 rwx 三种基本权限，Linux 还有三种特殊权限位：

#### 6.1 SUID（Set User ID，4000）

执行该文件时，进程以**文件所有者**的身份运行，而非执行者的身份。

```bash
# 典型例子：/usr/bin/passwd
ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root ... /usr/bin/passwd
#  注意 s 替代了 x，表示 SUID

# 普通用户执行 passwd 时，进程以 root 身份运行，
# 这样才能修改 /etc/shadow（仅 root 可写）

# 设置 SUID
sudo chmod u+s file          # 符号法
sudo chmod 4755 file         # 数字法（在原权限前加 4）

# 去除 SUID
sudo chmod u-s file
sudo chmod 755 file
```

> ⚠️ SUID 很危险：如果给一个脚本设 SUID 且所有者是 root，任何人执行该脚本都能以 root 身份运行。生产环境慎用。

#### 6.2 SGID（Set Group ID，2000）

- 对文件：执行时以文件所属组身份运行
- 对目录：目录下新建的文件**继承目录的所属组**（而非创建者的主组）

```bash
# 目录设置 SGID（团队共享目录常用）
sudo chmod g+s shared_dir
# 之后任何人在 shared_dir 下创建的文件，组都是 shared_dir 的组

ls -l shared_dir
# drwxr-sr-x 2 deploy developers ... shared_dir
#  注意 s 替代了组的 x

# 设置
sudo chmod g+s dir           # 符号法
sudo chmod 2755 dir          # 数字法（前面加 2）
```

#### 6.3 Sticky Bit（1000）

目录设置 Sticky Bit 后，目录下的文件**只有所有者（或 root）才能删除**，即使其他用户对该目录有写权限。

```bash
# 典型例子：/tmp
ls -ld /tmp
# drwxrwxrwt 15 root root ... /tmp
#  注意 t 替代了其他的 x

# /tmp 所有人可写，但设置了 Sticky Bit，
# 所以用户 A 在 /tmp 下创建的文件，用户 B 不能删除

# 设置
sudo chmod +t dir            # 符号法
sudo chmod 1777 dir          # 数字法（前面加 1）
```

#### 6.4 特殊权限位总结

| 权限 | 数字 | 符号 | 显示 | 作用 |
| --- | --- | --- | --- | --- |
| SUID | 4000 | `u+s` | `rwsr-xr-x` | 文件以所有者身份执行 |
| SGID | 2000 | `g+s` | `rwxr-sr-x` | 文件以组身份执行 / 目录下文件继承组 |
| Sticky | 1000 | `+t` | `rwxrwxrwt` | 目录下文件仅所有者可删 |

> 大写 S（如 `rwSr-xr-x`）表示有 SUID 但无执行权限（通常无意义）；小写 s（`rwsr-xr-x`）表示有 SUID 且有执行权限。

### 7. umask 默认权限掩码

umask 决定新建文件和目录的默认权限：

```bash
umask                       # 查看当前 umask（如 022）
umask 022                   # 设置 umask

# 计算方式：
# 目录默认权限 = 777 - umask
# 文件默认权限 = 666 - umask（文件默认无执行权限）

# umask 022:
#   新目录 = 777 - 022 = 755 (rwxr-xr-x)
#   新文件 = 666 - 022 = 644 (rw-r--r--)

# umask 077:
#   新目录 = 777 - 077 = 700 (rwx------)
#   新文件 = 666 - 077 = 600 (rw-------)

# umask 000:
#   新目录 = 777 - 000 = 777 (rwxrwxrwx)
#   新文件 = 666 - 000 = 666 (rw-rw-rw-)
```

| umask | 新文件 | 新目录 | 适用场景 |
| --- | --- | --- | --- |
| 022 | 644 | 755 | 默认（共享） |
| 077 | 600 | 700 | 高安全（私密） |
| 002 | 664 | 775 | 团队协作（同组可写） |
| 000 | 666 | 777 | 全开（危险） |

永久设置 umask：在 `~/.bashrc` 或 `/etc/profile` 中添加 `umask 022`。

### 8. ACL 访问控制列表

传统权限只能对"所有者/组/其他"三组设置权限，ACL 可以对**任意指定用户或组**设置权限，更细粒度。

#### 8.1 setfacl - 设置 ACL

```bash
# 给指定用户设置权限
sudo setfacl -m u:deploy:rwx file         # 给 deploy 用户 rwx 权限
sudo setfacl -m u:alice:rw file           # 给 alice 用户 rw 权限
sudo setfacl -m g:developers:rx file      # 给 developers 组 rx 权限

# 递归设置
sudo setfacl -R -m u:deploy:rwx dir/

# 设置默认 ACL（目录下新建文件自动继承）
sudo setfacl -d -m u:deploy:rwx dir/

# 移除 ACL
sudo setfacl -x u:alice file              # 移除 alice 的 ACL
sudo setfacl -x g:developers file         # 移除组的 ACL
sudo setfacl -b file                      # 清除所有 ACL
sudo setfacl -bR dir/                     # 递归清除
```

#### 8.2 getfacl - 查看 ACL

```bash
getfacl file
# # file: file
# # owner: deploy
# # group: deploy
# user::rw-
# user:deploy:rwx           ← ACL 条目
# user:alice:rw-            ← ACL 条目
# group::r--
# mask::rwx                 ← ACL 有效权限掩码
# other::r--

getfacl dir/
```

#### 8.3 ACL vs 传统权限

| 维度 | 传统权限 | ACL |
| --- | --- | --- |
| 粒度 | 三组（所有者/组/其他） | 任意用户/组 |
| 设置 | `chmod` | `setfacl` |
| 查看 | `ls -l` | `getfacl` |
| 复杂度 | 简单 | 较复杂 |
| 适用场景 | 普通文件 | 需要给特定用户额外权限 |

**示例场景**：文件所有者是 deploy，但需要让 www-data 也能读写，传统权限做不到（除非改组），ACL 可以：

```bash
sudo setfacl -m u:www-data:rw /opt/ecommerce/config/app.env
getfacl /opt/ecommerce/config/app.env
```

> `ls -l` 显示带 ACL 的文件时，权限后会加 `+`：`-rw-rw-r--+`。

### 9. SSH 密钥认证

#### 9.1 ssh-keygen - 生成密钥对

```bash
# 生成 ed25519 密钥（推荐，更安全更快）
ssh-keygen -t ed25519 -C "deploy@ecommerce"

# 生成 RSA 密钥（兼容性最好，4096 位）
ssh-keygen -t rsa -b 4096 -C "deploy@ecommerce"

# 指定密钥文件路径
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_github -C "github"

# 不设置密码（自动化场景，但有安全风险）
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
```

生成后会产生两个文件：
- `~/.ssh/id_ed25519`：私钥（**必须保密**，权限 600）
- `~/.ssh/id_ed25519.pub`：公钥（可公开，传到远程服务器）

#### 9.2 ssh-copy-id - 安装公钥

```bash
# 自动把公钥传到远程服务器的 ~/.ssh/authorized_keys
ssh-copy-id deploy@192.168.1.100
ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@192.168.1.100
ssh-copy-id -p 2222 deploy@192.168.1.100

# 手动安装（如 ssh-copy-id 不可用）
cat ~/.ssh/id_ed25519.pub | ssh deploy@192.168.1.100 \
    "mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
     cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

#### 9.3 authorized_keys 文件

远程服务器的 `~/.ssh/authorized_keys` 文件存储允许登录的公钥列表，每行一个公钥：

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... deploy@ecommerce
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... alice@laptop
```

**权限要求**（不对会拒绝登录）：

```
~/.ssh/                   700
~/.ssh/authorized_keys    600
~/.ssh/id_*              600（私钥）
~/.ssh/id_*.pub          644（公钥）
```

#### 9.4 禁用密码登录

修改 `/etc/ssh/sshd_config` 提高安全性：

```bash
sudo vim /etc/ssh/sshd_config

# 关键配置
Port 22                           # 可改为非标准端口
PermitRootLogin no                # 禁止 root 直接登录
PasswordAuthentication no         # 禁用密码登录（仅密钥）
PubkeyAuthentication yes          # 启用密钥认证
MaxAuthTries 3                    # 最大认证尝试次数
AllowUsers deploy                 # 仅允许 deploy 登录（白名单）
# AllowGroups sudo                # 或按组允许

# 修改后重启 SSH 服务
sudo systemctl restart sshd       # Ubuntu
sudo systemctl restart ssh        # 部分 Ubuntu 版本

# ⚠️ 修改前保持当前 SSH 会话不断开，另开一个终端测试新配置能否登录！
# 否则可能把自己锁在外面
```

## 关键知识点总结

### 用户管理命令速查

| 命令 | 作用 | 示例 |
| --- | --- | --- |
| `useradd -m -s /bin/bash user` | 创建用户 | `sudo useradd -m deploy` |
| `usermod -aG group user` | 追加到附加组 | `sudo usermod -aG sudo deploy` |
| `userdel -r user` | 删除用户及家目录 | `sudo userdel -r deploy` |
| `passwd user` | 设置密码 | `sudo passwd deploy` |
| `passwd -l user` | 锁定账户 | `sudo passwd -l deploy` |
| `id user` | 查看用户信息 | `id deploy` |
| `groupadd group` | 创建组 | `sudo groupadd developers` |
| `gpasswd -a user group` | 添加到组 | `sudo gpasswd -a deploy developers` |
| `su - user` | 切换用户 | `su - deploy` |
| `sudo command` | 临时提权 | `sudo apt update` |
| `visudo` | 编辑 sudoers | `sudo visudo` |

### 权限数字速查表

```
权限          数字  含义          常用场景
---           0    无权限
--x           1    仅执行
-w-           2    仅写
-wx           3    写+执行
r--           4    仅读
r-x           5    读+执行       目录/可执行文件
rw-           6    读+写         普通文件
rwx           7    读+写+执行

常用组合：
755  rwxr-xr-x   目录/脚本（所有者全，其他读+执行）
644  rw-r--r--   普通文件（所有者读写，其他只读）
600  rw-------   私密文件（SSH 私钥）
700  rwx------   私密目录（~/.ssh）
777  rwxrwxrwx   全开（危险！仅临时调试）
```

### 特殊权限说明表

| 权限 | 数字 | 显示 | 作用 | 典型应用 |
| --- | --- | --- | --- | --- |
| SUID | 4000 | `rwsr-xr-x` | 以所有者身份执行 | `/usr/bin/passwd` |
| SGID | 2000 | `rwxr-sr-x` | 继承目录组 | 共享目录 |
| Sticky | 1000 | `rwxrwxrwt` | 仅所有者可删 | `/tmp` |

### sudoers 语法表

| 语法 | 含义 |
| --- | --- |
| `user ALL=(ALL) ALL` | 用户可执行所有命令（需密码） |
| `user ALL=(ALL) NOPASSWD: ALL` | 用户可执行所有命令（免密） |
| `%group ALL=(ALL) ALL` | 组成员可执行所有命令 |
| `user ALL=(root) /usr/bin/systemctl restart nginx` | 仅允许重启 nginx |
| `user ALL=(www-data) /usr/bin/node /opt/app.js` | 以 www-data 身份运行 node |

### 用户配置文件速查

| 文件 | 作用 | 关键字段 |
| --- | --- | --- |
| `/etc/passwd` | 用户信息 | 用户名:x:UID:GID:描述:家目录:Shell |
| `/etc/shadow` | 密码哈希 | 用户名:$6$哈希:修改日期:... |
| `/etc/group` | 组信息 | 组名:x:GID:成员列表 |
| `/etc/gshadow` | 组密码 | （很少使用） |

## 代码文件说明

| 文件 | 用途 | 执行方式 |
| --- | --- | --- |
| `Code/01-user-group-management.sh` | 用户与组管理演示：创建 deploy 用户、加入 sudo 组、创建系统用户、id/who/last 查看 | `sudo bash 01-user-group-management.sh` |
| `Code/02-permission-management.sh` | 权限管理演示：chmod/chown、SUID/SGID/Sticky、umask、ACL，在 /opt/ecommerce/ 下设置项目权限 | `sudo bash 02-permission-management.sh` |
| `Code/03-ssh-key-auth.sh` | SSH 密钥认证配置：生成密钥对、配置 authorized_keys、修改 sshd_config 禁用密码登录、验证步骤 | `bash 03-ssh-key-auth.sh`（部分步骤需 sudo） |

## 实战练习

### 练习一：创建电商项目用户体系

按项目规划创建用户与组（需 sudo）：

1. 创建 deploy 用户（部署用户，加入 sudo 组）：
   ```bash
   sudo useradd -m -s /bin/bash -c "Deploy User" deploy
   sudo passwd deploy
   sudo usermod -aG sudo deploy
   ```
2. 创建 developers 组，把 deploy 加入：
   ```bash
   sudo groupadd developers
   sudo gpasswd -a deploy developers
   ```
3. 验证：`id deploy`、`groups deploy`
4. 用 `su - deploy` 切换用户，执行 `whoami`、`id`、`pwd` 验证
5. 配置 sudo 免密：`sudo visudo -f /etc/sudoers.d/deploy`，添加 `deploy ALL=(ALL) NOPASSWD: ALL`
6. 查看 `/etc/passwd` 中 deploy 的行：`getent passwd deploy`
7. 查看登录历史：`last deploy | head`

### 练习二：设置项目目录权限

在 `/opt/ecommerce/` 下设置安全的权限（需 sudo）：

1. 设置所有者为 deploy，组为 developers：
   ```bash
   sudo chown -R deploy:developers /opt/ecommerce/
   ```
2. 设置目录权限 755，文件权限 644：
   ```bash
   sudo find /opt/ecommerce -type d -exec chmod 755 {} \;
   sudo find /opt/ecommerce -type f -exec chmod 644 {} \;
   ```
3. scripts 目录下的脚本设为可执行：
   ```bash
   sudo chmod +x /opt/ecommerce/scripts/*.sh
   ```
4. logs 目录设为组可写（developers 组成员可写日志）：
   ```bash
   sudo chmod 775 /opt/ecommerce/logs
   sudo chmod g+s /opt/ecommerce/logs   # SGID，新建文件继承组
   ```
5. 设置 umask 002（组协作）：
   ```bash
   echo "umask 002" >> ~/.bashrc
   ```
6. 用 ACL 给 www-data 用户读取配置的权限：
   ```bash
   sudo setfacl -m u:www-data:r /opt/ecommerce/backend/config/
   getfacl /opt/ecommerce/backend/config/
   ```
7. 验证：`ls -l /opt/ecommerce/`、`getfacl /opt/ecommerce/logs/`

### 练习三：配置 SSH 免密登录

准备两台 Linux 环境（或云服务器 + 本地）：

1. 在本地生成 ed25519 密钥对：
   ```bash
   ssh-keygen -t ed25519 -C "deploy@local"
   ```
2. 把公钥传到远程服务器：
   ```bash
   ssh-copy-id deploy@192.168.1.100
   ```
3. 配置 `~/.ssh/config` 简化连接：
   ```ssh-config
   Host ecommerce
       HostName 192.168.1.100
       User deploy
       IdentityFile ~/.ssh/id_ed25519
   ```
4. 验证免密登录：`ssh ecommerce`（应无需密码直接登录）
5. 在远程服务器禁用密码登录（⚠️ 先保持当前会话，另开终端测试）：
   ```bash
   sudo vim /etc/ssh/sshd_config
   # PasswordAuthentication no
   # PermitRootLogin no
   sudo systemctl restart sshd
   ```
6. 用密码登录测试应被拒绝：`ssh -o PubkeyAuthentication=no deploy@192.168.1.100`
7. 检查 SSH 登录日志：`sudo tail /var/log/auth.log`
