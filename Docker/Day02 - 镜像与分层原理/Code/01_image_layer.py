# -*- coding: utf-8 -*-
"""
Day02 - 01 镜像分层模型

详解 Docker 镜像的分层存储：
1. 镜像由多个只读层（layer）叠加而成
2. 容器启动时在最上层加一个可写层（Copy-on-Write）
3. 读取时层层查找，写时复制（新增命令到可写层）
4. 层可复用、可共享 → 省磁盘、快下载

离线可运行（纯讲解 + 简单模型模拟）。
"""


def layer_diagram():
    print("一、镜像分层的直观模型\n")
    print("""  ┌─────────────────────────────────────┐
  │  可写层（容器运行时才有，可读写）← 新增/修改/删除都在这里
  ├─────────────────────────────────────┤
  │  层3：CMD（启动命令）                     │  只读
  ├─────────────────────────────────────┤
  │  层2：COPY 应用代码                     │  只读
  ├─────────────────────────────────────┤
  │  层1：安装 Python 依赖                  │  只读
  ├─────────────────────────────────────┤
  │  层0：基础镜像（如 python:3.11）        │  只读
  └─────────────────────────────────────┘
  向下层层只读共享，向上新增可写层 = 一个容器
""")


def simulate_layers():
    print("二、写时复制（Copy-on-Write）模拟\n")
    base_layers = ["os", "python", "deps", "app_code"]
    print(f"  基础镜像层（只读）：{base_layers}")

    # 容器层：可写
    container_layer: dict[str, str] = {}

    def read_file(path: str) -> str | None:
        """先查可写层，再向下查只读层"""
        if path in container_layer:
            return container_layer[path] + "（来自可写层）"
        for layer in base_layers:
            fake = f"{layer}:/etc/nginx.conf"
            if path.endswith(layer):
                return "（来自只读层）"
        return None

    # 删除操作会在容器层打标记（whiteout）
    print("\n  修改 /etc/nginx.conf → 复制到可写层后再改（原底层不变）")
    container_layer["/etc/nginx.conf"] = "server_name myapp;"
    print("  读取  /etc/nginx.conf →", read_file("/etc/nginx.conf"))
    base_layers_new = list(base_layers)
    print(f"  底层（仍只读，未被动过）: {base_layers_new}")

    print("\n  ⇒ 容器删除/修改不会影响镜像层，删除容器后镜像依旧干净如初。")


def real_hint():
    from docker_check import docker_cli_available, docker_daemon_available
    print("\n真实命令（Docker 就绪时）：")
    print("  docker image inspect python:3.11   # 查看镜像的层列表")
    if docker_cli_available() and docker_daemon_available():
        print("  （已检测到 Docker 环境，可执行上面命令查看真实分层）")
    else:
        print("  （当前无 Docker 环境，仅讲解）")


def main():
    print(">> 镜像分层模型\n")
    layer_diagram()
    simulate_layers()
    real_hint()


if __name__ == "__main__":
    main()