# Day12 Code - 生产部署完整指南

本目录提供 LLM 应用生产部署的完整工具链，包括 FastAPI 服务封装、Docker 容器化、成本监控与健康检查。AISearch 智能问答服务可通过本目录代码直接部署到生产环境。

## 环境准备

### 1. 安装依赖

```bash
pip install fastapi uvicorn[standard] openai redis pydantic
```

### 2. 配置环境变量

```bash
export OPENAI_API_KEY=sk-your-key        # OpenAI API Key
export API_KEY=your-service-api-key      # 服务访问密钥（客户端鉴权用）
export REDIS_URL=redis://localhost:6379/0 # Redis 地址（可选）
```

## 文件说明

| 文件 | 说明 | 运行命令 |
| --- | --- | --- |
| `01_fastapi_service.py` | 生产级 FastAPI LLM 服务 | `uvicorn 01_fastapi_service:app --host 0.0.0.0 --port 8000` |
| `02_docker_deploy.py` | Docker/K8s 部署配置生成器 | `python 02_docker_deploy.py` |
| `03_cost_monitor.py` | 成本监控与预算告警 | `python 03_cost_monitor.py` |
| `04_health_check.py` | 健康检查、熔断器与故障转移 | `python 04_health_check.py` |

## LLM 应用架构设计

```
                    ┌──────────────┐
                    │   客户端      │
                    └──────┬───────┘
                           ▼
┌──────────────────────────────────────────────┐
│  API 网关层  （认证 / 限流 / CORS / 日志）       │
├──────────────────────────────────────────────┤
│  业务逻辑层  （Prompt 管理 / 业务规则）          │
├──────────────────────────────────────────────┤
│  模型路由层  （简单→小模型 / 复杂→大模型）        │
├──────────────────────────────────────────────┤
│  缓存层     （Redis 响应缓存 / 语义缓存）        │
├──────────────────────────────────────────────┤
│  LLM 调用层  （重试 / 降级 / 熔断 / 故障转移）    │
├──────────────────────────────────────────────┤
│  监控层     （延迟 / 成本 / 质量 / 安全）        │
└──────────────────────────────────────────────┘
```

## FastAPI 服务部署教程

### 1. 启动服务

```bash
# 开发模式（热重载）
uvicorn 01_fastapi_service:app --host 0.0.0.0 --port 8000 --reload

# 生产模式（多 worker）
uvicorn 01_fastapi_service:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. API 文档

启动后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. 测试接口

```bash
# 健康检查
curl http://localhost:8000/health

# 对话（需带 API Key）
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer aisearch-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}]}'

# 流式对话
curl -X POST http://localhost:8000/stream \
  -H "Authorization: Bearer aisearch-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "讲个故事"}], "stream": true}'

# 向量生成
curl -X POST http://localhost:8000/embed \
  -H "Authorization: Bearer aisearch-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"input": "你好世界"}'
```

### 4. 接口列表

| 接口 | 方法 | 用途 | 鉴权 |
| --- | --- | --- | --- |
| `/health` | GET | 存活探针 | 否 |
| `/ready` | GET | 就绪探针 | 否 |
| `/models` | GET | 模型列表 | 是 |
| `/chat` | POST | 同步对话 | 是 |
| `/stream` | POST | 流式对话（SSE） | 是 |
| `/embed` | POST | 向量生成 | 是 |

## Docker 容器化步骤

### 1. 生成部署配置

```bash
python 02_docker_deploy.py
# 配置文件输出到 docker_deploy/ 目录
```

### 2. 构建与启动

```bash
cd docker_deploy

# 构建镜像
docker build -t aisearch-llm:1.0.0 .

# 启动全部服务（API + Redis + 监控）
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f llm-api
```

### 3. Dockerfile 特性

- ✅ 多阶段构建（builder + runtime，减小镜像体积）
- ✅ slim 基础镜像
- ✅ 非 root 用户运行
- ✅ HEALTHCHECK 健康检查
- ✅ 资源限制（2GB 内存 / 2 CPU）

## K8s 部署指南

### 1. 创建命名空间与 Secret

```bash
kubectl create namespace aisearch
kubectl create secret generic aisearch-llm-secrets \
  --from-literal=openai-api-key=sk-your-key \
  --from-literal=api-key=your-service-key \
  -n aisearch
