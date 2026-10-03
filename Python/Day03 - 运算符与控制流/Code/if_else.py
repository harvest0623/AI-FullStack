# 文件用途：条件语句练习，演示 if/elif/else、嵌套、三元运算符，用电商订单状态与折扣计算
# 语法：python if_else.py

# ============================================================
# 1. 基础 if / else
# ============================================================
print("=== 1. 基础 if/else ===")
stock = 50
if stock > 0:
    print(f"库存 {stock}：有货")
else:
    print(f"库存 {stock}：缺货")

# ============================================================
# 2. if / elif / else 多分支
# ============================================================
print("\n=== 2. 多分支 if/elif/else ===")
score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 60:
    grade = "C"
else:
    grade = "D"
print(f"分数 {score}，等级 {grade}")

# ============================================================
# 3. 嵌套 if
# ============================================================
print("\n=== 3. 嵌套 if ===")
is_vip = True
order_total = 1200
if is_vip:
    if order_total >= 1000:
        print("VIP 用户且满 1000 元：享 7 折")
    else:
        print("VIP 用户但未满额：享 9 折")
else:
    if order_total >= 1000:
        print("普通用户满 1000 元：享 9 折")
    else:
        print("普通用户未满额：无折扣")

# ============================================================
# 4. 三元运算符（条件表达式）
# ============================================================
print("\n=== 4. 三元运算符 ===")
stock = 0
status = "有货" if stock > 0 else "缺货"
print(f"库存 {stock} -> {status}")

# 嵌套三元（可读性差，慎用）
level = 2
label = "高级" if level >= 3 else ("中级" if level == 2 else "初级")
print(f"等级 {level} -> {label}")

# ============================================================
# 5. eshop 场景：根据订单状态显示信息
# ============================================================
print("\n=== 5. eshop 订单状态显示 ===")


def show_order_status(status: str) -> str:
    """根据订单状态返回提示信息。"""
    if status == "pending":
        return "订单待付款，请尽快完成支付"
    elif status == "paid":
        return "订单已支付，等待商家发货"
    elif status == "shipped":
        return "订单已发货，请注意查收"
    elif status == "completed":
        return "订单已完成，期待您的评价"
    elif status == "cancelled":
        return "订单已取消"
    else:
        return f"未知状态: {status}"


for s in ["pending", "paid", "shipped", "completed", "cancelled", "unknown"]:
    print(f"  {s}: {show_order_status(s)}")

# ============================================================
# 6. eshop 场景：根据金额计算折扣
# ============================================================
print("\n=== 6. eshop 折扣计算 ===")


def calc_discount(total: float, vip_level: int = 0) -> float:
    """根据订单金额与 VIP 等级计算折后价。

    规则：
        VIP3+ 且满 1000 元 -> 7 折
        VIP2+ 且满 500 元  -> 8 折
        VIP1+              -> 9 折
        其他               -> 不打折
    """
    if vip_level >= 3 and total >= 1000:
        return total * 0.7
    elif vip_level >= 2 and total >= 500:
        return total * 0.8
    elif vip_level >= 1:
        return total * 0.9
    else:
        return total


# 测试多组数据
test_cases = [
    (1500, 3, "VIP3 满 1000"),
    (600, 2, "VIP2 满 500"),
    (300, 1, "VIP1"),
    (100, 0, "普通用户"),
    (1000, 2, "VIP2 但刚好满 500"),
]
for total, level, desc in test_cases:
    final = calc_discount(total, level)
    print(f"  {desc}: 原价 {total} -> 折后 {final}")

# ============================================================
# 7. 条件表达式与逻辑运算符组合
# ============================================================
print("\n=== 7. 组合条件 ===")
# 链式比较判断库存安全区间
stock = 50
if 10 <= stock <= 100:
    print(f"库存 {stock} 处于安全区间")
elif stock < 10:
    print(f"库存 {stock} 不足，需补货")
else:
    print(f"库存 {stock} 过高，注意积压")

# 用 and/or 组合多条件
category = "手机"
price = 2999
is_hot = (category == "手机") and (price < 3000)
print(f"是否热销: {is_hot}")

# 短路求值提供默认值
remark = "" or "无备注"
print(f"订单备注: {remark}")


if __name__ == "__main__":
    print("\n--- if_else.py 演示结束 ---")
