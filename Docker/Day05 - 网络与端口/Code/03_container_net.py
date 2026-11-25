# -*- coding: utf-8 -*-
"""
Day05 - 03 自定义网络与容器互联

多容器协作时，用自定义 bridge 网络 + 容器名做 DNS，比 IP 更可靠。
离线可运行（纯讲解；有 Docker 时给出真实命令）。
"""


def why():
    print("为什么用自定义网络？\n")
    print("  · 容器重启后内网 IP 可能变 → 用 IP 互联不可靠")
    print("  · 默认 bridge 之间不互通，也不支持按名字解析")
    print("  · 自定义网络：容器用『容器名』当主机名互相访问，容器重建名字不变\n")


def how():
    print("操作流程：\n")
    rows = [
        ("docker network create mynet", "创建一个自定义 bridge 网络 mynet"),
        ("docker network ls", "列出网络"),
        ("docker network rm mynet", "删除网络"),
        ("docker run --network mynet --name web ...", "让容器加入 mynet"),
        ("docker network connect mynet c1", "给运行中容器追加网络"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd:<34} {desc}")


def example():
    print("\n示例：web 与 db 互联")
    print("""  docker network create app_net
  docker run -d --name db  --network app_net mysql:8
  docker run -d --name web --network app_net myweb:1.0
  # 在 web 容器里可用  db:3306  访问数据库（按名字解析）""")


def main():
    print(">> 自定义网络与容器互联\n")
    why()
    how()
    example()
    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可执行上述命令真实验证容器互联）")
    else:
        print("\n（当前无 Docker 环境，仅讲解）")


if __name__ == "__main__":
    main()