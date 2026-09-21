# 文件用途：规则路由模式
# 演示把「分类」和「路由」分离的设计：分类节点写 category 字段，
# 条件边按 content_type 把输入分发到不同的处理链（商品咨询/退换货/投诉）。
# 对比几种 path_map 写法，并加入无条件 fallback 处理。

from typing import TypedDict

from langgraph.graph import StateGraph, END, START


class State(TypedDict):
    input_text: str
    content_type: str  # product / after_sale / complaint / other


# ---- 分类节点：规则分类 ----
def classify_node(state: State) -> dict:
    """根据关键字对内容分类，并确保覆盖四种类型（含兜底 other）。"""
    text = state["input_text"]
    if any(k in text for k in ["退货", "换货", "退款", "售后"]):
        ctype = "after_sale"
    elif any(k in text for k in ["投诉", "差评", "不满", "很生气"]):
        ctype = "complaint"
    elif any(k in text for k in ["价格", "规格", "库存", "优惠"]):
        ctype = "product"
    else:
        ctype = "other"   # 兜底分类
    return {"content_type": ctype}


# ---- 三条处理链 ----
def product_chain(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [商品咨询处理]"}


def aftersale_chain(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [退换货处理]"}


def complaint_chain(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [投诉处理]"}


def default_chain(state: State) -> dict:
    return {"input_text": state["input_text"] + " | [兜底：通用处理]"}


# ---- path_map 写法对比 ----
def route_v1(state: State) -> str:
    """写法1：直接返回节点名（最简单，省去映射表）。"""
    return {"product": "product_chain",
            "after_sale": "aftersale_chain",
            "complaint": "complaint_chain",
            "other": "default_chain"}.get(state["content_type"], "default_chain")


def route_v2(state: State) -> str:
    """写法2：if/else 显式判断 + 无条件 fallback。"""
    if state["content_type"] == "product":
        return "product_chain"
    if state["content_type"] == "after_sale":
        return "aftersale_chain"
    if state["content_type"] == "complaint":
        return "complaint_chain"
    return "default_chain"   # 无条件 fallback：任何未知类型走兜底


def build_graph(route_fn) -> "CompiledGraph":
    b = StateGraph(State)
    b.add_node("classify", classify_node)
    b.add_node("product_chain", product_chain)
    b.add_node("aftersale_chain", aftersale_chain)
    b.add_node("complaint_chain", complaint_chain)
    b.add_node("default_chain", default_chain)
    b.add_edge(START, "classify")

    mapping = {
        "product_chain": "product_chain",
        "aftersale_chain": "aftersale_chain",
        "complaint_chain": "complaint_chain",
        "default_chain": "default_chain",
    }
    b.add_conditional_edges("classify", route_fn, mapping)

    for chain in ["product_chain", "aftersale_chain", "complaint_chain", "default_chain"]:
        b.add_edge(chain, END)
    return b.compile()


def main() -> None:
    print("=" * 60)
    print("GraphFlow - 规则路由（content_type → 不同处理链）")
    print("=" * 60)

    samples = [
        "这款手机价格多少？有库存吗？",
        "收到货尺寸不对，我要退货。",
        "客服态度很差，我非常不满，投诉！",
        "随机内容，无关键字。",
    ]

    for label, route_fn in [("route_v1(直接返节点名)", route_v1), ("route_v2(if/else+fallback)", route_v2)]:
        print("\n--- 使用", label, "---")
        app = build_graph(route_fn)
        for text in samples:
            out = app.invoke({"input_text": text, "content_type": ""})
            print(f"  {out['content_type']:<11} -> {out['input_text'].split(' | ')[1]}")


if __name__ == "__main__":
    main()