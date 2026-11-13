"""
Day03 练习二：自定义业务工具
==============================
用 @tool 定义「订单查询」「汇率换算」两个业务工具,
注册到 ToolRegistry, 打印各自的 openai 参数并执行。

运行:
  python "Day03 - 工具定义与注册/Code/02-custom-tool.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402


# 内置一个"假数据库", 模拟订单
ORDERS = {"A100": {"item": "Phone", "qty": 2, "total": 13998.0},
          "A200": {"item": "Laptop", "qty": 1, "total": 8999.0}}


@tool
def get_order(order_id: str) -> str:
    """按订单号查询订单详情(以字典字符串返回)"""
    data = ORDERS.get(order_id)
    return str(data) if data else f"未找到订单 {order_id}"


@tool
def convert_currency(amount: float, to: str = "USD") -> str:
    """把金额从 CNY 换算为 USD(简化汇率 7.2)"""
    rate = 7.2
    return f"{amount * rate:.2f} {to}"


def main() -> None:
    reg = ToolRegistry()
    reg.add(get_order)
    reg.add(convert_currency)

    print("注册的工具:", reg.names())
    print("\nOpenAI tools 参数:")
    import json
    print(json.dumps(reg.openai_tools(), ensure_ascii=False, indent=2))
    print()
    # 执行
    print("执行 get_order('A100')  :", reg.execute("get_order", order_id="A100"))
    print("执行 convert_currency(9.9):", reg.execute("convert_currency", amount=9.9, to="USD"))
    print("无效工具:", reg.execute("nope", x=1) if False else "(执行前应检查名称, 避免 KeyError)")


if __name__ == "__main__":
    main()