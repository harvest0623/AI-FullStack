# Code 说明

本目录为「Day09 - 综合实战与部署」的代码与模板。

- 01_full_stack.py       完整应用栈架构（离线）
- 02_deploy_check.py     上线自检清单（离线）
- docker-compose.yml     全栈编排模板（前端+后端+向量库+Ollama，需 Docker）
- Dockerfile.prod        生产镜像参考（需 Docker）
- docker_check.py        Docker 环境检测（各天共用）
- README.md

运行方式：

```bash
# 离线讲解
python 01_full_stack.py
python 02_deploy_check.py

# 需 Docker 环境
docker compose up -d
docker compose ps
```

> 讲解脚本无需 Docker。全栈 compose 与生产镜像需真实 Docker 环境。