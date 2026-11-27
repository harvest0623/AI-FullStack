# -*- coding: utf-8 -*-
"""
Day07 - 02 命名卷 vs 绑定挂载

两种把数据放容器外的方式：
1. 命名卷（named volume）：由 Docker 管理、路径自动分配、跨机器可移植
2. 绑定挂载（bind mount）：把宿主机某个目录直接挂进容器，路径由你指定

离线可运行（纯讲解）。
"""


def compare():
    print("命名卷 vs 绑定挂载：\n")
    rows = [
        ("管理方式", "Docker 管理（docker volume 命令）", "宿主主机路径直接挂载"),
        ("路径", "Docker 自动分配", "你指定宿主绝对路径"),
        ("可移植性", "强（卷是抽象，可跨机备份迁移）", "弱（绑死的宿主路径）"),
        ("用途", "应用持久数据、库数据", "开发时实时同步代码/配置文件"),
        ("命令", "-v volume:/data", "-v /宿主/绝对路径:/data"),
    ]
    print(f"{'维度':<10}{'命名卷':<24}{'绑定挂载'}")
    print("-" * 62)
    for a, b, c in rows:
        print(f"{a:<10}{b:<24}{c}")


def when():
    print("\n怎么选：\n")
    print("  · 数据库/应用持久数据 → 命名卷（推荐）")
    print("  · 开发热更新代码/改配置 → 绑定挂载（宿主机文件即容器文件）")
    print("  · 需要直接看到/编辑宿主机文件的场景 → 绑定挂载")


def cmds():
    print("\n卷相关命令：\n")
    cmds = [
        ("docker volume create mydata", "创建命名卷"),
        ("docker volume ls", "列出卷"),
        ("docker run -v mydata:/data ...", "挂载命名卷到 /data"),
        ("docker run -v /宿主机路径:/data ...", "绑定挂载宿主目录"),
        ("docker run -v /宿主机路径:/数据内容:ro ...", "只读挂载"),
        ("docker volume inspect mydata", "查看卷详情"),
    ]
    for c, d in cmds:
        print(f"  {c:<44} {d}")

    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可执行上述卷命令真实验证）")
    else:
        print("\n（当前无 Docker 环境，仅讲解）")


def main():
    print(">> 命名卷 vs 绑定挂载\n")
    compare()
    when()
    cmds()


if __name__ == "__main__":
    main()