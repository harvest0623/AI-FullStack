# -*- coding: utf-8 -*-
"""
Day03 - 02 常用命令讲解（run / ps / stop / start / rm）

以问答式讲解最常用的一组 docker 命令及其常见参数（-d / -it / --name / -p 等）。
离线可运行（纯讲解）。
"""


def cmd_table():
    print("docker 容器命令速览：\n")
    rows = [
        ("docker run <img>", "创建并启动容器（一步到位）"),
        ("docker run -d <img>", "后台运行（detach）"),
        ("docker run -it <img> bash", "交互式进入容器终端"),
        ("docker run --name web <img>", "给容器命名，便于后续引用"),
        ("docker run -p 8080:80 <img>", "端口映射：宿主8080→容器80"),
        ("docker ps", "列出运行中的容器"),
        ("docker ps -a", "列出所有容器（含已退出）"),
        ("docker stop <c>", "停止容器"),
        ("docker start <c>", "启动已停止的容器"),
        ("docker restart <c>", "重启容器"),
        ("docker rm <c>", "删除已停止的容器"),
        ("docker rm -f <c>", "强制删除运行中的容器"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd:<30} {desc}")


def run_forms():
    print("\nrun 的三种典型用法：\n")
    print("  # 前太（前台）：进程占住终端，输出直达")
    print("  docker run --name web nginx")
    print("\n  # 后台（detach）：终端释放，容器在后台")
    print("  docker run -d --name web nginx")
    print("\n  # 交互式：进入容器内 shell")
    print("  docker run -it --name db bash")


def main():
    print(">> 容器常用命令\n")
    cmd_table()
    run_forms()
    print("\n  tips: --name 给容器命名，比用随机容器ID方便太多。")


if __name__ == "__main__":
    main()