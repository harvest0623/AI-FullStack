# -*- coding: utf-8 -*-
"""
Day03 - 03 进入容器与查看日志（exec / logs / cp）

让容器"可被管理"的三个能力：
1. docker exec -it <c> bash  进入正在运行的容器
2. docker logs <c>           查看容器输出日志
3. docker cp                 在容器与宿主机间拷贝文件

离线可运行（纯讲解 + 是否有 Docker 环境的提示）。
"""


def cmds():
    print("三个管理命令：\n")
    rows = [
        ("docker exec -it web bash", "进入运行中容器，开一个 bash 终端"),
        ("docker exec web ls /", "在容器内执行单条命令（非交互）"),
        ("docker logs web", "查看容器 stdout/stderr 日志"),
        ("docker logs -f web", "跟踪输出（follow），像 tail -f"),
        ("docker cp a:/x.txt ./", "从容器拷出文件"),
        ("docker cp ./x.txt web:/x.txt", "把文件拷进容器"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd:<28} {desc}")


def use_cases():
    print("\n典型场景：\n")
    print("  · 容器异常 → docker logs 看日志首查（而不是进容器）")
    print("  · 调试/摸底 → docker exec -it 进容器看环境")
    print("  · 迁移小文件 → docker cp（大文件/持久数据建议用卷，见 Day07）")


def main():
    print(">> 进入容器与日志\n")
    cmds()
    use_cases()

    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可执行这些命令对照真实输出）")
    else:
        print("\n（当前无 Docker 环境，仅讲解命令语义）")


if __name__ == "__main__":
    main()