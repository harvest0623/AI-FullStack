# -*- coding: utf-8 -*-
"""
Day06 - 03 Compose 常用命令

管理整个服务栈的组合命令，以及如何查看状态/日志/停止。
离线可运行（纯讲解）。
"""


def commands():
    print("compose 常用命令：\n")
    rows = [
        ("docker compose up -d", "拉取/构建并后台启动整个服务栈"),
        ("docker compose ps", "查看当前服务栈的容器状态"),
        ("docker compose logs -f", "跟踪所有服务的日志"),
        ("docker compose logs web", "只看某服务的日志"),
        ("docker compose exec web bash", "进入某服务的容器"),
        ("docker compose stop", "按依赖顺序停止服务"),
        ("docker compose down", "停止并移除容器/网络（保留卷）"),
        ("docker compose down -v", "停止并连命名卷一起删除（慎用）"),
        ("docker compose build", "重新构建镜像"),
        ("docker compose restart", "重启服务栈"),
    ]
    for cmd, desc in rows:
        p = cmd.replace("docker compose,", "docker compose").replace("，ps", " ps")
        print(f"  {cmd:<30} {desc}")


def life():
    print("\n生命周期小口诀：\n")
    print("  up 建起 → 干活 → logs 看 → stop 停 → down 拆（del）")
    print("  -d 后台、-f 跟日志、exec 进入、down -v 才删数据")


def main():
    print(">> Compose 常用命令\n")
    commands()
    life()


if __name__ == "__main__":
    main()