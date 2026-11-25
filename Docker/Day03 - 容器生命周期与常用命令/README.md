# Day03 - 容器生命周期与常用命令

> 学会让容器"生、活、停、删"：理解容器的生命周期状态机，掌握 `run / ps / stop / start / restart / rm / exec / logs / cp` 这些最常用命令。

---

## 目录

- [核心概念](#核心概念)
- [今日学习目标](#今日学习目标)
- [示例项目演进](#示例项目演进)
- [每日内容详解](#每日内容详解)
- [练习与挑战](#练习与挑战)
- [运行代码](#运行代码)
- [知识点速查](#知识点速查)

---

## 核心概念

- **生命周期状态**：created → running ⇄ paused → exited → removed。
- **前台 vs 后台**：`-d` 后台运行，`-it` 交互式。
- **命名容器**：`--name` 让你用名字而不是随机 ID。
- **exec**：进入运行中的容器执行命令。
- **logs**：查看容器输出日志。
- **cp**：容器与宿主机拷贝文件。

---

## 今日学习目标

- 画出容器生命周期状态机
- 熟练 run/ps/stop/start/restart/rm 及常用参数
- 会用 exec 进入容器、logs 查看日志
- 理解容器"退出≠删除"，数据层需 rm 清理

---

## 示例项目演进

主线：今天掌握容器的"起停删查进入日志"，这是在 Day09 部署 AI 服务时管理容器实例的必备技能。

| 阶段 | Day03 中的体现 |
|------|--------------|
| 理解状态 | `01_lifecycle.py` 状态机模拟 |
| 常用命令 | `02_cmd_demo.py` 命令与参数 |
| 进入/日志 | `03_exec_logs.py` exec/logs/cp |

---

## 每日内容详解

### 01 - 生命周期状态机
用类模拟容器状态变迁，逐个触发 start/stop/restart/rm，直观看到状态流转。

### 02 - 常用命令
问答式速览 run/ps/stop/start/restart/rm 及其常见参数（-d/-it/--name/-p）。

### 03 - 进入与日志
讲清 exec/logs/cp 三个管理能力及各自典型场景。

---

## 练习与挑战

1. **背状态**：不看书写出容器的 4-5 个状态和它们之间的切换命令。
2. **背参数**：说出 `-d / -it / --name / -p` 各自作用。
3. **真机实操**：有 Docker 时 `docker run -d --name web nginx`，然后 ps/logs/exec 走一遍。

---

## 运行代码

```bash
python "Day03 - 容器生命周期与常用命令/Code/01_lifecycle.py"
python "Day03 - 容器生命周期与常用命令/Code/02_cmd_demo.py"
python "Day03 - 容器生命周期与常用命令/Code/03_exec_logs.py"
```

> 讲解脚本离线可运行；有 Docker 时 `03` 会提示真实命令供对照执行。

---

## 知识点速查

| 命令 | 作用 |
|------|------|
| `docker run -d -it --name X img` | 创建并运行容器 |
| `docker ps / ps -a` | 列运行中 / 全部容器 |
| `docker stop X` | 停止容器 |
| `docker start X` | 启动已停止容器 |
| `docker rm X` | 删除已停止容器 |
| `docker exec -it X bash` | 进入容器 |
| `docker logs [-f] X` | 查看日志 |
| `docker cp 源 目标` | 拷贝文件 |