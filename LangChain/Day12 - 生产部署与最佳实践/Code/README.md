# Day12 Code - 生产部署与最佳实践代码示例

> 本目录包含 Day12 全部可运行代码，整合 Day01-Day11 所学构建 ChainQA 生产级应用

## 文件清单

| 文件 | 内容 | 运行方式 | 场景 |
|------|------|---------|------|
| `01_production_architecture.py` | 5 层生产架构实现 | `uvicorn 01_production_architecture:app --reload --port 8002` | ProductionChainQA |
| `02_caching_retry.py` | 缓存与重试机制 | `python 02_caching_retry.py` | CacheRetryManager |
| `03_docker_deploy.py` | Docker 配置生成 | `python 03_docker_deploy.py` | DockerDeployGenerator |
| `04_best_practices.py` | 综合最佳实践 | `uvicorn 04_best_practices:app --reload --port 8003` | ChainQA 生产级应用 |

## 运行顺序建议

```
01_production_architecture.py  ← 先看完整生产架构
      │
      ▼
02_caching_retry.py            ← 再学缓存与重试机制
      │
      ▼
03_docker_deploy.py            ← 生成 Docker 部署配置
      │
      ▼
04_best_practices.py           ← 最后运行综合最佳实践应用
```

## 环境准备

```bash
# 核心依赖
pip install langchain langchain-openai langchain-community langserve langgraph
pip install fastapi uvicorn python-dotenv pydantic-settings

# 配置 API Key（.env 文件）
# OPENAI_API_KEY=sk-xxxxxxxx
# 可选：LangSmith
# LANGCHAIN_API_KEY=ls_xxxxxxxx
# LANGCHAIN_TRACING_V2=true
```

## 运行示例

```bash
cd "d:\Coding\AI-FullStack\LangChain\Day12 - 生产部署与最佳实践\Code"

# 1. 生产架构服务（端口 8002）
uvicorn 01_production_architecture:app --reload --port 8002

# 2. 缓存与重试演示
python 02_caching_retry.py

# 3. 生成 Docker 配置
python 03_docker_deploy.py

# 4. 综合最佳实践应用（端口 8003）
uvicorn 04_best_practices:app --reload --port 8003
```

## 生产部署完整指南

### 生产架构设计图

```
┌─────────────────────────────────────────────────────┐
│  客户端（Web/App/其他服务）                          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  API 网关层                                          │
│  FastAPI + 中间件（鉴权/限流/日志/CORS）             │
│  端点：/api/qa, /api/rag, /health, /metrics         │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Chain 层                                            │
│  LCEL 链 / 工具调用 / RAG 检索链                     │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  模型层                                              │
│  多模型路由 + .with_retry() + .with_fallbacks()     │
└──────────┬──────────────────────┬───────────────────┘
           ▼                      ▼
┌─────────────────┐     ┌─────────────────────────────┐
│  缓存层          │     │  监控层                      │
│  InMemoryCache  │     │  Callback + LangSmith       │
│  SQLiteCache    │     │  日志 + 指标 + 告警          │
└─────────────────┘     └─────────────────────────────┘
```

### 性能优化清单

| 优化项 | 方法 | 预期收益 |
|--------|------|---------|
| LLM 缓存 | `set_llm_cache(InMemoryCache())` | 重复请求零延迟 |
| 持久化缓存 | `set_llm_cache(SQLiteCache())` | 重启后保留 |
| 批量调用 | `chain.batch([...])` | 并行降低总耗时 |
| 异步并发 | `await chain.abatch([...])` | 高并发场景 |
| 模型路由 | 短问题用小模型 | 降低 80% 成本 |
| Prompt 精简 | 去除冗余描述 | 降低 30% Token |
| 连接池复用 | 保持 HTTP 长连接 | 降低连接开销 |

### 错误处理配置建议

```python
# 1. 重试（指数退避）
model = ChatOpenAI(...).with_retry(stop_after_attempt=3)

# 2. 回退（主模型故障切备用）
model = primary.with_fallbacks([fallback])

# 3. 超时
model = ChatOpenAI(..., timeout=30)

# 4. 工具内部错误处理
@tool
def safe_tool(x: str) -> str:
    try:
        return do_something(x)
    except Exception as e:
        return f"工具失败：{e}"  # 返回错误而非抛异常
```

### Docker 部署步骤

```bash
# 1. 生成 Docker 配置
python 03_docker_deploy.py

# 2. 进入输出目录
cd docker_output

# 3. 构建镜像
docker build -t chainqa:latest .

# 4. 单服务运行
docker run -d -p 8000:8000 --env-file ../.env --name chainqa chainqa:latest

# 5. 或用 docker-compose 多服务
docker compose up -d

# 6. 验证
curl http://localhost:8000/health
```

### CI/CD Pipeline 设计

