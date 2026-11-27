# Day09 - 综合实战与部署

> 把前 8 天的能力串成一个**可上线的 AI 全栈应用**：前端 + 后端 + 向量库 + Ollama 模型服务，用 compose 一并编排，并用生产级 Dockerfile 与自检清单保证可靠上线。

---

## 目录

- [核心概念](#核心概念)
- [今日学习目标](#今日学习目标)
- [示例项目演进](#示例项目演进)
- [每日内容详解](#每日内容详解)
- [练习与挑战](#练习与挑战)
- [运行代码](#运行代码)
- [知识点速查](#知识点速查)
- [学习路径总结](#学习路径总结)

---

## 核心概念

- **全栈编排**：前端 + 后端 + 向量库 + Ollama 一次拉起。
- **服务互联**：compose 网络内用服务名互访（OLLAMA_HOST=ollama:11434）。
- **生产 Dockerfile**：多阶段 + 精简 + 非 root + HEALTHCHECK。
- **上线自检**：镜像/安全/持久化/资源/可观测等清单。
- **持久化**：模型与向量数据用卷留存。

---

## 今日学习目标

- 说出一个 AI 全栈应用需要哪几个容器及各自职责
- 看懂并扩展 `docker-compose.yml` 完整编排
- 编写生产级 Dockerfile 的关键要素
- 用自检清单评估一个服务是否能上线

---

## 示例项目演进

主线收官：把 Ollama（Day08）、向量库（RAG）、前后端（业务层）用 compose 组装为完整应用并给生产交付建议。

| 阶段 | Day09 中的体现 |
|------|--------------|
| 架构 | `01_full_stack.py` 服务职责与流转 |
| 编排模板 | `docker-compose.yml` 全栈栈 |
| 生产镜像 | `Dockerfile.prod` |
| 交付检审 | `02_deploy_check.py` 自检清单 |

---

## 每日内容详解

### 01 - 组合架构
讲清 frontend/backend/vectorstore/ollama 的职责、一次请求的流转，以及数据持久化与组合命令。

### docker-compose.yml（全栈模板）
前端 + 后端 + Qdrant + Ollama 的完整编排，含 GPU 与卷、服务名互联。

### Dockerfile.prod
生产镜像：多阶段、非 root、HEALTHCHECK，可直接替换业务构建。

### 02 - 上线自检
逐项 checklist（体积/配置/持久化/网络/安全/资源/可观测/可复现）+ 最佳实践回顾。

---

## 练习与挑战

1. **加数据库**：给栈再加一个 mysql/pg 服务并让 backend 连上。
2. **配健康检查**：为你的服务写一个 HEALTHCHECK。
3. **自审镜像**：用 Check 清单给你的现有服务打分并修复 2 项。
4. **展全栈**：有 Docker 时替换占位镜像，真正 `docker compose up -d` 看整体起来。

---

## 运行代码

```bash
# 离线讲解
python "Day09 - 综合实战与部署/Code/01_full_stack.py"
python "Day09 - 综合实战与部署/Code/02_deploy_check.py"

# 需 Docker 环境
cd "Day09 - 综合实战与部署/Code"
docker compose up -d
docker compose ps
```

> 讲解脚本离线可运行；完整 compose 栈需真实 Docker 环境。

---

## 知识点速查

| 项 | 说明 |
|----|------|
| 全栈服务 | frontend / backend / vectorstore / ollama |
| 互联 | 服务名 + 网络（appnet） |
| 生产镜像 | 多阶段 + slim + 非root + HEALTHCHECK |
| 持久化 | 模型与向量数据用卷 |
| GPU | compose deploy + NVIDIA toolkit |
| 上线自检 | 镜像/配置/安全/持久化/资源/可观测 |

---

## 学习路径总结

从"认识镜像容器仓库"（Day01）、"分层与 Dockerfile"（Day02/04）、"生命周期/网络/Compose/数据卷"（Day03/05/06/07），到"容器化 AI 与 GPU"（Day08）和"全栈上线"（Day09），你已具备把 AI 应用**标准化打包、可复现交付、可靠部署**的能力。后续可延伸 Kubernetes 集群编排、CI/CD 流水线与微服务治理。