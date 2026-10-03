# -*- coding: utf-8 -*-
"""
Day09 - 01 完整案例架构讲解

三层结构：业务 Server（工具/资源/提示词）+ Agent 客户端 + 业务数据。
展示在线商店场景的模块划分。

离线可运行（纯讲解）。
"""


def layers():
    print("完整案例架构：\n")
    print("""  ┌──────────────────────────────────────────────┐
  │ Agent 客户端 (client_agent.py)                 │
  │   收集工具 → 决策 → call_tool → 回填 → 回复    │
  ├──────────────────────────────────────────────┤
  │ MCP Server (server_shop.py)                   │
  │   工具: list_items / order_item              │
  │   资源: inventory://items（商品清单）          │
  │   提示词: place_order_guide（下单说明）        │
  ├──────────────────────────────────────────────┤
  │ 业务数据（内存 mock 商品/库存）                │
  └──────────────────────────────────────────────┘
  """)


def primitives():
    print("三类原语各司其职：\n")
    rows = [
        ("工具", "list_items（列商品）、order_item（下单+校验）", "让 Agent 动手"),
        ("资源", "inventory://items（商品/库存清单）", "让 Agent 读清单"),
        ("提示词", "place_order_guide（下单流程）", "复用下单话术"),
    ]
    for kind, what, role in rows:
        print(f"  ■ {kind:<3} {what}\n      角色：{role}\n")


def flow():
    print("一次下单闭环：\n")
    steps = [
        "用户：『买 2 个苹果』",
        "Agent 发现订单类工具 → 决策调用 order_item('apple', 2)",
        "Server 校验库存/数量 → 返回订单结果",
        "Agent 回填结果 → 回复用户『下单成功』",
    ]
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")


def main():
    print(">> 完整案例架构\n")
    layers()
    primitives()
    flow()
    print("\n  tips: 同一套 Server 结构，换成真实数据库/API 即为生产实现。")


if __name__ == "__main__":
    main()