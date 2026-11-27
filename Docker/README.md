# Docker 学习指南

> 系统化掌握 Docker：从镜像与容器基础、镜像分层、容器生命周期、Dockerfile 构建、网络与端口、Compose 多容器编排、数据持久化，到容器化 AI/LLM 应用（GPU 支持）与生产部署，构建可移植、可复现、易上线的现代化应用交付能力

> 共 9 天，聚焦 Docker 本身的原理与工程实践，是 AI-FullStack 应用的"打包与部署"层

---

## 目录

- [板块定位](#板块定位)
- [前置要求](#前置要求)
- [为什么用 Docker](#为什么用-docker)
- [学习路线图](#学习路线图)
- [每日内容详表](#每日内容详表)
- [目录结构](#目录结构)
- [学习建议](#学习建议)
- [如何运行代码](#如何运行代码)
- [知识点速查](#知识点速查)
- [后续板块](#后续板块)

---

## 板块定位

**Docker** 是一个容器化平台，它把"应用 + 运行环境 + 依赖"一起打包成**镜像**，在任何装有 Docker 的机器上都能以**容器**形式一键运行，实现"一次构建，到处运行"。

**与 AI-FullStack 其他板块的关系**：
- 前面模块（Python / LLM / LangChain / RAG / Agent / Ollama）解决了"代码与模型怎么组织、怎么调"；
- **本板块解决"写好的东西怎么装进一个标准化的盒子，稳定分发、部署、上线"**。
- 尤其是 **Ollama / 推理服务 / Web 后端**，用 Docker 打包后即可在开发机、测试机、云服务器（含 GPU 机）上无差异运行。

**学习目标**：完成本板块后，你应能：
- 讲清镜像、容器、仓库、数据卷、网络等核心概念
- 理解镜像分层与联合文件系统的原理
- 掌握容器的创建、运行、停止、查看、进入、日志等生命周期操作
- 编写 Dockerfile 构建自定义镜像，使用多阶段构建
- 配置网络的端口映射与多容器互联
- 用 Docker Compose 编排多容器应用
- 用数据卷与绑定挂载实现持久化
- 将 AI / LLM 应用（含 GPU 支持）容器化
- 交付一个完整的 docker-compose 服务栈并上线

**设计原则**：
- 知识点梳理为主，每天独立成章，含理论 + 可执行 Python 讲解脚本 + 可直接套用的 Dockerfile/compose 模板
- **代码优先兼容离线运行**：本机未装 Docker 时，讲解脚本自动讲解概念与命令（不真执行）；检测到 Docker 环境时给出真实命令提示，便于对照。
- 紧扣 Docker 本身，逐层深入，最后结合 AI 场景综合实战

---

## 前置要求

| 能力 | 要求 | 说明 |
|------|------|------|
| 命令行 | 必须 | 终端基本操作、`cd` / 环境变量 |
| Python | 了解 | 讲解脚本均为 Python，用于离线演示概念 |
| 网络基础 | 了解 | 端口、IP、DNS（对网络章节有助） |
| AI 基础 | 了解 | Ollama / Web 服务概念（对 Day08-09 有助） |

**环境准备**（建议，但不是运行本板块代码的强制前提）：
- 安装 Docker：Windows / macOS 装 **Docker Desktop**，Linux 用官方脚本
  - Linux: `curl -fsSL https://get.docker.com | sh`
- 验证：`docker run hello-world`（能正常打印则 Docker 就绪）
- 可选：注册一个 Docker Hub 账号（Day02 推镜像用）
- GPU 场景：Windows 装 NVIDIA Container Toolkit，Linux `nvidia-container-toolkit`

> **重要**：本板块讲解脚本全部**离线可运行**，未装 Docker 也能学完概念。若装了 Docker，可在"真实命令"段落手动对照执行，加深理解。

---

## 为什么用 Docker

| 对比项 | 裸机/手动部署 | Docker |
|--------|-------------|--------|
| 环境一致性 | 依赖手动装 | 镜像自带环境，零差异 ★ |
| 隔离性 | 弱，易冲突 | 进程级隔离 |
| 启动速度 | 慢 | 秒级启动 |
| 可移植性 | 绑主机 | 一次构建到处运行 |
| 资源占用 | 高（虚拟机） | 轻量（共享内核） |
| 回滚 | 靠备份 | 镜像 tag 即版本，一键回退 |

---

## 学习路线图

```
┌──────────────────────────────────────────────────────────────────┐
│           Docker 学习路线（9天，从会跑到能编排上线）              │
└──────────────────────────────────────────────────────────────────┘

阶段一：基础入门（Day01-Day03）
┌──────────┬──────────┬──────────┐
│ Day01    │ Day02    │ Day03    │
│ 概述与   │ 镜像与   │ 容器生命 │
│ 快速体验 │ 分层原理 │ 周期命令 │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     ▼          ▼          ▼
阶段二：构建与编排（Day04-Day06）
┌──────────┬──────────┬──────────┐
│ Day04    │ Day05    │ Day06    │
│ Dockerfile│ 网络与   │ Compose  │
│ 构建镜像 │ 端口     │ 多容器   │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     ▼          ▼          ▼
阶段三：数据与生产（Day07-Day09）
┌──────────┬──────────┬──────────┐
│ Day07    │ Day08    │ Day09    │
│ 数据卷与 │ 容器化AI │ 综合实战 │
│ 持久化   │ /LLM(GPU)│ 与部署   │
└──────────┴──────────┴──────────┘
```

---

## 每日内容详表

### Day01 - Docker概述与快速体验
- **核心**：Docker 是什么、虚拟机 vs 容器、镜像/容器/仓库三要素、架构（Client/Daemon/Registry）、Hello World、常用命令速览
- **代码**：`01_what_is_docker.py`（概念与三要素）/`02_vm_vs_container.py`（容器 vs 虚拟机对比）/`03_hello_world.py`（helloworld 流程讲解）/`docker_check.py`（环境检测）/`README.md`
- **重点**：三要素、架构、能跑通 hello-world

### Day02 - 镜像与分层原理
- **核心**：镜像是什么、分层存储（UnionFS）、只读层 + 容器可写层、层缓存与复用、镜像 tag、从仓库拉取、层为何共享
- **代码**：`01_image_layer.py`（镜像分层模型）/`02_layer_cache.py`（层缓存与复用演示）/`03_tag_pull.py`（tag 与拉取讲解）/`README.md`
- **重点**：分层原理、联合文件系统、层复用

### Day03 - 容器生命周期与常用命令
- **核心**：容器 = 可写层 + 进程、`run/ps/stop/start/restart/rm/exec/logs/cp`、前台/后台、交互式、退出状态、容器命名与启停生命周期
- **代码**：`01_lifecycle.py`（容器生命周期状态机）/`02_cmd_demo.py`（常用命令讲解）/`03_exec_logs.py`（进入与日志）/`README.md`
- **重点**：run 各类参数、生命周期、exec/logs

### Day04 - Dockerfile 构建镜像
- **核心**：Dockerfile 指令（FROM/RUN/COPY/CMD/ENTRYPOINT/ENV/EXPOSE/WORKDIR）、构建缓存顺序、多阶段构建、.dockerignore、体积优化
- **代码**：`01_dockerfile_guide.py`（指令讲解）/`Dockerfile`（可直接构建的示例）/`02_multistage.py`（多阶段构建原理）/`03_build_demo.py`（build 流程讲解）/`README.md`
- **重点**：常用指令、多阶段、构建缓存

### Day05 - 网络与端口
- **核心**：网络模式（bridge/host/none）、端口映射 `-p`、`--network`、容器名称做 DNS、自定义 bridge 网络、容器互联
- **代码**：`01_network_model.py`（网络模式对比）/`02_port_map.py`（端口映射原理）/`03_container_net.py`（自定义网络与互联）/`README.md`
- **重点**：端口映射、bridge、容器互联

### Day06 - Docker Compose 多容器编排
- **核心**：Compose 是什么、docker-compose.yml 结构（services/networks/volumes）、服务依赖 depends_on、启动/停止/日志组合命令、环境变量、与跑单个容器对比
- **代码**：`01_compose_intro.py`（Compose 概念）/`docker-compose.yml`（示例栈: web + db）/`02_services_scale.py`（多服务与伸缩）/`03_compose_cmd.py`（常用命令）/`README.md`
- **重点**：compose 结构、服务编排、组合命令

### Day07 - 数据卷与持久化
- **核心**：容器数据易失、`-v` 绑定挂载、命名卷 vs 匿名卷、持久化策略、权限、备份与恢复、与 AI 模型数据无缝衔接
- **代码**：`01_why_volume.py`（为何需要数据卷）/`02_bind_vs_named.py`（绑定挂载 vs 命名卷）/`03_backup.py`（备份与恢复）/`README.md`
- **重点**：命名卷、绑定挂载、持久化策略

### Day08 - 容器化 AI / LLM 应用（GPU）
- **核心**：把 Ollama / Python 推理服务打包成镜像、模型数据用卷挂载、GPU 支持（NVIDIA Container Toolkit）、资源限制（--memory/--cpus）、环境变量传参
- **代码**：`Dockerfile.ollama`（Ollama 镜像示例）/`docker-compose.gpu.yml`（GPU compose）/`01_package_service.py`（打包推理服务原理）/`02_gpu.py`（GPU 检测与容器化）/`README.md`
- **重点**：模型服务容器化、GPU、资源限制

### Day09 - 综合实战与部署
- **核心**：组装一个完整应用（前端 + 后端 + 向量库 + Ollama 模型服务）、生产最佳实践、镜像瘦身与安全、日志与健康检查、在服务器上线流程、总结与学习路径
- **代码**：`docker-compose.yml`（完整应用栈）/`Dockerfile.prod`（生产镜像）/`01_full_stack.py`（组合架构讲解）/`02_deploy_check.py`（上线自检清单）/`README.md`
- **重点**：整合编排、生产实践

---

## 目录结构

```
Docker/
├── README.md                          ← 本文件（板块总入口）
├── Day01 - Docker概述与快速体验/
│   ├── README.md
│   └── Code/
│       ├── 01_what_is_docker.py
│       ├── 02_vm_vs_container.py
│       ├── 03_hello_world.py
│       ├── docker_check.py
│       └── README.md
├── Day02 - 镜像与分层原理/
│   ├── README.md
│   └── Code/...
├── ...（Day03-Day08 同构）...
└── Day09 - 综合实战与部署/
    ├── README.md
    └── Code/
        ├── 01_full_stack.py
        ├── 02_deploy_check.py
        ├── docker-compose.yml
        ├── Dockerfile.prod
        └── README.md
```

**结构约定**：
- 每个 `DayXX` 文件夹下有**根级** `README.md`（学习文档）
- 代码/模板统一放在 `Code/` 子文件夹内，`.py` 可直接 `python x.py` 运行，`Dockerfile` / `docker-compose.yml` 需在 Docker 环境下使用
- 概念讲解脚本**离线可跑**（不依赖 Docker 环境）

---

## 学习建议

### 推荐学习节奏

| 节奏 | 适合人群 | 每天投入 | 完成周期 |
|------|---------|---------|---------|
| 激进 | 全职学习 | 4-5 小时 | 约 1.5 周 |
| 标准 | 业余学习 | 2 小时 | 约 2-3 周 |
| 保守 | 碎片时间 | 1 小时 | 约 1.5 月 |

### 学习方法论

1. **先装环境**：Day01 装好 Docker Desktop 并跑通 hello-world，所有真实命令都需要它
2. **概念先行**：先跑 Python 讲解脚本理解概念，再手动执行"真实命令"对照
3. **动手为主**：Dockerfile / compose 一定自己写几遍，改一个指令看构建变化
4. **场景驱动**：围绕"把 Ollama 模型服务 + Web 后端 + 向量库打包上线"这一条主线学完 9 天
5. **安全与体积**：多阶段构建、.dockerignore、最小镜像从小就在意

### 阶段性检查点

- **阶段一完成后**：能跑通 hello-world，讲清镜像/容器/仓库区别
- **阶段二完成后**：能编写 Dockerfile 构建并运行自己的镜像
- **阶段三完成后**：能用 compose 编排多容器 + 数据卷，并把 AI 服务容器化（含 GPU）

---

## 如何运行代码

### 环境准备

```bash
# 1. 安装 Docker
# Windows / macOS: 下载 Docker Desktop
# Linux:
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker

# 2. 验证
docker --version
docker run hello-world

# 3.（可选，GPU 用）NVIDIA Container Toolkit
sudo apt-get install nvidia-container-toolkit
```

### 运行示例

```bash
# 离线概念讲解（无需 Docker）
python "Day01 - Docker概述与快速体验/Code/01_what_is_docker.py"

# 需要 Docker 环境的模板（配合讲解脚本学习）
cd "Day04 - Dockerfile 构建镜像/Code"
docker build -t myapp .
docker run --rm myapp

# Compose 编排
cd "Day06 - Docker Compose 多容器编排/Code"
docker compose up -d
docker compose ps
```

> 讲解脚本**无 Docker 也能运行**；Dockerfile / compose 需真实 Docker 环境执行。

---

## 知识点速查

### 核心概念速查

| 概念 | 说明 |
|------|------|
| 镜像 Image | 只读模板，包含应用+环境+依赖 |
| 容器 Container | 镜像的运行实例，有可写层 |
| 仓库 Repository | 存镜像的地方（Docker Hub 等） |
| Dockerfile | 定义如何构建镜像的脚本 |
| 数据卷 Volume | 持久化的外部存储 |
| Compose | 用 YAML 编排多容器 |
| Docker Desktop | Windows/macOS 桌面版 |

### 常用命令速查

| 命令 | 作用 |
|------|------|
| `docker run` | 运行容器 |
| `docker ps / ps -a` | 列出运行中 / 全部容器 |
| `docker stop / start / restart` | 停止 / 启动 / 重启 |
| `docker rm` | 删除容器 |
| `docker images` | 列出镜像 |
| `docker build -t name .` | 构建镜像 |
| `docker exec -it <c> bash` | 进入容器 |
| `docker compose up -d` | 编排启动服务栈 |

### 关键概念速查

| 项 | 说明 |
|----|------|
| 分层存储 | 镜像由只读层叠加，容器加可写层 |
| 绑定挂载 | 主机目录直接映射进容器 |
| 命名卷 | 由 Docker 管理、可持久化的卷 |
| 端口映射 | `-p 主机端口:容器端口` |
| GPU 支持 | NVIDIA Container Toolkit + `--gpus all` |

---

## 后续板块

本板块完成后，可自然衔接：

| 板块 | 与本板块的衔接 |
|------|--------------|
| **部署运维 / K8s** | 单机 Docker → 集群编排 Kubernetes |
| **微服务** | Compose 多容器 → 服务网格 |
| **CI/CD** | 用 Docker 构建/测试/发布流水线 |
| **AI 落地** | 把 Ollama / RAG / Agent 打包上云 |

---

## 学习资源补充

> 遇到疑问时优先查阅官方文档

- [Docker 官方文档](https://docs.docker.com) - 权威参考
- [Docker Hub](https://hub.docker.com) - 镜像仓库
- [Dockerfile 参考](https://docs.docker.com/engine/reference/builder/) - 指令权威参考
- [docker-compose 参考](https://docs.docker.com/compose/) - Compose 文档

---

## 贡献与反馈

本学习手册为原创内容，参考 Docker 官方文档的组织思想但不复制任何内容。如发现错误或有改进建议，欢迎反馈。

**祝学习愉快，让应用随处可跑！**