# -*- coding: utf-8 -*-
"""
Day05 - 02 端口映射原理

为什么容器里监听 80，宿主机却要访问 8080？——端口映射把所有者对外的
访问转进来：宿主机:<端口> = port at > 容器:<端口>。

离线可运行（纯讲解 + 常见参数解读）。
"""


def explain():
    print("端口映射 `-p 宿主端口:容器端口`：\n")
    print("""   访问  http://localhost:8080
              │
     宿主机/081 ┌──────────────┐
     （监听8080）│  docker NAT  │
              └──────┬───────┘
                     │ 转发到容器内 80
              ┌──────▼───────┐
              │ 容器内 web@80 │
              └──────────────┘
""")


def forms():
    print("常见形式的解读：\n")
    rows = [
        ("-p 8080:80", "宿主 8080 → 容器 80（显式指定两边端口）"),
        ("-p 80", "宿主随机端口 → 容器 80"),
        ("-p 127.0.0.1:8080:80", "只绑定本机回环，不对外暴露（更安全）"),
        ("-P", "把 EXPOSE 的端口随机映射到宿主（较少用）"),
    ]
    for f, desc in rows:
        print(f"  {f:<24} {desc}")

    print("\n查看映射：docker port <容器>")

    from docker_check import docker_cli_available, docker_daemon_available
    if docker_cli_available() and docker_daemon_available():
        print("\n（已检测到 Docker 环境，可 docker run -d -p 8080:80 nginx 后访问 8080 验证）")
    else:
        print("\n（当前无 Docker 环境，仅讲解）")


def main():
    print(">> 端口映射原理\n")
    explain()
    forms()


if __name__ == "__main__":
    main()