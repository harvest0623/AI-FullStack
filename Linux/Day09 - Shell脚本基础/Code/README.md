# Day09 - Shell 脚本基础 · 代码说明

本目录包含 Day09 所有 Shell 脚本，可在 Ubuntu 22.04+ 直接执行。

## 环境准备

```bash
# 查看当前 Shell
echo $SHELL           # 应为 /bin/bash

# 确认 bash 版本
bash --version

# 进入脚本目录
cd /path/to/Day09/Code
```

> 所有脚本默认以 `#!/bin/bash` 开头，使用 bash 4+ 特性（关联数组需 bash 4+）。
> Ubuntu 22.04 默认 bash 5.1，完全满足。

## 脚本列表

| 文件 | 用途 | 是否需要参数 |
| --- | --- | --- |
| `01-hello-shell.sh` | 第一个 Shell 脚本：echo、注释、变量、执行方式 | 否 |
| `02-variables.sh` | 变量练习：自定义/环境变量、位置参数、特殊变量 | 推荐传 3 个参数 |
| `03-string-array.sh` | 字符串与数组：截取/替换/删除/大小写、普通/关联数组 | 否 |
| `04-arithmetic-read.sh` | 算术运算、read 输入、printf 格式化输出 | 否 |

## 执行方式

```bash
# 方式一：bash 执行（无需可执行权限，调试推荐）
bash 01-hello-shell.sh

# 方式二：赋予执行权限后直接运行
chmod +x *.sh
./01-hello-shell.sh

# 方式三：source 执行（在当前 Shell 中执行，影响当前环境）
# 注意：source 会让脚本里的变量/函数留在当前 Shell，一般仅用于加载配置
source 02-variables.sh
echo $APP_NAME      # 若 source 执行，能拿到脚本里的 export 变量
```

## 带参数执行示例

```bash
# 02-variables.sh 推荐传 3 个参数演示位置参数
bash 02-variables.sh nginx mysql redis

# 也可传入含空格的参数对比 $@ vs $*
bash 02-variables.sh "web server" mysql redis
```

## 常见问题

### 1. 执行报错 `command not found: name`

变量赋值时等号两边带了空格：

```bash
# 错误：name = "value"（被当成执行命令 name）
# 正确：name="value"（等号两边紧贴）
```

### 2. 关联数组报错

关联数组需要 `declare -A` 先声明，且需要 bash 4+：

```bash
declare -A map       # 必须先声明
map["key"]="value"
```

### 3. 脚本在 Windows 编辑后执行报错 `\r`

Windows 换行符 CRLF 与 Linux LF 不兼容：

```bash
sudo apt install dos2unix -y
dos2unix *.sh
```

或在 VS Code 右下角把 CRLF 切换为 LF。

### 4. `source` 执行后变量消失

`source` 必须在**当前 Shell**执行，若用 `bash` 执行则变量在子 Shell 中，执行完即消失。

## 学习建议

1. 先通读 Day09 根目录的 README.md 理解概念
2. 逐个执行脚本，观察输出
3. 修改脚本里的变量值，重新执行，观察变化
4. 故意制造错误（删引号、加空格），观察报错信息
5. 完成 README 末尾的实战练习
