# -*- coding: utf-8 -*-
"""
Day09 - client_agent.py  消费 server_shop 的 Agent 客户端（离线模拟）

演示一个完整 Agent 闭环：发现 server_shop 的工具 → 决策 → 调用 → 回填回复。
用规则函数代替真实 LLM，说明结构；真实环境换成 LLM tool calling 即可。

离线可运行（无需 mcp 包）。
"""

# —— 模拟 server_shop 的能力（含路由与执行） ——
SHOP = {}

# 商品库存（与 server_shop.py 逻辑一致，便于离线演示）
_ITEMS = {
    "apple": {"name": "苹果", "price": 5.0, "stock": 10},
    "banana": {"name": "香蕉", "price": 3.0, "stock": 20},
}


def list_items():
    return "\n".join(f"{k}: {v['name']} ￥{v['price']} 库存{v['stock']}"
                     for k, v in _ITEMS.items())


def order_item(item, qty):
    it = _ITEMS.get(item)
    if not it:
        raise ValueError(f"没有商品『{item}』")
    if qty <= 0:
        raise ValueError("数量必须为正整数")
    if it["stock"] < qty:
        raise ValueError(f"库存不足（{item} 库存 {it['stock']}）")
    _ITEMS[item]["stock"] -= qty
    return f"下单成功：{it['name']} x{qty}，共 ￥{it['price'] * qty:.2f}"


TOOLS = {
    "list_items": {"server": "shop", "fn": lambda *a, **k: list_items()},
    "order_item": {"server": "shop", "fn": order_item},
}


def discover():
    print(f"  [发现] MCP 工具面 → {list(TOOLS.keys())}")


def decide(query):
    """极简规则决策：识别是看商品还是下单。"""
    if "看看" in query or "都有什么" in query or "商品" in query:
        return "list_items", {}
    if "下" in query or "买" in query or "订单" in query:
        # 解析「数量」与「商品」——简化：取最后一个数字作 qty，首个中文名作商品
        import re
        qty_match = re.search(r"(\d+)\s*(个|斤|件)?", query)
        qty = int(qty_match.group(1)) if qty_match else 1
        # 从库存里找出现在句子中的商品
        for key in _ITEMS:
            if key in query:
                return "order_item", {"item": key, "qty": qty}
        return "order_item", {"item": "apple", "qty": qty}
    return None, None


def agent_loop(query):
    print(f"  用户：『{query}』")
    discover()
    name, args = decide(query)
    if name is None:
        print("  [决策] 无需调用，直接回答。\n")
        return
    print(f"  [决策] 调用 {name} {args}")
    try:
        result = TOOLS[name]["fn"](**args)
        print(f"  [执行] {TOOLS[name]['server']} 返回 → {result}")
        print(f"  [回复] {result}\n")
    except ValueError as e:
        print(f"  [执行] Server 报错 → {e}")
        print(f"  [回复] 已把失败原因反馈给用户：{e}\n")


def main():
    print(">> Agent + server_shop 闭环（离线模拟）\n")
    agent_loop("店里都有什么商品？")
    agent_loop("帮我下 2 个苹果的订单")
    agent_loop("买 20 个香蕉")
    print("  note: 换成真实 LLM 后，decision 由模型完成，其余结构一致。")


if __name__ == "__main__":
    main()