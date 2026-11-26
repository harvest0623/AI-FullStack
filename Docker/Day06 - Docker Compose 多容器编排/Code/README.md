# Code 说明

本目录为「Day06 - Docker Compose 多容器编排」的代码与模板。

- 01_compose_intro.py    Compose 是什么（离线）
- 02_services_scale.py   多服务与伸缩（离线）
- 03_compose_cmd.py      Compose 常用命令（离线）
- docker-compose.yml     web + db 组合服务栈（需 Docker）
- docker_check.py        Docker 环境检测（各天共用）
- README.md

运行方式：

```bash
# 离线讲解
python 01_compose_intro.py
python 02_services_scale.py
python 03_compose_cmd.py

# 需 Docker 环境
docker compose up -d
docker compose ps
docker compose down
```

> 讲解脚本无需 Docker。docker-compose.yml 需真实 Docker 环境执行。