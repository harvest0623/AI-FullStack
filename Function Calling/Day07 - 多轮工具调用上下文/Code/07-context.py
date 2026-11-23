"""
Day07 多轮工具调用上下文
=======================
演示多轮(多次工具调用)之间如何"带着上下文"——每轮结果都留在对话历史里,
后续模型决策可以参考之前的中间结果, 形成有状态的多步处理。

场景: 订披萨流程
  1. 查菜单(拿到可选披萨与价格)
  2. 按预算选择 -> 下单选一款
  3. 统计需要多少份(根据人数)
规则 planner 依据"对话历史里已有结果"逐步推进, 体现上下文驱动。

运行:
  python "Day07 - 多轮工具调用上下文/Code/07-context.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec,
)


MENU = {"玛格丽特": 58, "海鲜至尊": 88, "素食": 68}


def get_menu() -> dict:
    return MENU


def place_order(flavor: str, count: int) -> str:
    if flavor not in MENU:
        return f"无此口味: {flavor}"
    return f"已下单 {count} 份 {flavor}, 单价 {MENU[flavor]} 元, 共 {MENU[flavor]*count} 元"


def make_reg():
    reg = FunctionRegistry()
    reg.add(FunctionSpec("get_menu", "查看菜单与价格",
                         {"properties": {}}, get_menu))
    reg.add(FunctionSpec("place_order", "下单指定口味与数量",
                         {"properties": {"flavor": {"type": "string"},
                                         "count": {"type": "integer"}},
                          "required": ["flavor", "count"]}, place_order))
    return reg


def main() -> None:
    reg = make_reg()
    print("可用工具:", reg.names())
    print("菜单:", MENU)

    def planner(messages, tools):
        # 依据对话历史中的工具结果逐步推进(多轮上下文)
        tool_msgs = [m for m in messages if m["role"] == "tool"]

        # 第 1 步: 还没查过菜单 -> 先调 get_menu
        if not any(m["name"] == "get_menu" for m in tool_msgs):
            return ("call", [{"name": "get_menu", "args": {}}])

        # 第 2 步: 已查菜单、但还没下单 -> 用户预算内下单
        if not any(m["name"] == "place_order" for m in tool_msgs):
            # 从菜单结果里挑一个价格适中的
            menu_content = next(m["content"] for m in reversed(tool_msgs)
                                if m["name"] == "get_menu")
            return ("call", [{"name": "place_order",
                              "args": {"flavor": "玛格丽特", "count": 2}}])

        # 第 3 步: 已下单 -> 汇总最终结果
        last = tool_msgs[-1]
        return ("text", f"订单完成: {last['content']}")

    llm = FunctionCallingLLM(plan=planner)
    print("\n" + "=" * 60)
    print("用户: '帮我订 2 份玛格丽特'")
    final = llm.chat_with_tools("帮我订 2 份玛格丽特", reg)
    print("最终回答:", final)
    assert "116" in final  # 58*2
    assert "订单完成" in final

    print("\n多轮上下文断言通过 ✓")


if __name__ == "__main__":
    main()