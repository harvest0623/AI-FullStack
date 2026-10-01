# 文件用途：Docker 部署配置生成
# DockerDeployGenerator 类：生成 Dockerfile（多阶段构建/slim镜像/非root用户/HEALTHCHECK）
# + docker-compose.yml（LLM服务+Redis缓存+监控）+ .dockerignore
# 含 K8s 部署 YAML 生成
# Python 3.10+ 可运行（纯标准库）

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DeployConfig:
    """部署配置。"""

    app_name: str = "aisearch-llm"
    image_name: str = "aisearch-llm"
    image_tag: str = "1.0.0"
    port: int = 8000
    python_version: str = "3.11"
    requirements_file: str = "requirements.txt"
    app_module: str = "01_fastapi_service:app"
    workers: int = 4
    redis_enabled: bool = True
    monitor_enabled: bool = True
    k8s_replicas: int = 3
    k8s_namespace: str = "aisearch"


class DockerDeployGenerator:
    """Docker 部署配置生成器。"""

    def __init__(self, config: DeployConfig | None = None) -> None:
        self.config = config or DeployConfig()

    def generate_dockerfile(self) -> str:
        """生成多阶段 Dockerfile。"""
        c = self.config
        return f"""# ===== 构建阶段 =====
FROM python:{c.python_version}-slim AS builder

WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc g++ && \\
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY {c.requirements_file} .

# 安装依赖到指定目录
RUN pip install --no-cache-dir --user -r {c.requirements_file}

# ===== 运行阶段 =====
FROM python:{c.python_version}-slim AS runtime

# 安装运行时依赖（仅必要）
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl && \\
    rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY --chown=appuser:appuser . /app/

# 切换用户
USER appuser

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE {c.port}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \\
    CMD curl -f http://localhost:{c.port}/health || exit 1

# 启动命令
CMD ["uvicorn", "{c.app_module}", "--host", "0.0.0.0", "--port", "{c.port}", "--workers", "{c.workers}"]
"""

    def generate_compose(self) -> str:
        """生成 docker-compose.yml。"""
        c = self.config
        services: list[str] = []

        # LLM API 服务
        services.append(f"""  llm-api:
    image: {c.image_name}:{c.image_tag}
    container_name: {c.app_name}-api
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "{c.port}:{c.port}"
    environment:
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
      - API_KEY=${{API_KEY:-aisearch-secret-key}}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "2.0"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{c.port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - aisearch-net""")

        # Redis 缓存
        if c.redis_enabled:
            services.append("""  redis:
    image: redis:7-alpine
    container_name: aisearch-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - aisearch-net""")

        # 监控服务
        if c.monitor_enabled:
            services.append("""  prometheus:
    image: prom/prometheus:latest
    container_name: aisearch-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - aisearch-net

  grafana:
    image: grafana/grafana:latest
    container_name: aisearch-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - aisearch-net""")

        volumes: list[str] = []
        if c.redis_enabled:
            volumes.append("  redis_data:")
        if c.monitor_enabled:
            volumes.append("  prometheus_data:")
            volumes.append("  grafana_data:")

        return f"""version: "3.9"

services:
{chr(10).join(services)}

volumes:
{chr(10).join(volumes)}

networks:
  aisearch-net:
    driver: bridge
"""

    def generate_dockerignore(self) -> str:
        """生成 .dockerignore。"""
        return """__pycache__/
*.pyc
*.pyo
.git/
.gitignore
.env
.env.local
*.md
!README.md
.vscode/
.idea/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
eval_results/
output/
*.log
"""

    def generate_k8s_deployment(self) -> str:
        """生成 K8s Deployment YAML。"""
        c = self.config
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {c.app_name}
  namespace: {c.k8s_namespace}
  labels:
    app: {c.app_name}
spec:
  replicas: {c.k8s_replicas}
  selector:
    matchLabels:
      app: {c.app_name}
  template:
    metadata:
      labels:
        app: {c.app_name}
    spec:
      containers:
        - name: api
          image: {c.image_name}:{c.image_tag}
          ports:
            - containerPort: {c.port}
          env:
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {c.app_name}-secrets
                  key: openai-api-key
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: {c.app_name}-secrets
                  key: api-key
            - name: REDIS_URL
              value: "redis://redis-service:6379/0"
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: {c.port}
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: {c.port}
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: {c.app_name}-service
  namespace: {c.k8s_namespace}
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: {c.port}
      protocol: TCP
  selector:
    app: {c.app_name}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {c.app_name}-hpa
  namespace: {c.k8s_namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {c.app_name}
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
"""

    def generate_requirements(self) -> str:
        """生成 requirements.txt。"""
        return """fastapi>=0.110.0
uvicorn[standard]>=0.27.0
openai>=1.12.0
redis>=5.0.0
pydantic>=2.6.0
"""

    def generate_all(self, output_dir: str | Path = "docker_deploy") -> None:
        """生成所有部署文件。"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        files = {
            "Dockerfile": self.generate_dockerfile(),
            "docker-compose.yml": self.generate_compose(),
            ".dockerignore": self.generate_dockerignore(),
            "k8s-deployment.yaml": self.generate_k8s_deployment(),
            "requirements.txt": self.generate_requirements(),
        }
        for name, content in files.items():
            path = output_dir / name
            path.write_text(content, encoding="utf-8")
            print(f"[DockerDeploy] {name} 已生成")

        print(f"\n所有部署文件已生成到 {output_dir}")
        print("使用方法：")
        print(f"  cd {output_dir}")
        print("  docker-compose up -d")


def demo_docker_deploy() -> None:
    """演示 Docker 部署配置生成。"""
    config = DeployConfig(
        app_name="aisearch-llm",
        image_name="aisearch-llm",
        image_tag="1.0.0",
        port=8000,
        workers=4,
        redis_enabled=True,
        monitor_enabled=True,
        k8s_replicas=3,
    )
    generator = DockerDeployGenerator(config)

    print("=" * 60)
    print("Dockerfile")
    print("=" * 60)
    print(generator.generate_dockerfile())

    print("=" * 60)
    print("docker-compose.yml")
    print("=" * 60)
    print(generator.generate_compose())

    print("=" * 60)
    print("K8s Deployment")
    print("=" * 60)
    print(generator.generate_k8s_deployment())

    # 生成所有文件
    generator.generate_all()


if __name__ == "__main__":
    demo_docker_deploy()
