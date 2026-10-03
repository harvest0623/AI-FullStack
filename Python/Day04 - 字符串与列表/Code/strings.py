# 文件用途：字符串操作练习，演示创建/索引/切片/反转、格式化三种方式对比、encode/decode，用电商场景格式化商品信息
# 语法：python strings.py

# ============================================================
# 1. 字符串创建
# ============================================================
print("=== 1. 字符串创建 ===")
s1 = 'eshop'                      # 单引号
s2 = "eshop"                      # 双引号（等价）
s3 = """多行
字符串"""                          # 三引号（跨行）
s4 = r"C:\new\folder"             # 原始字符串（反斜杠不转义）
print(f"单引号: {s1}")
print(f"双引号: {s2}")
print(f"三引号: {s3!r}")
print(f"原始字符串: {s4}")         # 反斜杠保留

# 转义字符
print(f"转义: 换行\n制表符\t引号\"结束")

# ============================================================
# 2. 字符串不可变性
# ============================================================
print("\n=== 2. 字符串不可变性 ===")
s = "eshop"
# s[0] = "E"   # 报错：str 不支持项赋值
s = "E" + s[1:]  # 创建新字符串
print(f"修改后: {s}")   # Eshop

# ============================================================
# 3. 索引与切片
# ============================================================
print("\n=== 3. 索引与切片 ===")
s = "eshop-cli"
print(f"字符串: {s!r}")
print(f"s[0] = {s[0]!r}")          # 'e'（正索引）
print(f"s[-1] = {s[-1]!r}")        # 'i'（负索引）
print(f"s[1:4] = {s[1:4]!r}")      # 'sho'（左闭右开）
print(f"s[:5] = {s[:5]!r}")        # 'eshop'
print(f"s[6:] = {s[6:]!r}")        # 'cli'
print(f"s[::2] = {s[::2]!r}")      # 'eh-ci'（步长2）
print(f"s[::-1] = {s[::-1]!r}")    # 'ilc-pohse'（反转）

# eshop 场景：订单号切片
order_no = "ORD20260730001"
date_part = order_no[3:11]   # 20260730
seq_part = order_no[11:]     # 001
print(f"\n订单号 {order_no} -> 日期 {date_part}, 序号 {seq_part}")

# ============================================================
# 4. 字符串格式化三种方式对比
# ============================================================
print("\n=== 4. 字符串格式化对比 ===")
product_name = "iPhone 15"
price = 5999
discount = 0.85

# 方式一：% 格式化（旧，不推荐）
fmt1 = "商品: %s, 价格: %.2f, 折扣: %.2f%%" % (product_name, price, discount * 100)
print(f"%% 格式化: {fmt1}")

# 方式二：str.format()
fmt2 = "商品: {}, 价格: {:.2f}, 折扣: {:.2%}".format(product_name, price, discount)
print(f"format(): {fmt2}")

# 方式三：f-string（3.6+，推荐）
fmt3 = f"商品: {product_name}, 价格: {price:.2f}, 折扣: {discount:.2%}"
print(f"f-string:  {fmt3}")

# ============================================================
# 5. f-string 高级用法
# ============================================================
print("\n=== 5. f-string 高级用法 ===")
name = "iPhone"
price = 5999

# 对齐
print(f"右对齐: |{price:>10}|")
print(f"左对齐: |{price:<10}|")
print(f"居中:   |{price:^10}|")

# 填充
print(f"零填充: {price:010d}")
print(f"千分位: {price:,}")
print(f"千分位+小数: {price:,.2f}")

# 百分比
rate = 0.85
print(f"百分比: {rate:.2%}")

# 调试输出（3.8+）
x = 42
print(f"{x = }")              # x = 42
print(f"{price * 2 = }")      # price * 2 = 11998

# 表达式
qty = 3
print(f"总价: {price * qty:,}")

# ============================================================
# 6. encode / decode
# ============================================================
print("\n=== 6. encode/decode ===")
s = "eshop 商城"
b = s.encode("utf-8")        # str -> bytes
print(f"编码后: {b}")
s2 = b.decode("utf-8")       # bytes -> str
print(f"解码后: {s2}")
print(f"还原一致: {s == s2}")

# 不同编码
print(f"UTF-8 字节数: {len(s.encode('utf-8'))}")
print(f"GBK 字节数: {len(s.encode('gbk'))}")

# ============================================================
# 7. eshop 场景：格式化商品信息输出
# ============================================================
print("\n=== 7. eshop 商品信息格式化 ===")


def format_product(pid: int, name: str, price: float, stock: int) -> str:
    """格式化商品信息为一行报告。"""
    return (
        f"| {pid:04d} | {name:<12} | {price:>10,.2f} | {stock:>6} |"
    )


products = [
    (1, "iPhone 15", 5999.0, 50),
    (2, "MacBook Pro", 12999.0, 20),
    (3, "AirPods", 1999.0, 100),
]
# 表头
print(f"| {'ID':>4} | {'名称':<12} | {'单价':>10} | {'库存':>6} |")
print("|" + "-" * 6 + "|" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 8 + "|")
for pid, name, price, stock in products:
    print(format_product(pid, name, price, stock))

# ============================================================
# 8. eshop 场景：生成订单摘要
# ============================================================
print("\n=== 8. 订单摘要 ===")


def order_summary(order_id: int, items: list, discount: float = 1.0) -> str:
    """生成订单摘要字符串。"""
    total = sum(price * qty for _, price, qty in items)
    final = total * discount
    lines = [f"订单号: ORD{order_id:06d}"]
    for name, price, qty in items:
        lines.append(f"  - {name}: {price} x {qty} = {price * qty}")
    lines.append(f"小计: {total:,.2f}")
    lines.append(f"折扣: {discount:.2%}")
    lines.append(f"应付: {final:,.2f}")
    return "\n".join(lines)


items = [("iPhone 15", 5999, 2), ("AirPods", 1999, 1)]
print(order_summary(5001, items, discount=0.85))


if __name__ == "__main__":
    print("\n--- strings.py 演示结束 ---")
