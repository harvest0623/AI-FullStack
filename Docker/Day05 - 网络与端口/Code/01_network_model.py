# -*- coding: utf-8 -*-
"""
Day05 - 01 网络模式对比

Docker 的几种网络模式：bridge（默认，有独立内网段）、host（共享宿主网）、
none（无网络）、自定义 bridge（可域名互联）。

离线可运行（纯讲解）。
"""


def modes():
    print("Docker 网络模式：\n")
    rows = [
        ("bridge（默认）", "容器在独立内网（如 172.17.x.x），可互联；需端口映射才能被宿主机访问"),
        ("host", "容器直接复用宿主机网络栈，无内网隔离，性能好但少一层隔离"),
        ("none", "完全无网络，适合只做计算/隔离的任务"),
        ("自定义 bridge", "可给每个容器分配名字，用名字互相解析（推荐多容器互联）"),
    ]
    for name, desc in rows:
        print(f"  ■ {name}\n     {desc}\n")


def diagram():
    print("bridge 模式拓扑：\n")
    print("""  宿主机 192.168.1.10
      │
  ┌───┴────────────────────────── bridge 网桥 docker0 ───────────┐
  │                                                             │
  容器A 172.17.0.2   ──►  容器B 172.17.0.3  （同一网段可互访问）
    80 ► 宿主 8080        3306
    端口映射
""")


def main():
    print(">> 网络模式对比\n")
    modes()
    diagram()
    print("  tips: 默认 bridge 里容器用内网 IP 互通；对外服务要 -p 映射端口。")


if __name__ == "__main__":
    main()