# -*- coding: utf-8 -*-
"""
Day03 - 01 容器生命周期状态机

容器从创建到销毁会经历一系列状态：
Created → Running → Exited（Paused / Restarting 等中间态）。

用状态机演示 run/start/stop/restart/rm 如何推动状态变迁。
离线可运行。
"""


class Container:
    """极简容器生命周期模拟"""

    STATES = ["created", "running", "paused", "exited", "removed"]

    def __init__(self, name: str):
        self.name = name
        self.state = "created"

    def _trans(self, action: str, new_state: str):
        print(f"  {self.name}: {action:<12} {self.state:>9} → {new_state}")
        self.state = new_state

    def start(self):
        if self.state != "running":
            self._trans("docker start", "running")
        else:
            print(f"  {self.name}: 已在运行")

    def pause(self):
        if self.state == "running":
            self._trans("docker pause", "paused")

    def unpause(self):
        if self.state == "paused":
            self._trans("docker unpause", "running")

    def stop(self):
        if self.state in ("running", "paused"):
            self._trans("docker stop", "exited")

    def restart(self):
        if self.state == "exited":
            self._trans("docker start", "running")
            self._trans("docker restart", "running")

    def remove(self):
        if self.state == "exited":
            self._trans("docker rm", "removed")


def main():
    print(">> 容器生命周期状态机\n")
    c = Container("my-app")
    print("状态集合：created → running ⇄ paused / exited → removed\n")
    steps = [
        ("run", lambda: c.start()),
        ("stop", c.stop),
        ("start", c.start),
        ("pause", c.pause),
        ("unpause", c.unpause),
        ("stop", c.stop),
        ("rm", c.remove),
    ]
    for name, fn in steps:
        fn()

    print("\n  tips: 容器退出后仍在（Exited），需 docker rm 才真正删除数据层。")


if __name__ == "__main__":
    main()