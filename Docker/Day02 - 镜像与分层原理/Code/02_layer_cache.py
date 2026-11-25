# -*- coding: utf-8 -*-
"""
Day02 - 02 层缓存与复用

Docker 组件层的意义不仅在于概念，更在于工程收益：
1. 层缓存（Layer Cache）：已构建且指令未变的层直接复用，无需重做
2. 依赖层在前、业务代码在后的顺序 → 改代码只重建最上层
3. 多个镜像共享公共底层 → 省磁盘、快拉取

用"指令序列 → 判断是否命中缓存"来模拟构建缓存逻辑。离线可运行。
"""


class LayerStore:
    """模拟 docker 的本地层存储（以指令+内容 hash 作为层标识）"""

    def __init__(self):
        self.cached: dict[str, str] = {}

    def hash(self, instruction: str, content: str):
        import hashlib
        return hashlib.md5((instruction + "|" + content).encode()).hexdigest()[:8]

    def build(self, instructions: list[tuple[str, str]]) -> list[str]:
        """执行一串指令（instruction, content），返回每层的状态"""
        results = []
        for inst, content in instructions:
            h = self.hash(inst, content)
            if h in self.cached:
                results.append(f"[缓存命中] {inst}: {h}（{self.cached[h]}）→ 复用，不重复执行")
            else:
                self.cached[h] = content
                results.append(f"[重建]      {inst}: {h}（{content}）→ 执行并缓存")
        return results


def default_dockerfile(order: str):
    """常规 Dockerfile：先把依赖装好，最后 COPY 业务代码"""
    instructions = [
        ("FROM python:3.11", "base"),
        ("COPY requirements.txt .", f"requirements-{order}"),
        ("RUN pip install -r requirements.txt", f"deps-{order}"),
        ("COPY app.py .", f"app-{order}"),
        ("CMD [python, app.py]", "cmd"),
    ]
    return instructions


def main():
    print(">> 层缓存与复用\n")
    store = LayerStore()

    print("第一次构建（全部无缓存）：")
    for line in store.build(default_dockerfile("v1")):
        print(f"  {line}")

    print("\n改业务代码 app.py 后再构建（v2，依赖没变）：")
    for line in store.build(default_dockerfile("v2")):
        print(f"  {line}")
    print("  → 前三层命中缓存，只有『COPY app.py』这层重建，秒级完成")

    print("\n结论：把『变化慢的放前面、变化快的放后面』，能最大化层缓存收益。")
    print("  tips: Dockerfile 顺序不当（先 COPY 代码再装依赖）会让每次改动都全量重建。")


if __name__ == "__main__":
    main()