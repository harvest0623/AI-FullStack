# -*- coding: utf-8 -*-
"""
Day09 - server_shop.py  完整业务 Server（在线商店）

提供工具（列商品/下单）、资源（商品清单）、提示词（下单说明），
是 Day09 综合实战的服务端模板。

运行（需安装 mcp）：
    python server_shop.py
或调试：uv run mcp dev server_shop.py

未安装 mcp 时，可直接阅读本文件理解工具/资源/提示词的写法，
或运行离线版 client_agent.py 看 Agent 如何消费。
"""

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("未检测到 mcp SDK，请先运行: pip install mcp")
    raise SystemExit(1)

mcp = FastMCP("Shop")

# —— 内存 mock 商品 ——
_ITEMS = {
    "apple": {"name": "苹果", "price": 5.0, "stock": 10},
    "banana": {"name": "香蕉", "price": 3.0, "stock": 20},
    "orange": {"name": "橙子", "price": 4.0, "stock": 0},
}


# ---------- 工具 ----------
@mcp.tool()
def list_items() -> str:
    """列出所有在售商品及其价格、库存。"""
    lines = [f"{k}: {v['name']} ￥{v['price']} 库存{v['stock']}"
             for k, v in _ITEMS.items()]
    return "\n".join(lines)


@mcp.tool()
def order_item(item: str, qty: int) -> str:
    """为指定商品下单；校验商品存在、库存充足、数量为正。"""
    if qty <= 0:
        raise ValueError("数量必须为正整数")
    it = _ITEMS.get(item)
    if not it:
        raise ValueError(f"没有商品『{item}』")
    if it["stock"] < qty:
        raise ValueError(f"库存不足（{item} 库存 {it['stock']}）")
    _ITEMS[item]["stock"] -= qty
    return f"下单成功：{it['name']} x{qty}，共 ￥{it['price'] * qty:.2f}"


# ---------- 资源 ----------
@mcp.resource("inventory://items")
def get_inventory() -> str:
    """商品与库存清单（JSON 字符串）。"""
    import json
    return json.dumps(_ITEMS, ensure_ascii=False)


# ---------- 提示词 ----------
@mcp.prompt()
def place_order_guide() -> str:
    """下单流程说明（复用模板）。"""
    return ("下单步骤：1) list_items 查看商品；2) order_item 指定商品与数量。"
            "注意数量为正整数，且需确认库存充足。")


if __name__ == "__main__":
    mcp.run()