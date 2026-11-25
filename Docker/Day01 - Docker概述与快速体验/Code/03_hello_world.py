# -*- coding: utf-8 -*-
"""
Day01 - 03 Hello World 全流程

讲解 docker run hello-world 这台戏怎么唱：
1. docker run 执行后，Client 通知 Daemon
2. Daemon 检查本地有没有 hello-world 镜像
3. 没有 → 从 Registry 拉取
4. 创建并运行容器，打印欢迎信息后退出

离线可运行：同时检测本机 Docker 环境，若就绪会给出真实命令提示。
"""

from docker_check import docker_cli_available, docker_daemon_available


def flow():
    print("docker run hello-world 的执行流程：\n")
    steps = [
        ("1. 用户输入命令", "docker run hello-world"),
        ("2. Client → Daemon", "把『运行 hello-world』请求发给守护进程"),
        ("3. 查找镜像", "Daemon 检查本地镜像仓库是否已有 hello-world"),
        ("4. 拉取（若缺）", "没有 → 从 Docker Hub 拉取该镜像"),
        ("5. 创建容器", "基于镜像创建容器并启动"),
        ("6. 打印欢迎", "容器内程序输出欢迎信息"),
        ("7. 容器退出", "默认命令执行完即退出"),
    ]
    for title, desc in steps:
        print(f"  {title}\n     → {desc}")
    print("\n  关键：镜像若已在本地，则跳过第 4 步（速度快很多）。")


def real_hint():
    print("\n真实命令（安装 Docker 后执行）：")
    print("  docker run hello-world")
    if not (docker_cli_available() and docker_daemon_available()):
        print("  （当前未检测到可用 Docker 环境，无法真实执行，先看流程讲解）")


def main():
    print(">> Hello World 全流程\n")
    flow()
    real_hint()
    print("\n  tips: run 在这里既『拉镜像』又『跑容器』，是 Docker 最常用的命令。")


if __name__ == "__main__":
    main()