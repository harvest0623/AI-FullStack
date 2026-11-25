# Code 说明

本目录为「Day02 - 镜像与分层原理」的可执行代码。

- 01_image_layer.py    镜像分层模型 + 写时复制
- 02_layer_cache.py    层缓存与复用模拟
- 03_tag_pull.py       镜像 tag 与拉取命令
- docker_check.py      Docker 环境检测（各天共用）
- README.md

运行方式：

```bash
python 01_image_layer.py
python 02_layer_cache.py
python 03_tag_pull.py
```

> 全部离线可运行。有 Docker 时 `03` 会提示真实命令供对照。