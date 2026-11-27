# -*- coding: utf-8 -*-
"""
docker_check.py - Docker 环境检测工具（各天共用）
离线可运行。
"""

import subprocess


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode, (r.stdout or r.stderr).strip()
    except Exception as e:
        return -1, str(e)


def docker_cli_available() -> bool:
    code, out = _run(["docker", "--version"])
    return code == 0 and "Docker" in out


def docker_daemon_available() -> bool:
    code, _ = _run(["docker", "info"])
    return code == 0


def docker_version() -> str:
    code, out = _run(["docker", "--version"])
    return out if code == 0 else "未安装 Docker CLI"


def summarize() -> dict:
    cli = docker_cli_available()
    daemon = docker_daemon_available() if cli else False
    return {
        "cli": cli,
        "daemon": daemon,
        "version": docker_version(),
        "note": ("Docker 就绪" if (cli and daemon)
                 else "未检测到可用 Docker 环境（讲解脚本仍可运行）" if not cli
                 else "已装 CLI，但 Docker Daemon 未运行（请启动 Docker Desktop）"),
    }


def print_report():
    out = summarize()
    print("=" * 60)
    print("Docker 环境检测报告")
    print("=" * 60)
    print(f"  版本信息：{out['version']}")
    print(f"  CLI 可用：{'✓' if out['cli'] else '✗'}")
    print(f"  Daemon 运行：{'✓' if out['daemon'] else '✗'}")
    print(f"  结论：{out['note']}")


if __name__ == "__main__":
    print_report()