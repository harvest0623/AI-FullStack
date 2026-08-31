# Day12 - 生产部署与最佳实践

> 从原型到生产是 LangChain 应用的关键跨越：架构设计、性能优化、错误处理、Docker 部署与全面最佳实践

## 本章简介

一个在本地跑通的 Chain，距离"生产可用"还有很长的路要走：它需要清晰的分层架构、缓存与重试机制保障稳定性、成本控制避免预算失控、Docker 容器化便于部署、CI/CD 流水线支撑持续迭代、以及监控告警确保线上可观测。本天作为整个 LangChain 板块的收官，整合 Day01-Day11 所学，把 ChainQA 从原型升级为生产级应用。

我们将设计生产架构（API 层 / Chain 层 / 模型层 / 缓存层 / 监控层），实现缓存与重试机制，生成 Docker 部署配置，并给出涵盖架构、Prompt、错误处理、测试、部署、成本、安全的最佳实践总结，以及 LangChain 版本升级迁移指南。

---

## 学习目标

完成本章后，你应能够：

1. 设计 LangChain 应用的生产分层架构
2. 实现模型缓存（InMemoryCache / SQLiteCache）和语义缓存
3. 使用 `.with_retry()` 配置指数退避重试
4. 使用 `.with_fallbacks()` 实现模型回退降级
5. 生成 Dockerfile（多阶段构建）和 docker-compose.yml
6. 编写 CI/CD Pipeline 配置（自动化测试/灰度/回滚）
7. 用 Pydantic Settings 管理多环境配置
8. 整合 Day01-Day11 所学构建完整 ChainQA 生产级应用
9. 掌握 LangChain 版本升级迁移策略
10. 理解生产环境的最佳实践清单

---

## 理论知识讲解

### 1. LangChain 生产架构设计

#### 分层架构

```
┌─────────────────────────────────────────────┐
│  API 网关层（FastAPI / LangServe）           │  对外暴露 REST API
├─────────────────────────────────────────────┤
│  Chain 层（LCEL 链 / LangGraph）             │  业务逻辑编排
├─────────────────────────────────────────────┤
│  模型层（多模型路由 / 回退）                  │  LLM 调用
├─────────────────────────────────────────────┤
│  缓存层（LLM Cache / 语义缓存）              │  降低成本/延迟
├─────────────────────────────────────────────┤
│  监控层（Callback / LangSmith）              │  可观测性
└─────────────────────────────────────────────┘
```

#### 核心组件职责

| 组件 | 职责 | 关键技术 |
|------|------|---------|
| API 网关层 | 接收请求、鉴权、限流、路由 | FastAPI / LangServe |
| Chain 层 | 编排业务逻辑 | LCEL / LangGraph |
| 模型层 | 调用 LLM、多模型路由 | ChatOpenAI / with_fallbacks |
| 缓存层 | 缓存重复请求结果 | set_llm_cache / SQLiteCache |
| 监控层 | 采集指标、追踪、告警 | Callback / LangSmith |

### 2. 性能优化

#### 模型缓存 `set_llm_cache`

相同输入直接返回缓存结果，跳过 LLM 调用：

```python
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache

# 内存缓存（重启丢失）
set_llm_cache(InMemoryCache())

# SQLite 缓存（持久化）
set_llm_cache(SQLiteCache(database_path="cache.db"))
```

#### 语义缓存

语义相似的输入复用结果（基于 Embedding 相似度）：

```python
from langchain_community.cache import SemanticCache
from langchain_openai import OpenAIEmbeddings

set_llm_cache(SemanticCache(
    embedding=OpenAIEmbeddings(),
    store=...  # 向量存储
))
```

#### 批量处理与异步并发

```python
# 批量调用（并行）
results = chain.batch([{"q": "问题1"}, {"q": "问题2"}])

# 异步并发
results = await chain.abatch([{"q": "问题1"}, {"q": "问题2"}])
```

### 3. 成本控制

| 策略 | 方法 | 效果 |
|------|------|------|
| 模型路由 | 简单任务用 gpt-4o-mini，复杂用 gpt-4o | 降低 80% 成本 |
| Token 优化 | 精简 Prompt、限制输出长度 | 降低 30-50% Token |
| 缓存策略 | LLM 缓存 + 语义缓存 | 重复请求零成本 |
| 成本监控 | Callback 统计 Token 消耗 | 防止预算失控 |

### 4. 错误处理与重试

#### `.with_retry()` 指数退避重试

```python
from langchain_core.runnables import RunnableConfig

model = ChatOpenAI(model="gpt-4o-mini")
# 失败后重试 3 次，指数退避
retry_model = model.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=False,
    retry_if_exception_type=(Exception,),
)
```

#### `.with_fallbacks()` 模型回退

```python
primary = ChatOpenAI(model="gpt-4o")
fallback = ChatOpenAI(model="gpt-4o-mini")  # 大模型故障时降级

# 主模型失败自动切到备用模型
model_with_fallback = primary.with_fallbacks([fallback])
```

#### 超时与熔断

```python
# 超时
model = ChatOpenAI(model="gpt-4o-mini", timeout=30, max_retries=2)

# 熔断：连续失败 N 次暂停一段时间（需自定义实现）
```

### 5. 配置管理

#### Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    cache_type: str = "sqlite"
    max_retries: int = 3
    timeout: int = 30

    class Config:
        env_file = ".env"

