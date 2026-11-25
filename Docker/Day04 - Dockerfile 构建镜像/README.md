# Day04 - Dockerfile 构建镜像

> 前三天我们用现成镜像。今天学**写 Dockerfile 构建自己的镜像**：掌握常用指令、构建缓存、多阶段构建与镜像瘦身。这是把 Ollama / Web 服务 / AI 应用打包的基础。

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

- **Dockerfile**：定义如何一步步构建镜像的脚本，每条指令生成一层。
- **常用指令**：`FROM / RUN / COPY / CMD / ENTRYPOINT / ENV / EXPOSE / WORKDIR`。
- **构建触法**：`docker build -t name:tag .`。
- **.dockerignore**：排除不需要进镜像的文件。
- **多阶段构建**：(builder)跑编译出产物 → (runtime)只复制产物，镜像更小。
- **构建缓存**：指令未变则复用层，见 Day02。

---

## 今日学习目标

- 读懂并写出一个基本 Dockerfile
- 理解每条指令生成一个镜像层
- 用多阶段构建显著缩小镜像体积
- 配置 `CMD` vs `ENTRYPOINT` 的区别与配合
- 知道构建缓存与 `.dockerignore` 的最佳实践

---

## 示例项目演进

主线：今天先把"Python Web/AI 服务"的 Dockerfile 写对，这是 Day08 打包 Ollama/推理服务、Day09 全栈上线的基础。

| 阶段 | Day04 中的体现 |
|------|--------------|
| 学指令 | `01_dockerfile_guide.py` 指令逐条讲解 |
| 实构建 | `Dockerfile` 可直接构建的示例 |
| 瘦镜像 | `02_multistage.py` 多阶段原理 |

---

## 每日内容详解

### 01 - Dockerfile 指令
逐条解释 FROM/RUN/COPY/CMD/ENTRYPOINT/ENV/EXPOSE/WORKDIR，并说明指令顺序与层缓存的关系。

### Dockerfile（示例）
一个可直接构建的 Python Web 镜像，依赖靠前、代码靠后，含注释。

### 02 - 多阶段构建
讲解"builder（装编译环境出产物）→ runtime（只保留产物）"如何让镜像从 GB 级缩到几百 MB。

### 03 - build 流程
用脚本走一遍 `docker build` 的完整流程，并说明 .dockerignore / 缓存 / tag 的运用。

---

## 练习与挑战

1. **改顺序**：把 Dockerfile 的 COPY 提前到 RUN pip 之前，看缓存命中率变化。
2. **多阶段**：用多阶段构建一个含编译步骤的服务，对比体积。
3. **写 .dockerignore**：为你的项目写一份，排除 venv/.git/node_modules 等。
4. **CMD vs ENTRYPOINT**：写出"默认参数用 CMD、固定可执行用 ENTRYPOINT"的组合。

---

## 运行代码

```bash
# 离线讲解（无需 Docker）
python "Day04 - Dockerfile 构建镜像/Code/01_dockerfile_guide.py"
python "Day04 - Dockerfile 构建镜像/Code/02_multistage.py"
python "Day04 - Dockerfile 构建镜像/Code/03_build_demo.py"

# 需要 Docker 环境（构建示例镜像）
cd "Day04 - Dockerfile 构建镜像/Code"
docker build -t myweb:1.0 .
docker run --rm myweb
```

---

## 知识点速查

| 指令 | 作用 |
|------|------|
| FROM | 指定基础镜像 |
| RUN | 构建时执行命令（生成层） |
| COPY / ADD | 复制文件进镜像 |
| CMD | 默认启动命令（可被覆盖） |
| ENTRYPOINT | 固定的启动程序 |
| ENV | 环境变量 |
| EXPOSE | 声明端口 |
| WORKDIR | 设置工作目录 |

| build 流程 | `docker build -t name:tag .` |
| 瘦身 | 多阶段 + 尽量小基础镜像 |
| 排除 | `.dockerignore` |