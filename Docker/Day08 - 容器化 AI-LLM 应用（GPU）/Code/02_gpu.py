# -*- coding: utf-8 -*-
"""
Day08 - 02 GPU 支持与资源限制

让容器用上宿主机 GPU，并给容器设资源上限（内存/CPU），保证多容器不争抢。

离线可运行：检测宿主机 GPU + Docker 环境，纯讲解 GPU 容器化；同时给出资源限制命令。
"""

import shutil
import subprocess
from docker_check import docker_cli_available, docker_daemon_available


def host_gpu():
    """检测宿主机是否有 NVIDIA GPU"""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name",
             "--format=csv,noheader"], timeout=5).decode().strip()
        return out
    except Exception:
        return None


def gpu_docker():
    print("容器内使用 GPU（需 NVIDIA Container Toolkit）：\n")
    rows = [
        ("docker run --gpus all <img>", "把全部 GPU 传入容器"),
        ("docker run --gpus manual --device nvidia.com/gpu=0 <img>", "只给某块 GPU"),
        ("deploy.gpus", "compose 里用 deploy.resources.reservations.devices 声明 gpu"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd:<52} {desc}")


def resource_limit():
    print("\n资源限制（避免容器吃光主机）：\n")
    rows = [
        ("docker run --memory 4g --cpus 2 <img>", "限制内存 4GB、CPU 2 核"),
        ("--memory-swap 8g", "允许最多 8GB（含 swap）"),
        ("--cpuset-cpus 0-3", "绑定到 CPU 0-3"),
        ("compose: deploy.resources.limits", "compose 里声明 limits/requests"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd:<44} {desc}")


def main():
    print(">> GPU 支持与资源限制\n")

    gpu = host_gpu()
    if gpu:
        print(f"宿主机检测到 NVIDIA GPU：{gpu}\n")
    else:
        print("宿主机未检测到 NVIDIA GPU（本机可能是 CPU 或未装 nvidia-smi）\n")

    print("容器里如何用 GPU（需宿主机先装 NVIDIA Container Toolkit）：\n")
    gpu_docker()

    print("\n" + "=" * 60)
    print("资源限制（重要！模型服务吃显存/内存，务必设上限）：")
    resource_limit()

    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境；如有 GPU + toolkit，可 run --gpus 验证）")
    else:
        print("\n（当前无 Docker 环境，仅讲解）")


if __name__ == "__main__":
    main()