settings = Settings()  # 自动从环境变量加载
```

#### 多环境配置

```bash
# .env.dev    开发环境
# .env.test   测试环境
# .env.prod   生产环境
```

### 6. 日志与监控

- **LangSmith 追踪**：配置环境变量自动上报
- **自定义 Callback**：采集延迟/Token/成本/错误率
- **日志持久化**：JSON Lines 格式写入文件
- **告警配置**：错误率超阈值时触发

### 7. Docker 容器化部署

#### Dockerfile 最佳实践

```dockerfile
# 多阶段构建
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .
# 非 root 用户
RUN useradd -m appuser
USER appuser
# 健康检查
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose 多服务

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [redis]
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
```

### 8. CI/CD

| 环节 | 工具 | 内容 |
|------|------|------|
| Prompt 版本管理 | Git | Prompt 模板纳入版本控制 |
| 自动化测试 | pytest | 单元测试 + 集成测试 |
| 灰度发布 | Feature Flag | 小流量验证 |
| 回滚机制 | Docker/K8s | 快速回滚到上一版本 |

### 9. LangChain 版本升级策略

| 迁移路径 | 关键变化 | 注意事项 |
|---------|---------|---------|
| 0.1 → 0.2 | Legacy Chain 废弃 | 用 LCEL 替代 LLMChain |
| 0.2 → 0.3 | 包结构调整 | langchain_community 拆分 |
| Legacy → LCEL | 管道符替代类式 Chain | 重写 Chain 为管道 |

### 10. 最佳实践总结

| 维度 | 最佳实践 |
|------|---------|
| 架构设计 | 分层 / 模块化 / 可测试 |
| Prompt 管理 | 模板化 / 版本管理 / 测试 |
| 错误处理 | 重试 / 回退 / 降级 / 超时 |
| 测试 | 单元测试 / 集成测试 / 回归测试 |
| 部署 | Docker / CI-CD / 监控 |
| 成本控制 | 路由 / 缓存 / Token 优化 |
| 安全 | 输入过滤 / 输出检查 / 密钥管理 |

---

## 代码文件说明

| 文件 | 内容 | 场景 |
|------|------|------|
| `01_production_architecture.py` | 完整生产架构实现（5层） | ProductionChainQA |
| `02_caching_retry.py` | 缓存与重试机制 | CacheRetryManager |
| `03_docker_deploy.py` | Docker 部署配置生成 | DockerDeployGenerator |
| `04_best_practices.py` | 综合最佳实践示例 | ChainQA 生产级应用 |

---

## 关键知识点总结

### 生产架构设计清单

- [ ] API 网关层（FastAPI + 鉴权 + 限流）
- [ ] Chain 层（LCEL / LangGraph 编排）
- [ ] 模型层（多模型路由 + 回退）
- [ ] 缓存层（LLM Cache + 语义缓存）
- [ ] 监控层（Callback + LangSmith）

### 性能优化技巧清单

- [ ] `set_llm_cache` 开启缓存
- [ ] `.batch()` 批量调用
- [ ] `.ainvoke()` 异步并发
- [ ] 模型路由（简单任务用小模型）
- [ ] Prompt 精简（减少 Token）

### 错误处理配置速查

- [ ] `.with_retry(stop_after_attempt=3)`
- [ ] `.with_fallbacks([backup_model])`
- [ ] `timeout=30` 超时配置
- [ ] 工具内部 try/except 返回错误信息

### Docker 部署配置速查

- [ ] 多阶段构建（减小镜像体积）
- [ ] 非 root 用户运行
- [ ] HEALTHCHECK 健康检查
- [ ] .dockerignore 排除无关文件
- [ ] docker-compose 编排多服务

### 最佳实践总结表

见上文"最佳实践总结"小节。

---

## 实战练习

### 练习一：实现生产架构

基于 `01_production_architecture.py`，扩展 ProductionChainQA：
1. 添加限流中间件（每分钟最多 60 次请求）
2. 添加请求日志中间件（记录所有请求的路径、耗时、状态码）
3. 实现模型路由：根据问题长度选择模型（短问题用 mini，长问题用 gpt-4o）

### 练习二：Docker 部署 ChainQA

基于 `03_docker_deploy.py` 生成的配置：
1. 构建并运行 Docker 镜像
2. 用 docker-compose 启动完整服务（API + Redis）
3. 验证健康检查端点
4. 测试服务可正常问答

### 练习三：编写 Chain 测试

为 `04_best_practices.py` 中的 ChainQA 编写 pytest 测试：
1. 单元测试：测试 Prompt 模板渲染正确
2. 集成测试：测试完整问答流程（mock LLM 响应）
3. 回归测试：测试缓存命中后返回相同结果

---

## 结语

完成本天后，你已掌握 LangChain 从原型到生产的完整能力。回顾整个板块：

- **阶段一（Day01-04）**：Model I/O、Prompt、Output Parsers——基础组件
- **阶段二（Day05-07）**：LCEL Chains、Memory、Document Loaders——组合与管理
- **阶段三（Day08-10）**：Retrievers、Tools、Callbacks——检索与工具
- **阶段四（Day11-12）**：LangServe/LangGraph、生产部署——服务化与工程化

**下一步**：基于这些基础，深入 **RAG 板块**（构建检索增强生成系统）和 **Agent 板块**（构建智能体），它们是 LangChain 的高级应用场景。

---

**返回**：[LangChain 学习指南](../README.md)
