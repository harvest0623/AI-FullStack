# -*- coding: utf-8 -*-
"""
Day04 - 01 Dockerfile 指令详解

逐条讲解常用 Dockerfile 指令及其对应"生成一个层"的概念。
离线可运行（纯讲解）。
"""


def instructions():
    print("常用指令与作用：\n")
    rows = [
        ("FROM python:3.11", "指定基础镜像（每条 Dockerfile 的第一条有效指令）"),
        ("WORKDIR /app", "设置工作目录，之后的相对路径基于此"),
        ("COPY a b", "把宿主文件 a 复制进镜像的 b 位置"),
        ("RUN pip install ...", "构建时执行命令（生成一个新层，适合装依赖/编译）"),
        ("ENV K=V", "设置环境变量"),
        ("EXPOSE 8000", "声明容器要监听 8000（文档性质，真正映射靠 -p/compose）"),
        ("CMD [python, app.py]", "容器启动时的默认命令（可被 run 覆盖）"),
        ("ENTRYPOINT [python]", "容器启动时固定的可执行程序（不可被 run 简单覆盖）"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd:<28} {desc}")


def layer_gen():
    print("\n" + "-" * 62)
    print("关键认识：几乎每条指令都会生成一个新的只读层")
    print("""  FROM      → 层0（基础镜像）
  RUN install→ 层1
  COPY 代码 → 层2
  CMD       → 层3（元数据）
  （容器运行时再叠加一个可写层）
""")


def cmd_ent():
    print("CMD vs ENTRYPOINT 的最常见组合写法：\n")
    print("  ENTRYPOINT [\"python\", \"app.py\"]   # 固定跑这个程序")
    print("  CMD        [\"--port\", \"8000\"]     # 默认参数，可被 docker run 附加参数覆盖")
    print("  → docker run myimg            # 等价 python app.py --port 8000")
    print("  → docker run myimg --port 9000# 等价 python app.py --port 9000")


def main():
    print(">> Dockerfile 指令详解\n")
    instructions()
    layer_gen()
    cmd_ent()
    print("\n  tips: 顺序影响缓存——变化少的放前面、多的放后面（见 Day02）。")


if __name__ == "__main__":
    main()