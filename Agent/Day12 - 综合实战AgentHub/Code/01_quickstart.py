# -*- coding: utf-8 -*-
"""
Day12 - 01 Quickstart：3 步跑通一个 Agent

演示最小用法：
  1. 创建 AgentHub 并注册工具
  2. run() 一个任务
  3. 查看轨迹日志
"""

from agenthub import AgentHub, default_tools


def main():
    print("=" * 56)
    print("AgentHub Quickstart：查库存 + 查价格 + 下单")
    print("=" * 56)

    # 步骤 1：创建 Agent 并注册工具
    print("\n[步骤 1] 注册工具：")
    hub = AgentHub()
    hub.register_tools(default_tools())

    # 步骤 2：运行任务（place_order 是高危工具，这里给自动批准的审批函数）
    print("\n[步骤 2] 运行任务：")
    hub.gate.approve_fn = lambda req: True  # 演示环境自动批准
    result = hub.run("帮我查 A100 的库存和价格，然后下单 10 个")
    print(f"\n最终回答：{result}")

    # 步骤 3：查看轨迹日志
    print("\n[步骤 3] 轨迹日志：")
    print(hub.logger.render())


if __name__ == "__main__":
    main()
