# -*- coding: utf-8 -*-
"""
Day06 - 01 Compose 是什么

Compose 用一份 YAML 声明"有哪些服务、怎么互相连接、用什么网络/数据卷"，
然后用一条命令把整个应用栈跑起来，代替一条条 docker run。

离线可运行（纯讲解）。
"""


def compose_vs_run():
    print("Compose vs 逐个 docker run：\n")
    print("  逐个 run（繁琐、易错）：")
    print("    docker network create appnet")
    print("    docker volume create dbdata")
    print("    docker run -d --name db  --network appnet -v dbdata:/var/lib/mysql mysql:8")
    print("    docker run -d --name web --network appnet -p 8080:80 nginx")
    print("\n  用 Compose（一个文件搞定）：")
    print("    services/db、services/web ... 写在 docker-compose.yml")
    print("    docker compose up -d    ← 全部拉起、互联、建卷\n")


def yaml_blocks():
    print("docker-compose.yml 的主要子块：\n")
    rows = [
        ("version/services", "组合应用位置（新版可省略 version），核心是 services"),
        ("services.*", "定义一个服务（≈ 一个容器）"),
        ("image / build", "用现成镜像，或从 Dockerfile 构建"),
        ("ports", "端口映射列表（宿主机:容器）"),
        ("environment", "环境变量"),
        ("depends_on", "服务启动依赖顺序"),
        ("volumes", "数据卷挂载"),
        ("networks", "共享的自定义网络"),
        ("volumes / networks（顶层）", "声明要用到的命名卷与网络"),
    ]
    for k, v in rows:
        print(f"  {k:<14} {v}")


def main():
    print(">> Compose 是什么\n")
    compose_vs_run()
    yaml_blocks()
    print("\n  tips: 一个 compose 项目 = 一套「开箱即用」的多服务应用。")


if __name__ == "__main__":
    main()