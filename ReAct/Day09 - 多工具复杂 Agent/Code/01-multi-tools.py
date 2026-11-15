"""
Day09 练习一：三工具 Agent
=============================
注册"搜索商品 / 计算 / 数据库查询"三工具, Mock Agent 按任务分派工具链,
最后综合 Observation 输出自然语言回答。

运行:
  python "Day09 - 多工具复杂 Agent/Code/01-multi-tools.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402
from llm import auto_llm, MockLLM, text, tool_call  # noqa: E402


# ---------- 三工具 ----------
@tool
def search_product(kw: str) -> str:
    """按关键词搜索商品并返回结果列表"""
    db = {"耳机": "无线降噪耳机 $199", "笔记本": "轻薄本 $899", "手表": "智能手表 $299"}
    return db.get(kw, f"未找到 {kw}")


@tool
def calc_total(prices: list) -> str:
    """对一组价格求和"""
    return f"{sum(prices):.2f}"


@tool
def query_stock(sku: str) -> str:
    """查询库存是否充足"""
    return "充足" if sku in "ABCD" else "缺货"


def big_decider(messages, tools=None):
    """模拟"模型决策": 看关键词决定用哪个工具链。"""
    user = messages[0]["content"]
    obs = [m["content"] for m in messages if m.get("role") == "tool"]
    if "耳机" in user and not obs:
        return tool_call("search_product", {"kw": "耳机"})
    if obs and obs[-1].startswith("无线降噪耳机"):
        return text("推荐无线降噪耳机, 价格 $199, 是同价位性价比之选。")
    if "总价" in user and not obs:
        return tool_call("search_product", {"kw": "笔记本"})
    return text("我不确定, 但可以帮你查询。")


def main() -> None:
    reg = ToolRegistry([search_product, calc_total, query_stock])
    llm = auto_llm(mock_decider=big_decider)

    messages = [{"role": "user", "content": "我想买一副耳机, 有什么推荐?"}]
    print("三工具 Agent 执行:\n")
    resp = llm.chat(messages, tools=reg.openai_tools())
    for tc in resp["tool_calls"]:
        r = reg.execute(tc["name"], **tc["arguments"])
        print(f"  调用 {tc['name']}({tc['arguments']}) -> {r}")
        messages.append({"role": "tool", "content": str(r)})
    final = llm.text(messages, tools=reg.openai_tools())
    print("\n✅ 最终回答:", final)


if __name__ == "__main__":
    main()