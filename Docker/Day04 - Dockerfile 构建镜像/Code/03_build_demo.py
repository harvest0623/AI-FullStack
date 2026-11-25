# -*- coding: utf-8 -*-
"""
Day04 - 03 docker build 流程与最佳实践

走一遍 docker build 的完整流程，并讲解 .dockerignore、tag、
构建上下文（context）等关键点。离线可运行。
"""


def build_flow():
    print("docker build 的执行流程：\n")
    steps = [
        ("读取构建上下文", "把当前目录（.）作为构建上下文发送给 Daemon"),
        ("逐条读取 Dockerfile", "从 FROM 开始，一条指令生成一层"),
        ("查询层缓存", "指令+内容未变则复用层，否则重建"),
        ("执行 RUN/COPY 等", "真正执行命令、复制文件，生成新层"),
        ("打 tag", "构建完成后赋名 myapp:1.0"),
    ]
    for i, (t, d) in enumerate(steps, 1):
        print(f"  {i}. {t}\n     → {d}")
    print("\n  命令：docker build -t myapp:1.0 .")


def best_practice():
    print("\n" + "-" * 60)
    print("最佳实践：\n")

    print("  · .dockerignore 排除无关文件（改少上下文，也避免泄密）")
    print("      示例：.venv/  .git/  node_modules/  __pycache__/")
    print("  · 冷变动放前：COPY requirements + RUN pip 在前，业务代码放后")
    print("  · 用具体基础镜像 tag（如 python:3.11-slim）而非 latest")
    print("  · 尽量小镜像：slim/alpine + 多阶段，减小攻击面与体积")
    print("  · 收尾清理：RUN 里 && 拼装并用 --no-cache-dir / minimal tools")
    print("  · 别用 root 跑：RUN useradd ... + USER 非 root 用户运行")

    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可在 Code 目录执行 docker build 看真实构建）")
    else:
        print("\n（当前无 Docker 环境，先理解流程与最佳实践）")


def main():
    print(">> docker build 流程与最佳实践\n")
    build_flow()
    best_practice()


if __name__ == "__main__":
    main()