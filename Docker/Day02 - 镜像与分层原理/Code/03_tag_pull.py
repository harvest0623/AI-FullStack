# -*- coding: utf-8 -*-
"""
Day02 - 03 镜像 tag 与拉取

讲解镜像的命名规范（仓库:标签）、tag 的多种写法、
`docker pull` / `docker images` / `docker tag` / `docker rmi` 的真实命令语义。

离线可运行（纯讲解；有 Docker 时给出真实命令提示）。
"""


def naming():
    print("一、镜像命名（repo:tag）\n")
    print("  完整写法：  <仓库名>:<标签>")
    print("  例如：      python:3.11      → 仓库名 python，标签 3.11")
    print("              python:latest    → 仓库名 python，标签 latest（默认）")
    print("              nginx:latest     → 仓库名 nginx，默认 latest")
    print("  Docker Hub 公共镜像会省略前缀 docker.io/library/")
    print("  私有/组织级： mycompany/webapp:1.0.0 → mycompany/webapp:1.0.0")


def tag_usage():
    print("\n二、tag 的意义：版本即标签\n")
    for tag in ["1.0.0", "1.0", "1", "latest"]:
        print(f"  {tag:<8} → 指向同一份具体镜像的别名，便于滚动升级与回滚")
    print("  tips: 部署时固定具体 tag（如 1.0.0）而非 latest，保证可复现。")


def commands():
    print("\n三、常用真实命令（语义）\n")
    cmds = [
        ("docker pull python:3.11", "从仓库拉取镜像到本地"),
        ("docker images", "列出本地镜像（带 tag、大小）"),
        ("docker tag a b", "给镜像打新标签"),
        ("docker rmi <镜像>", "删除本地镜像"),
        ("docker run python:3.11", "用指定 tag 运行"),
    ]
    for cmd, desc in cmds:
        print(f"  {cmd:<28} {desc}")

    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可执行上面命令查看真实输出）")
    else:
        print("\n（当前无 Docker 环境，仅讲解命令语义）")


def main():
    print(">> 镜像 tag 与拉取\n")
    naming()
    tag_usage()
    commands()


if __name__ == "__main__":
    main()