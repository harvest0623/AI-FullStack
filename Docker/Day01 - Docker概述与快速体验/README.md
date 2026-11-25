# Day01 - Docker概述与快速体验

> 从一个"跑 hello-world"的简单动作切入，理解 Docker 解决了什么问题、它的三大核心概念（镜像/容器/仓库）和整体架构，为后续深入了解打好地基。

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

- **镜像 Image**：只读模板，内含应用 + 运行环境 + 依赖。
- **容器 Container**：镜像的运行实例，有独立可写层，互相隔离。
- **仓库 Repository**：存放/分发镜像的地方（Docker Hub）。
- **架构**：`Client`（docker 命令）→ `Daemon`（守护进程，真正干活）→ `Registry`（镜像仓库）。
- **hello-world**：第一个演示镜像，跑通即说明 Docker 环境就绪。

---

## 今日学习目标

- 说清 Docker 解决的核心问题：环境不一致、部署繁琐
- 区分镜像 / 容器 / 仓库三要素
- 画出 Docker 的 Client/Daemon/Registry 架构
- 讲清 `docker run hello-world` 的执行流程
- 检查本机 Docker 环境是否就绪

---

## 示例项目演进

主线：**把 Ollama 模型服务 + Web 后端 + 向量库打包上线**。今天先用 hello-world 打通环境，理解基础，之后每天往这条主线上加一块能力。

| 阶段 | Day01 中的体现 |
|------|--------------|
| 理解原理 | 三要素、架构、VM vs 容器 |
| 打通环境 | `docker_check.py` 检测与 hello-world 流程 |
| 确立主线 | 明确要打包的 AI 应用场景 |

---

## 每日内容详解

### 01 - 什么是 Docker
讲清三要素与整体架构，帮你建立"镜像→容器→仓库"的模型。

### 02 - 虚拟机 vs 容器
用对比理解容器为何"轻量、秒级、共享内核"，以及相对虚拟机的取舍。

### 03 - Hello World 全流程
拆解 `docker run hello-world` 的每一步内部动作，并提示真实命令。

### docker_check.py
一个可复用的环境检测脚本：判断 CLI / Daemon 是否就绪，供各天讲解脚本共用。

---

## 练习与挑战

1. **画架构图**：不看笔记，自己画出 Client/Daemon/Registry 和容器运行关系。
2. **三要素造句**：用自己的话给"镜像/容器/仓库"各写一个比喻。
3. **装 Docker**：安装 Docker Desktop（或 Linux 脚本）并跑通 `docker run hello-world`。
4. **真机对照**：装好后重跑 `03_hello_world.py`，看它如何检测到你环境就绪。

---

## 运行代码

```bash
python "Day01 - Docker概述与快速体验/Code/01_what_is_docker.py"
python "Day01 - Docker概述与快速体验/Code/02_vm_vs_container.py"
python "Day01 - Docker概述与快速体验/Code/03_hello_world.py"
python "Day01 - Docker概述与快速体验/Code/docker_check.py"
```

> 讲解脚本离线可运行，无需 Docker；装好 Docker 后 `03` 与 `docker_check` 会检测到真实环境。

---

## 知识点速查

| 项 | 说明 |
|----|------|
| 镜像 | 只读模板：应用+环境+依赖 |
| 容器 | 镜像的运行实例，可写、可隔离 |
| D仓库 | 存镜像处，如 Docker Hub |
| 架构 | Client → Daemon → Registry |
| hello-world | 验证 Docker 就绪的最小镜像 |
| 关键命令 | `docker run`、`docker ps`、`docker images` |