```
代码提交 → GitHub/GitLab
    │
    ▼
┌─────────────────────┐
│ 1. 代码检查         │  lint + type check
├─────────────────────┤
│ 2. 单元测试         │  pytest（mock LLM）
├─────────────────────┤
│ 3. 集成测试         │  pytest（真实 LLM，小流量）
├─────────────────────┤
│ 4. 构建镜像         │  docker build
├─────────────────────┤
│ 5. 灰度发布         │  K8s 滚动更新（30%流量）
├─────────────────────┤
│ 6. 健康检查         │  /health 验证
├─────────────────────┤
│ 7. 全量发布         │  100% 流量
├─────────────────────┤
│ 8. 监控告警         │  LangSmith + Prometheus
└─────────────────────┘
    │（异常时）
    ▼
  自动回滚
```

### 版本升级迁移指南

| 迁移路径 | 关键变化 | 迁移建议 |
|---------|---------|---------|
| 0.1 → 0.2 | Legacy Chain 废弃 | `LLMChain` → `prompt \| model \| parser` |
| 0.2 → 0.3 | langchain_community 拆分 | 更新 import 路径 |
| Legacy → LCEL | 类式 → 管道符 | 重写 Chain 为 LCEL |
| 0.3 → 未来 | 持续演进 | 关注 changelog |

**迁移检查清单**：
- [ ] 更新依赖版本 `pip install -U langchain`
- [ ] 检查废弃 API（DeprecationWarning）
- [ ] 更新 import 路径
- [ ] 重写 Legacy Chain 为 LCEL
- [ ] 运行回归测试验证

### 最佳实践总结表

| 维度 | 最佳实践 | 对应天数 |
|------|---------|---------|
| 架构 | 分层设计 / 模块化 / 可测试 | Day05, Day12 |
| Prompt | 模板化 / 版本管理 / 测试 | Day03 |
| 输出 | 结构化解析 / 错误重试 | Day04 |
| 组合 | LCEL 管道 / 可组合 | Day05 |
| 记忆 | 策略选择 / 多会话管理 | Day06 |
| 文档 | RecursiveCharacterTextSplitter | Day07 |
| 检索 | VectorStore / MMR | Day08 |
| 工具 | @tool 装饰器 / 错误处理 | Day09 |
| 监控 | Callback / LangSmith | Day10 |
| 服务 | LangServe / LangGraph | Day11 |
| 部署 | Docker / CI-CD | Day12 |
| 成本 | 模型路由 / 缓存 / Token 优化 | Day12 |
| 安全 | 输入过滤 / 密钥管理 | Day12 |

### 安全配置清单

- [ ] API Key 不硬编码（用 .env / 环境变量 / 密钥管理服务）
- [ ] .env 不入 Git（.gitignore）和镜像（.dockerignore）
- [ ] API 鉴权（JWT / API Token）
- [ ] 输入过滤（防 Prompt 注入）
- [ ] 输出检查（敏感信息脱敏）
- [ ] 限流（防滥用）
- [ ] eval 限制（工具中禁用 `__builtins__`）
- [ ] HTTPS 部署
- [ ] 非 root 用户运行容器

## 常见问题

**Q1：缓存不生效？**
- 确认 `set_llm_cache` 在创建模型前调用
- 注意：temperature != 0 时缓存可能不生效（输出不确定）
- SQLite 缓存需确认文件可写

**Q2：with_fallbacks 不触发？**
- 主模型需真实抛异常（而非返回错误文本）
- 确认主模型和备用模型都正确配置

**Q3：Docker 镜像过大？**
- 用多阶段构建（builder + runtime）
- 用 slim 基础镜像
- 配置 .dockerignore 排除无关文件

**Q4：LangServe 部署后并发上不去？**
- 增加 uvicorn workers：`--workers 4`
- 用异步：`ainvoke` / `astream`
- 加缓存减少 LLM 调用

## 学习产出

完成本目录代码后，你应能：
- [ ] 设计 5 层生产架构
- [ ] 实现 LLM 缓存（内存 + SQLite）
- [ ] 配置重试和模型回退
- [ ] 生成 Docker 部署配置
- [ ] 整合 Day01-Day11 所学构建完整应用
- [ ] 配置监控、日志、错误处理
- [ ] 理解 CI/CD 流程和版本迁移

---

## 整个 LangChain 板块总结

恭喜完成 Day01-Day12 全部学习！回顾你的成长路径：

| 阶段 | 天数 | 核心能力 |
|------|------|---------|
| 阶段一 | Day01-04 | 基础组件：Model I/O / Prompt / Parser |
| 阶段二 | Day05-07 | 组合管理：LCEL / Memory / Document |
| 阶段三 | Day08-10 | 检索工具：Retriever / Tools / Callbacks |
| 阶段四 | Day11-12 | 服务部署：LangServe / LangGraph / 生产 |

**下一步推荐**：
- **RAG 板块**：深入检索增强生成系统
- **Agent 板块**：基于 Tools + LangGraph 构建智能体
- **FastAPI 板块**：深入 API 服务开发
- **Docker 板块**：深入容器化部署
