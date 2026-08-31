# 文件用途：Docker 部署配置生成
# 生成 Dockerfile（多阶段构建/slim 镜像/非 root 用户/HEALTHCHECK）
# + docker-compose.yml（API 服务+Redis 缓存+监控）
# + .dockerignore + requirements.txt
# DockerDeployGenerator 类。含 K8s 部署 YAML 示例
# 运行：python 03_docker_deploy.py
# 依赖：无需额外依赖（纯文件生成）

from __future__ import annotations

import os
from pathlib import Path


# ============================================================
# DockerDeployGenerator：Docker 部署配置生成器
# ============================================================

class DockerDeployGenerator:
    """生成 ChainQA 的 Docker 部署配置文件

    生成文件：
    - Dockerfile（多阶段构建）
    - docker-compose.yml（API + Redis）
    - .dockerignore
    - requirements.txt
    - k8s.yaml（K8s 部署示例）
    """

    def __init__(self, output_dir: str = "docker_output") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> None:
        """生成全部配置文件"""
        print(f"输出目录：{self.output_dir.resolve()}")
        self._generate_dockerfile()
        self._generate_docker_compose()
        self._generate_dockerignore()
        self._generate_requirements()
        self._generate_k8s_yaml()
        self._print_usage()

    # ── Dockerfile ──

    def _generate_dockerfile(self) -> None:
        """生成 Dockerfile（多阶段构建 + 非 root + HEALTHCHECK）"""
        content = """# ============================================================
# ChainQA Dockerfile - 多阶段构建
# ============================================================

# --- 阶段1：构建阶段（安装依赖）---
FROM python:3.12-slim AS builder

WORKDIR /build

# 仅复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

# 安装依赖到指定目录（便于阶段2复制）
RUN pip install --no-cache-dir --user -r requirements.txt

# --- 阶段2：运行阶段（最终镜像）---
FROM python:3.12-slim

WORKDIR /app

# 复制依赖（从 builder 阶段）
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 确保 PATH 包含用户安装的包
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 创建非 root 用户运行（安全最佳实践）
RUN useradd -m -u 1000 appuser && \\
    chown -R appuser:appuser /app
USER appuser

# 健康检查（每 30s 检查一次）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "01_production_architecture:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""
        self._write("Dockerfile", content)

    # ── docker-compose.yml ──

    def _generate_docker_compose(self) -> None:
        """生成 docker-compose.yml（API + Redis + 监控）"""
        content = """# ============================================================
# ChainQA docker-compose - 多服务编排
# ============================================================
version: "3.9"

services:
  # ChainQA API 服务
  chainqa-api:
    build: .
    container_name: chainqa-api
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - CHAINQA_CACHE_TYPE=sqlite
      - CHAINQA_ENABLE_CACHE=true
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - chainqa-net

  # Redis 缓存服务
  redis:
    image: redis:7-alpine
    container_name: chainqa-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - chainqa-net

  # 可选：Prometheus 监控
  prometheus:
    image: prom/prometheus:latest
    container_name: chainqa-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - chainqa-api
    restart: unless-stopped
    networks:
      - chainqa-net
    profiles:
      - monitoring  # docker compose --profile monitoring up 启用

volumes:
  redis-data:

networks:
  chainqa-net:
    driver: bridge
"""
        self._write("docker-compose.yml", content)

    # ── .dockerignore ──

    def _generate_dockerignore(self) -> None:
        """生成 .dockerignore"""
        content = """# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.egg-info
.venv
venv
env

# IDE
.vscode
.idea
*.swp

# 测试与文档
tests/
*.md
docs/

# 环境变量（敏感信息，不入镜像）
.env
.env.*

# 缓存与日志
*.db
*.log
cache/
__pycache__/

# Docker 自身
Dockerfile
docker-compose.yml
.dockerignore

# 输出目录
docker_output/
"""
        self._write(".dockerignore", content)

    # ── requirements.txt ──

    def _generate_requirements(self) -> None:
        """生成 requirements.txt"""
        content = """# ChainQA 生产依赖
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langserve>=0.3.0
langgraph>=0.2.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# 可选：缓存后端
redis>=5.0.0

# 可选：监控
# prometheus-client>=0.21.0
"""
        self._write("requirements.txt", content)

    # ── K8s 部署 YAML ──

    def _generate_k8s_yaml(self) -> None:
        """生成 K8s 部署 YAML 示例"""
        content = """# ============================================================
# ChainQA Kubernetes 部署示例
# ============================================================
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chainqa-api
  labels:
    app: chainqa
spec:
  replicas: 3                      # 3 个副本
  selector:
    matchLabels:
      app: chainqa
  template:
    metadata:
      labels:
        app: chainqa
    spec:
      containers:
      - name: chainqa-api
        image: chainqa:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chainqa-secrets
              key: openai-api-key
        - name: CHAINQA_CACHE_TYPE
          value: "sqlite"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: chainqa-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: chainqa
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chainqa-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chainqa-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"""
        self._write("k8s.yaml", content)

    # ── 辅助 ──

    def _write(self, filename: str, content: str) -> None:
        """写入文件"""
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        print(f"  ✅ 已生成 {filename}")

    def _print_usage(self) -> None:
        """打印使用说明"""
        print(f"""
{'=' * 60}
📦 Docker 部署配置已生成到：{self.output_dir.resolve()}

文件清单：
  - Dockerfile          （多阶段构建镜像）
  - docker-compose.yml  （API + Redis + 监控）
  - .dockerignore       （排除无关文件）
  - requirements.txt    （Python 依赖）
  - k8s.yaml            （K8s 部署示例）

使用方法：

1️⃣  Docker 单服务部署：
  cd {self.output_dir}
  docker build -t chainqa:latest .
  docker run -d -p 8000:8000 --env-file ../.env --name chainqa chainqa:latest

2️⃣  Docker Compose 多服务部署：
  cd {self.output_dir}
  docker compose up -d                    # 启动 API + Redis
  docker compose --profile monitoring up -d  # 含监控
  docker compose logs -f                  # 查看日志
  docker compose down                     # 停止

3️⃣  Kubernetes 部署：
  kubectl apply -f k8s.yaml
  kubectl get pods -l app=chainqa
  kubectl scale deployment chainqa-api --replicas=5

4️⃣  验证服务：
  curl http://localhost:8000/health
  curl http://localhost:8000/docs
{'=' * 60}
""")


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    print("=" * 60)
    print("Day12 - 03 Docker 部署配置生成")
    print("DockerDeployGenerator")
    print("=" * 60)

    # 默认输出到 Code 目录下的 docker_output
    output_dir = os.path.join(os.path.dirname(__file__), "docker_output")
    generator = DockerDeployGenerator(output_dir=output_dir)

    print("\n生成 Docker 部署配置文件...\n")
    generator.generate_all()

    print("\n✅ Docker 部署配置生成完成")
    print("要点：")
    print("  1. Dockerfile 多阶段构建减小镜像体积")
    print("  2. 非 root 用户运行提升安全性")
    print("  3. HEALTHCHECK 配置健康检查")
    print("  4. docker-compose 编排 API + Redis + 监控")
    print("  5. K8s 配置含副本、自动扩缩、探针")
    print("  6. .dockerignore 排除敏感文件（.env 不入镜像）")


if __name__ == "__main__":
    main()
