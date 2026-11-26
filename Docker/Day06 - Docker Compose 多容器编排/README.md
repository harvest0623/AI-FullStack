# Day06 - Docker Compose 多容器编排

> 单个 `docker run` 管不了"多个互相依赖的服务"。**Docker Compose** 用一份 YAML 把多容器应用一次性编排起来：一条命令拉起前端、后端、数据库、Ollama 模型服务等整个栈。

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

- **Compose**：用 `docker-compose.yml` 声明多个服务，一键编排运行。
- **services**：一个服务 ≈ 一个容器。
- **ports / environment / volumes / networks**：端口、环境变量、数据卷、网络的可声明配置。
- **depends_on**：服务启动依赖顺序。
- **服务名做 DNS**：同网络内用服务名互相访问。

---

## 今日学习目标

- 读懂并写出一个 `docker-compose.yml`
- 理解 services / ports / env / networks / volumes 子块
- 掌握 up/ps/logs/exec/stop/down 等组合命令
- 理解为何 AI 全栈应用适合用 Compose 编排

---

## 示例项目演进

主线迎来关键一步：用 Compose 把 **Web 前端 + 后端 + 数据库** 编排成一台"开箱即用的应用"，Day08/09 会在这个模式上加入 Ollama 模型服务与向量库。

| 阶段 | Day06 中的体现 |
|------|--------------|
| 概念 | `01_compose_intro.py` Compose vs run |
| 多服务 | `docker-compose.yml` web+db 示例 |
| 命令 | `03_compose_cmd.py` 组合命令 |

---

## 每日内容详解

### 01 - Compose 是什么
对比"逐条 docker run"与"一份 YAML + up"，并讲清 YAML 的主要子块。

### docker-compose.yml（示例）
一个 web + db 的完整编排，含端口映射、环境变量、依赖、数据卷、网络。

### 02 - 多服务与伸缩
解读示例中服务如何互联、依赖与数据卷如何配置。

### 03 - Compose 命令
up/ps/logs/exec/stop/down，以及 down 是否删数据。

---

## 练习与挑战

1. **改端口**：把 web 对外端口改成 9090，思考容器内端口要不要动。
2. **加服务**：给栈加一个 redis 服务，让 web 通过 name 访问。
3. **生命周期**：跑一遍 up → ps → logs → down，观察数据卷是否保留。
4. **真机验证**：有 Docker 时在 Code 目录执行 `docker compose up -d`。

---

## 运行代码

```bash
# 离线讲解
python "Day06 - Docker Compose 多容器编排/Code/01_compose_intro.py"
python "Day06 - Docker Compose 多容器编排/Code/02_services_scale.py"
python "Day06 - Docker Compose 多容器编排/Code/03_compose_cmd.py"

# 需 Docker 环境
cd "Day06 - Docker Compose 多容器编排/Code"
docker compose up -d
docker compose ps
docker compose down
```

> 讲解脚本离线可运行；compose 需真实 Docker 环境执行。

---

## 知识点速查

| 命令 | 作用 |
|------|------|
| `docker compose up -d` | 后台启动服务栈 |
| `docker compose ps` | 查看状态 |
| `docker compose logs -f` | 跟踪日志 |
| `docker compose exec X bash` | 进入服务容器 |
| `docker compose stop` | 停止 |
| `docker compose down` | 移除容器/网络（保留卷） |
| `docker compose down -v` | 带上数据卷一起删 |

| compose 子块 | 作用 |
|------|------|
| services | 定义各服务 |
| ports | 端口映射 |
| environment | 环境变量 |
| depends_on | 依赖顺序 |
| volumes / networks | 卷与网络 |