# -*- coding: utf-8 -*-
"""
Day07 - 01 为什么需要数据卷

容器的可写层随容器删除而消失，所以数据库/应用数据要放到容器外的"卷"里持久化。

用模拟演示："写进容器可写层" vs "写进命名卷"在删容器后的差异。
离线可运行。
"""


def scenario():
    print("问题：容器删除，数据会丢\n")
    print("  场景：某容器写了一些数据，然后 docker rm 把它删了")
    print("  容器可写层的文件 → 随之删除 → 数据丢失 ✗")
    print("  数据卷里的文件  → 卷由 Docker 管理、独立存活 → 数据保留 ✓\n")


def simulate():
    # 模拟"卷"的持久化语义
    named_volume = {"todos": ["买牛奶", "写日报"]}

    print("卷的语义演示：")
    print(f"  卷当前内容：{named_volume['todos']}")

    # 容器往卷写
    named_volume["todos"].append("学习 Docker")
    print(f"  容器往卷追加后：{named_volume['todos']}")

    # 删除容器（用新容器实例接管同一卷）
    print("  （删除旧容器，用新容器挂载同一个卷）")
    new_container_view = named_volume["todos"]
    print(f"  新容器看到的卷：{new_container_view}  → 数据还在 ✓")


def main():
    print(">> 为什么需要数据卷\n")
    scenario()
    simulate()
    print("\n  tips: 卷适合持久数据（数据库、上传文件、模型缓存等）。")


if __name__ == "__main__":
    main()