```

### 2. 部署

```bash
kubectl apply -f docker_deploy/k8s-deployment.yaml -n aisearch
```

### 3. 验证

```bash
kubectl get pods -n aisearch
kubectl get svc -n aisearch
kubectl get hpa -n aisearch
```

### 4. 自动扩缩容

HPA 配置已包含：
- 最小 2 副本，最大 10 副本
- CPU > 70% 扩容
- 内存 > 80% 扩容

## 成本控制策略

### 成本优化组合拳

| 策略 | 实现位置 | 预期节省 |
| --- | --- | --- |
| 模型路由 | `01_fastapi_service.py` ModelRouter | 30-50% |
| 响应缓存 | `01_fastapi_service.py` ResponseCache | 20-40% |
| 成本监控 | `03_cost_monitor.py` CostMonitor | 防超支 |
| Token 优化 | Prompt 精简 | 10-20% |

### 配置成本预算

```python
from importlib import util
import sys
sys.path.insert(0, ".")

# 通过文件加载（避免文件名以数字开头无法 import）
import importlib.util
spec = importlib.util.spec_from_file_location("cost_monitor", "03_cost_monitor.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

monitor = mod.CostMonitor(
    budget=mod.BudgetConfig(
        daily_budget=50.0,
        weekly_budget=300.0,
        monthly_budget=1000.0,
    )
)
```

## 安全防护配置

### 1. API 鉴权

服务默认启用 Bearer Token 鉴权：
```python
# 请求需携带
Authorization: Bearer <API_KEY>
```

### 2. 限流

默认每用户每分钟 60 次请求，可通过环境变量调整：
```bash
export RATE_LIMIT=120  # 调高到 120
```

### 3. Prompt 注入防护建议

在业务逻辑层增加输入过滤：
```python
INJECTION_PATTERNS = ["忽略以上指令", "ignore previous", "system prompt"]
def check_injection(text: str) -> bool:
    return any(p in text.lower() for p in INJECTION_PATTERNS)
```

## CI/CD Pipeline 设计

### GitHub Actions 示例

```yaml
name: LLM Service CI/CD
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run eval tests
        run: python eval_tests.py
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t aisearch-llm:${{ github.sha }} .
      - name: Push to registry
        run: docker push aisearch-llm:${{ github.sha }}
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to K8s (canary 5%)
        run: kubectl set image deployment/aisearch-llm api=aisearch-llm:${{ github.sha }}
```

## 运维监控手册

### 监控接入

1. `01_fastapi_service.py` 暴露 `/health` 与 `/ready` 探针
2. `03_cost_monitor.py` 提供成本指标
3. `04_health_check.py` 提供熔断器与故障转移

### 告警配置

| 告警 | 条件 | 级别 |
| --- | --- | --- |
| 服务不可用 | `/health` 失败 | Critical |
| 高延迟 | P95 > 5s | Warning |
| 成本超限 | 日消耗 > 120% 预算 | Critical |
| 错误率高 | 错误率 > 10% | Critical |
| 熔断器开启 | Circuit OPEN | Critical |

## 最佳实践总结清单

### 架构设计
- [ ] 分层解耦（网关/业务/调用/缓存/监控）
- [ ] 无状态服务（便于水平扩展）
- [ ] 缓存优先（命中缓存直接返回）

### 安全防护
- [ ] API Key 鉴权
- [ ] 限流（用户级/IP级）
- [ ] Prompt 注入检测
- [ ] 输出内容过滤
- [ ] TLS 传输加密
- [ ] 审计日志

### 高可用
- [ ] 多模型备份
- [ ] 故障转移自动切换
- [ ] 熔断器防雪崩
- [ ] 重试与超时

### 成本控制
- [ ] 模型路由
- [ ] 响应缓存
- [ ] Token 优化
- [ ] 实时成本监控
- [ ] 预算告警

### 运维
- [ ] 健康检查探针
- [ ] 全链路监控
- [ ] 自动扩缩容
- [ ] 灰度发布
- [ ] 一键回滚
