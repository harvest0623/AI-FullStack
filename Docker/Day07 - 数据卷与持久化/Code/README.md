# Code 说明

本目录为「Day07 - 数据卷与持久化」的可执行代码。

- 01_why_volume.py     为什么需要数据卷
- 02_bind_vs_named.py  命名卷 vs 绑定挂载
- 03_backup.py         卷的备份与恢复
- docker_check.py      Docker 环境检测（各天共用）
- README.md

运行方式：

```bash
python 01_why_volume.py
python 02_bind_vs_named.py
python 03_backup.py
```

> 全部离线可运行。有 Docker 时 `02` 提示真实卷命令供对照。