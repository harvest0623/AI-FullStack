# Code 说明

本目录为「Day04 - Dockerfile 构建镜像」的代码与模板。

- 01_dockerfile_guide.py  Dockerfile 指令详解（离线）
- 02_multistage.py        多阶段构建原理（离线）
- 03_build_demo.py        docker build 流程与最佳实践（离线）
- Dockerfile             可直接构建的 Python Web 示例（需 Docker）
- docker_check.py         Docker 环境检测（各天共用）
- README.md

运行方式：

```bash
# 离线讲解
python 01_dockerfile_guide.py
python 02_multistage.py
python 03_build_demo.py

# 需 Docker 环境：构建示例镜像
docker build -t myweb:1.0 .
docker run --rm myweb
```

> 讲解脚本无需 Docker。Dockerfile 需真实 Docker 环境执行 docker build。