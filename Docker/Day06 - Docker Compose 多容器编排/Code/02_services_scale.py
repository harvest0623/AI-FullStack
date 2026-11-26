# -*- coding: utf-8 -*-
"""
Day06 - 02 多服务与伸缩

用 Compose 管理多服务，并理解端口映射、环境变量、依赖与网络如何串联。
离线可运行（纯讲解 + 命令语义）。
"""


def services_table():
    print("compose 多服务示例（来自本目录 docker-compose.yml）：\n")
    rows = [
        ("web", "nginx", "8080:80", "对外入口，依赖 db"),
        ("db", "mysql:8", "—", "后台数据库，数据卷 dbdata"),
    ]
    print(f"{'服务':<8}{'镜像':<14}{'端口':<12}{'说明'}")
    print("-" * 60)
    for s, i, p, d in rows:
        print(f"{s:<8}{i:<14}{p:<12}{d}")


def detail():
    print("\n关键点解读：\n")
    print("  · depends_on: web 依赖 db → db 先起，顺序可控")
    print("  · environment: DB_HOST=db → web 里用「db」访问数据库")
    print("  · 同属 networks.appnet → 服务名即域名，互为可解析")
    print("  · volumes: dbdata → 数据库数据持久化，不随容器删除丢失")

    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可在 Code 目录执行 docker compose up -d 验证）")
    else:
        print("\n（当前无 Docker 环境，仅讲解）")


def main():
    print(">> 多服务与伸缩\n")
    services_table()
    detail()


if __name__ == "__main__":
    main()