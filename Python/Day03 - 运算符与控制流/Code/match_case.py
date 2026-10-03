# 文件用途：match-case 模式匹配练习，覆盖基本匹配、字面量、变量绑定、序列解构、类模式（需 Python 3.10+）
# 语法：python match_case.py

import sys

# 确认 Python 版本 >= 3.10
if sys.version_info < (3, 10):
    print("本脚本需要 Python 3.10+ 才能使用 match-case 语法")
    sys.exit(1)

# ============================================================
# 1. 基本匹配（字面量）
# ============================================================
print("=== 1. 基本字面量匹配 ===")


def describe_status(status: str) -> str:
    """根据订单状态返回描述。"""
    match status:
        case "pending":
            return "待付款"
        case "paid":
            return "已付款"
        case "shipped":
            return "已发货"
        case "completed":
            return "已完成"
        case "cancelled":
            return "已取消"
        case _:
            return f"未知状态: {status}"


for s in ["pending", "paid", "shipped", "completed", "cancelled", "unknown"]:
    print(f"  {s} -> {describe_status(s)}")

# ============================================================
# 2. 或模式 | 与守卫 guard
# ============================================================
print("\n=== 2. 或模式与守卫 ===")


def classify_number(n: int) -> str:
    """对数字分类。"""
    match n:
        case 0:
            return "零"
        case x if x > 0:        # 守卫：附加条件
            return "正数"
        case x if x < 0:
            return "负数"


for n in [0, 5, -3]:
    print(f"  {n} -> {classify_number(n)}")

# 或模式：多个值共用一个分支
def classify_vip(level: int) -> str:
    match level:
        case 1 | 2:
            return "普通会员"
        case 3 | 4:
            return "高级会员"
        case 5:
            return "至尊会员"
        case _:
            return "非会员"


for lv in [1, 3, 5, 0]:
    print(f"  VIP{lv} -> {classify_vip(lv)}")

# ============================================================
# 3. 变量绑定与序列解构
# ============================================================
print("\n=== 3. 序列解构 ===")


def process_point(point) -> str:
    """处理二维坐标点。"""
    match point:
        case (0, 0):
            return "原点"
        case (0, y):           # 绑定 y
            return f"y 轴上, y={y}"
        case (x, 0):
            return f"x 轴上, x={x}"
        case (x, y):
            return f"普通点 ({x}, {y})"


for p in [(0, 0), (0, 5), (3, 0), (2, 4)]:
    print(f"  {p} -> {process_point(p)}")

# 星号解包：匹配任意长度序列
def handle_command(cmd) -> str:
    match cmd:
        case ["quit"]:
            return "退出"
        case ["add", item]:
            return f"添加商品: {item}"
        case ["add", *items]:   # 多个商品
            return f"批量添加: {items}"
        case ["remove", item]:
            return f"删除商品: {item}"
        case [cmd_name, *args]:
            return f"命令 {cmd_name}, 参数 {args}"
        case _:
            return "未知命令"


for c in [["quit"], ["add", "iPhone"], ["add", "iPhone", "MacBook", "AirPods"], ["list", "all"]]:
    print(f"  {c} -> {handle_command(c)}")

# ============================================================
# 4. 类模式（匹配对象属性）
# ============================================================
print("\n=== 4. 类模式 ===")


class Product:
    """eshop 商品数据模型。"""

    def __init__(self, id: int, name: str, price: float, stock: int, category: str):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category


def describe_product(p: Product) -> str:
    """根据商品属性分类描述。"""
    match p:
        case Product(stock=0):
            return f"{p.name}：缺货"
        case Product(price=price, category="手机") if price > 5000:
            return f"{p.name}：高端手机"
        case Product(category="手机"):
            return f"{p.name}：普通手机"
        case Product(category=cat):
            return f"{p.name}：{cat}类商品"


products = [
    Product(1001, "iPhone 15 Pro", 9999, 50, "手机"),
    Product(1002, "Redmi Note", 1299, 100, "手机"),
    Product(1003, "MacBook Air", 7999, 0, "笔记本"),
    Product(1004, "鼠标垫", 29, 200, "配件"),
]
for p in products:
    print(f"  {describe_product(p)}")

# ============================================================
# 5. eshop 场景：根据订单状态执行不同处理逻辑
# ============================================================
print("\n=== 5. eshop 订单状态分发 ===")


def handle_order(order) -> str:
    """根据订单数据结构匹配并执行处理逻辑。

    order 可以是：
        ("pending", order_id)
        ("paid", order_id, amount)
        ("shipped", order_id, tracking_no)
        {"status": "completed", "id": ..., "rating": ...}
    """
    match order:
        case ("pending", oid):
            return f"订单 {oid}：待付款，发送催付提醒"
        case ("paid", oid, amount):
            return f"订单 {oid}：已支付 {amount} 元，通知仓库发货"
        case ("shipped", oid, tracking):
            return f"订单 {oid}：已发货，运单号 {tracking}"
        case {"status": "completed", "id": oid, "rating": rating}:
            return f"订单 {oid}：已完成，评分 {rating} 星"
        case {"status": "cancelled", "id": oid}:
            return f"订单 {oid}：已取消，退款处理中"
        case _:
            return "无法识别的订单格式"


orders = [
    ("pending", 5001),
    ("paid", 5002, 299.5),
    ("shipped", 5003, "SF1234567890"),
    {"status": "completed", "id": 5004, "rating": 5},
    {"status": "cancelled", "id": 5005},
    ("unknown", 9999),
]
for o in orders:
    print(f"  {o} -> {handle_order(o)}")


if __name__ == "__main__":
    print("\n--- match_case.py 演示结束 ---")
