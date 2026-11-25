# -*- coding: utf-8 -*-
"""
Day01 - 01 Docker 是什么：概念与三要素

讲解 Docker 的三大核心概念：镜像 / 容器 / 仓库，
以及 Docker 的整体架构（Client / Daemon / Registry）。

离线可运行（纯讲解，不依赖 Docker）。
"""


def three_elements():
    print("一、三大核心概念（镜像 / 容器 / 仓库）\n")
    rows = [
        ("镜像 Image", "只读模板：应用 + 运行环境 + 依赖，一层层打包。",
         "类似「程序安装包 + 完整系统环境」"),
        ("容器 Container", "镜像的运行实例，拥有一个可写的顶层；可起可停、互相隔离。",
         "类似「运行中的一个程序进程」（但自带完整环境）"),
        ("仓库 Repository", "存放与分发镜像的地方，如 Docker Hub。",
         "类似「应用商店/代码仓库」"),
    ]
    for name, desc, analogy in rows:
        print(f"  ■ {name}")
        print(f"     {desc}")
        print(f"     类比：{analogy}\n")


def architecture():
    print("二、Docker 整体架构\n")
    print("""
  ┌────────────┐  命令    ┌──────────────┐   拉取/推送   ┌──────────────┐
  │  CLI       │ ───────► │  Docker      │ ───────────► │  Registry    │
  │  docker    │          │  Daemon      │              │  (Docker Hub)│
  │  (客户端)   │ ◄─────── │  (守护进程)   │ ◄─────────── │              │
  └────────────┘  结果     └──────┬───────┘      构建镜像   └──────────────┘
                                 │ 管理
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌─────────┐  ┌─────────┐  ┌─────────┐
              │ 容器 A   │  │ 容器 B   │  │ 容器 C   │
              │ (进程)   │  │ (进程)   │  │ (进程)   │
              └─────────┘  └─────────┘  └─────────┘
    """)
    print("要点：你只会接触到 CLI；Daemon 负责创建/运行容器；"
          "Registry 负责存镜像。")


def main():
    print(">> Docker 是什么\n")
    three_elements()
    architecture()

    print("三、一句话概括")
    print("  Docker = 把『应用 + 环境』打包成镜像，在任何机器上一个命令跑成容器。")

    print("\n  tips: 后续几日会逐一深入镜像(分层)、容器(生命周期)、仓库(拉取/推送)。")


if __name__ == "__main__":
    main()