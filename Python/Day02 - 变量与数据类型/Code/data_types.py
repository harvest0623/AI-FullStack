# 文件用途：数据类型练习，演示 int 任意精度、float 精度陷阱、bool 运算、None 判断、Decimal 金额计算
# 语法：python data_types.py

from decimal import Decimal, getcontext

# ============================================================
# 1. int 整数：任意精度，无溢出
# ============================================================
print("=== 1. int 任意精度 ===")
big = 10 ** 100   # 10 的 100 次方
print(f"10^100 = {big}")
print(f"位数: {len(str(big))}")

# 不同进制表示
print(f"二进制 0b11111111 = {0b11111111}")    # 255
print(f"八进制 0o377 = {0o377}")               # 255
print(f"十六进制 0xff = {0xff}")               # 255

# 下划线分隔提升可读性（3.6+）
population = 1_000_000
price = 5_999
print(f"下划线分隔: population={population}, price={price}")

# 整数运算
print(f"7 // 2 = {7 // 2}（整除）")
print(f"7 % 2 = {7 % 2}（取余）")
print(f"2 ** 10 = {2 ** 10}（幂）")
print(f"divmod(7, 2) = {divmod(7, 2)}（商和余）")
print(f"abs(-5) = {abs(-5)}（绝对值）")

# ============================================================
# 2. float 浮点数：精度陷阱
# ============================================================
print("\n=== 2. float 精度陷阱 ===")
print(f"0.1 + 0.2 = {0.1 + 0.2}")
print(f"0.1 + 0.2 == 0.3 -> {0.1 + 0.2 == 0.3}")

# round 四舍五入（但无法根治精度问题）
print(f"round(0.1 + 0.2, 1) = {round(0.1 + 0.2, 1)}")

# 多次累加的误差
total = 0.0
for _ in range(10):
    total += 0.1
print(f"0.1 累加 10 次 = {total}（应为 1.0）")

# ============================================================
# 3. Decimal 精确金额计算（eshop 场景）
# ============================================================
print("\n=== 3. Decimal 金额计算 ===")
# 关键：用字符串初始化 Decimal，避免 float 精度问题
price1 = Decimal("0.1")
total_decimal = price1 + price1 + price1
print(f"Decimal('0.1') * 3 = {total_decimal}")
print(f"等于 0.3? {total_decimal == Decimal('0.3')}")

# eshop 场景：购物车金额精确计算
cart = [
    ("iPhone 15", Decimal("5999.00"), 2),
    ("AirPods Pro", Decimal("1999.00"), 1),
    ("保护壳", Decimal("99.50"), 3),
]
subtotal = sum(Decimal(qty) * Decimal(price) for _, price, qty in cart)
print(f"购物车小计: {subtotal}")

# 设置精度后做除法
getcontext().prec = 6
discount = subtotal * Decimal("0.85")
print(f"85 折后价: {discount}")

# ============================================================
# 4. bool 布尔：是 int 的子类
# ============================================================
print("\n=== 4. bool 运算 ===")
print(f"True == 1: {True == 1}")
print(f"False == 0: {False == 0}")
print(f"True + True = {True + True}")
print(f"isinstance(True, int): {isinstance(True, int)}")

# eshop 场景：用 bool 统计库存状态
stock_status = [True, False, True, True, False]   # True=有货
in_stock_count = sum(stock_status)
print(f"有货商品数: {in_stock_count} / {len(stock_status)}")

# ============================================================
# 5. None 空值判断
# ============================================================
print("\n=== 5. None 判断 ===")
# None 表示"没有值"，既不是 0 也不是空字符串
order_remark = None
print(f"order_remark = {order_remark}")
print(f"order_remark is None: {order_remark is None}")
print(f"order_remark == 0: {order_remark == 0}")
print(f"order_remark == '': {order_remark == ''}")

# eshop 场景：未填写备注的订单
def get_remark(order_id: int):
    """模拟查询订单备注，无备注返回 None。"""
    remarks = {5001: "加急", 5002: None}
    return remarks.get(order_id)


for oid in [5001, 5002, 5003]:
    r = get_remark(oid)
    if r is None:
        print(f"订单 {oid}: 无备注")
    else:
        print(f"订单 {oid}: {r}")

# ============================================================
# 6. 浮点数比较：math.isclose
# ============================================================
print("\n=== 6. 浮点数比较 ===")
import math
a = 0.1 + 0.2
b = 0.3
print(f"a == b: {a == b}")
print(f"math.isclose(a, b): {math.isclose(a, b)}")


if __name__ == "__main__":
    print("\n--- data_types.py 演示结束 ---")
