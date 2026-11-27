# Code 说明

本目录为「Day08 - 容器化 AI/LLM 应用（GPU）」的代码与模板。

- 01_package_service.py   打包 AI 服务设计（离线）
- 02_gpu.py               GPU 支持与资源限制（离线）
- Dockerfile.service      自定义 Python 推理服务模板（需 Docker）
- docker-compose.gpu.yml  Ollama + GPU 组合编排（需 Docker + GPU toolkit）
- docker_check.py         Docker 环境检测（各天共用）
- README.md

运行方式：

```bash
# 离线讲解
python 01_package_service.py
python 02_gpu.py

# 需 Docker（及 GPU toolkit）
docker compose -f docker-compose.gpu.yml up -d
```

> 讲解脚本无需 Docker。Ollama 容器运行与 GPU 传递需真实 Docker 环境。