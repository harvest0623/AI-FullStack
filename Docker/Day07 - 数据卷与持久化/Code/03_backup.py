# -*- coding: utf-8 -*-
"""
Day07 - 03 备份与恢复卷

命名卷的数据要能备份、迁移、恢复。给出常用做法与命令。
离线可运行（纯讲解）。
"""


def backup():
    print("备份一个命名卷：\n")
    print("""  # 用一个临时容器挂载该卷 + 挂载宿主备份目录，打包.tar
  docker run --rm \\
      -v mydata:/src \\
      -v $(pwd):/backup \\
      alpine tar czf /backup/mydata_backup.tar.gz -C /src .

  # 注意我用 $(pwd) 挂载当前目录，把 tar 输出到宿主
  """)


def restore():
    print("\n从备份恢复：\n")
    print("""  # 向挂载的卷里解包
  docker run --rm \\
      -v mydata:/dest \\
      -v $(pwd):/backup \\
      alpine tar xzf /backup/mydata_backup.tar.gz -C /dest
  """)


def tips():
    print("\n要点：\n")
    print("  · 备份 = 把卷的内容打包成 tar（利用 --rm 一次性容器）")
    print("  · 恢复 = 解包回卷")
    print("  · 若用绑定挂载，其实直接备份宿主机目录的 tar 即可")
    print("  · 生产上常用云卷快照/存储服务做增量")


def main():
    print(">> 卷的备份与恢复\n")
    backup()
    restore()
    tips()


if __name__ == "__main__":
    main()