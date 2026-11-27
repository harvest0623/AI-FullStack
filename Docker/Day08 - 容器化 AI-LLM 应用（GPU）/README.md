# Day08 - 容器化 AI/LLM 应用（GPU）

> 把之前学的所有能力用在 AI 场景：把 **Ollama / Python 推理服务** 打包成容器、模型用卷挂载、传 GPU 给容器、设资源上限。

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

- **模型用卷挂载**：模型几个 GB 不进镜像，用 `-v models:/models`，镜像小、可换模型。
- **依赖层缓存**：`pip` 在前、代码在后。
- **环境变量传参**：模型路径/端口用 ENV 配置。
- **GPU 传递**：`--gpus all` / compose `deploy.gpus`（需 NVIDIA Container Toolkit）。
- **资源限制**：`--memory` / `--cpus` 防止容器吃光主机。

---

## 今日学习目标

- 说清"模型为何用卷挂载而非打入镜像"
- 把一个 Python 推理服务容器化
- 在 compose 里给 Ollama 配置 GPU
- 掌握 GPU 传递与资源限制命令

---

## 示例项目演进

主线进入 AI 战场：今天把 **Ollama 模型服务**容器化并接入 GPU。这是 Day09 全栈（前端+后端+向量库+Ollama）的最后一环。

| 阶段 | Day08 中的体现 |
|------|--------------|
| 服务封装 | `01_package_service.py` + `Dockerfile.service` |
| GPU 容器 | `02_gpu.py` + `docker-compose.gpu.yml` |

---

## 每日内容详解

### 01 - 打包 AI 服务
讲清模型放卷、依赖层缓存、配置环境变量、暴露端口四大决策。

### Dockerfile.service
封装自定义 Python 推理服务的模板（含非 root 运行）。

### 02 - GPU 与资源
检测宿主机 GPU、讲 `--gpus`/compose gpu 传递、以及内存/CPU 资源限制。

### docker-compose.gpu.yml
官方 Ollama 镜像 + 模型卷 + GPU 声明的组合示例。

---

## 练习与挑战

1. **对比**：为什么模型用卷挂载比打进镜像更合理？
2. **加限制**：给 Ollama 服务加 `--memory 12g --cpus 8`。
3. **GPU 验证**：有 GPU + toolkit 时 `docker run --gpus all ollama/ollama` 跑起来。
4. **自封装**：把你写过的任意推理脚本用 `Dockerfile.service` 模板封装。

---

## 运行代码

```bash
# 离线讲解
python "Day08 - 容器化 AI-LLM 应用（GPU）/Code/01_package_service.py"
python "Day08 - 容器化 AI-LLM 应用（GPU）/Code/02_gpu.py"

# 需 Docker + GPU toolkit
cd "Day08 - 容器化 AI-LLM 应用（GPU）/Code"
docker compose -f docker-compose.gpu.yml up -d
curl http://127.0.0.1:11434
```

> 讲解脚本离线可运行；Ollama 容器的真正运行需 Docker 环境。

---

## 知识点速查

| 项 | 说明 |
|----|------|
| 模型挂载 | `-v models:/models`，不进镜像 |
| GPU | `--gpus all` 或 deploy.gpus |
| 资源限制 | `--memory 4g --cpus 2` |
| Ollama 镜像 | `ollama/ollama`，API 端口 11434 |
| 模型卷 | `ollama_models:/root/.ollama` |
| 依赖缓存 | pip 在前、代码在后 |