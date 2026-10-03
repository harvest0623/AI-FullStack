# 文件用途：列表推导式练习，演示基本推导式/条件过滤/嵌套/矩阵展平，对比 for 循环写法，用电商场景提取商品数据
# 语法：python list_comprehension.py

# ============================================================
# 1. 基本列表推导式
# ============================================================
print("=== 1. 基本推导式 ===")
# 语法: [表达式 for 变量 in 可迭代对象]
squares = [x ** 2 for x in range(1, 6)]
print(f"平方: {squares}")   # [1, 4, 9, 16, 25]

doubles = [x * 2 for x in range(5)]
print(f"翻倍: {doubles}")   # [0, 2, 4, 6, 8]

# 对比 for 循环写法
squares_for = []
for x in range(1, 6):
    squares_for.append(x ** 2)
print(f"for 循环写法: {squares_for}")
print(f"两者相等: {squares == squares_for}")

# ============================================================
# 2. 带条件过滤
# ============================================================
print("\n=== 2. 带条件过滤 ===")
# 语法: [表达式 for 变量 in 可迭代对象 if 条件]
nums = range(1, 11)
evens = [x for x in nums if x % 2 == 0]
print(f"偶数: {evens}")     # [2, 4, 6, 8, 10]

# 带表达式的过滤
even_squares = [x ** 2 for x in nums if x % 2 == 0]
print(f"偶数的平方: {even_squares}")   # [4, 16, 36, 64, 100]

# 对比 for 循环
even_squares_for = []
for x in nums:
    if x % 2 == 0:
        even_squares_for.append(x ** 2)
print(f"for 循环写法: {even_squares_for}")

# ============================================================
# 3. 带条件表达式（三元）
# ============================================================
print("\n=== 3. 条件表达式 ===")
# 表达式本身也可以是三元
labels = ["偶" if x % 2 == 0 else "奇" for x in range(5)]
print(f"奇偶标签: {labels}")   # ['偶', '奇', '偶', '奇', '偶']

# eshop 场景：库存状态
stocks = [50, 0, 30, 0, 100]
status = ["有货" if s > 0 else "缺货" for s in stocks]
print(f"库存状态: {status}")

# ============================================================
# 4. 嵌套循环推导式
# ============================================================
print("\n=== 4. 嵌套循环 ===")
# 语法: [表达式 for x in seq1 for y in seq2]
# 等价于两层 for 循环
pairs = [(x, y) for x in range(2) for y in range(2)]
print(f"组合对: {pairs}")   # [(0,0), (0,1), (1,0), (1,1)]

# 九九乘法表（部分）
table = [f"{x}x{y}={x*y}" for x in range(1, 4) for y in range(1, x + 1)]
print(f"乘法表: {table}")

# 对比 for 循环
pairs_for = []
for x in range(2):
    for y in range(2):
        pairs_for.append((x, y))
print(f"for 循环写法: {pairs_for}")

# ============================================================
# 5. 矩阵展平
# ============================================================
print("\n=== 5. 矩阵展平 ===")
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
# 推导式展平
flat = [cell for row in matrix for cell in row]
print(f"展平: {flat}")   # [1, 2, 3, 4, 5, 6, 7, 8, 9]

# 对比 for 循环
flat_for = []
for row in matrix:
    for cell in row:
        flat_for.append(cell)
print(f"for 循环写法: {flat_for}")

# 提取矩阵对角线
diagonal = [matrix[i][i] for i in range(len(matrix))]
print(f"对角线: {diagonal}")   # [1, 5, 9]

# ============================================================
# 6. 嵌套推导式（生成矩阵）
# ============================================================
print("\n=== 6. 生成矩阵 ===")
# 生成 3x3 单位矩阵
identity = [[1 if i == j else 0 for j in range(3)] for i in range(3)]
print("单位矩阵:")
for row in identity:
    print(f"  {row}")

# 生成 3x4 零矩阵
zeros = [[0 for _ in range(4)] for _ in range(3)]
print(f"零矩阵: {zeros}")

# ============================================================
# 7. eshop 场景：从商品列表提取价格
# ============================================================
print("\n=== 7. 提取商品价格 ===")
products = [
    {"id": 1001, "name": "iPhone 15", "price": 5999, "stock": 50},
    {"id": 1002, "name": "MacBook Pro", "price": 12999, "stock": 20},
    {"id": 1003, "name": "AirPods", "price": 1999, "stock": 100},
    {"id": 1004, "name": "iPad", "price": 3999, "stock": 30},
]

# 提取所有价格
prices = [p["price"] for p in products]
print(f"所有价格: {prices}")

# 提取商品名
names = [p["name"] for p in products]
print(f"所有名称: {names}")

# 提取 (名称, 价格) 对
name_price = [(p["name"], p["price"]) for p in products]
print(f"名称-价格: {name_price}")

# ============================================================
# 8. eshop 场景：过滤库存不足商品
# ============================================================
print("\n=== 8. 过滤库存不足 ===")
# 找出库存低于 30 的商品名
LOW_STOCK = 30
low_stock = [p["name"] for p in products if p["stock"] < LOW_STOCK]
print(f"库存不足(<{LOW_STOCK}): {low_stock}")

# 找出库存充足且价格高于 3000 的商品
premium_available = [
    p["name"] for p in products
    if p["stock"] >= 30 and p["price"] > 3000
]
print(f"高端且有货: {premium_available}")

# 缺货商品（库存为 0）
out_of_stock = [p["name"] for p in products if p["stock"] == 0]
print(f"缺货: {out_of_stock}")   # []

# ============================================================
# 9. eshop 场景：生成商品名列表（带格式化）
# ============================================================
print("\n=== 9. 格式化商品列表 ===")
# 生成格式化的商品信息字符串列表
formatted = [
    f"{p['id']:04d} | {p['name']:<12} | {p['price']:>6} 元 | 库存 {p['stock']}"
    for p in products
]
for line in formatted:
    print(f"  {line}")

# 生成"名称: 价格"格式的列表
price_list = [f"{p['name']}: {p['price']:,} 元" for p in products]
print(f"\n价目表:")
for item in price_list:
    print(f"  {item}")

# ============================================================
# 10. 推导式与函数组合
# ============================================================
print("\n=== 10. 推导式 + 函数 ===")
# 对每个价格应用折扣
apply_discount = lambda price, rate: round(price * rate, 2)

discounted = [apply_discount(p["price"], 0.85) for p in products]
print(f"85 折后价: {discounted}")

# 计算每个商品的总库存价值
stock_value = [p["price"] * p["stock"] for p in products]
print(f"库存价值: {stock_value}")
print(f"总库存价值: {sum(stock_value):,}")

# ============================================================
# 11. 性能对比：推导式 vs for 循环 vs map
# ============================================================
print("\n=== 11. 写法对比 ===")
data = list(range(1, 6))

# 推导式
result1 = [x ** 2 for x in data]
print(f"推导式: {result1}")

# for 循环
result2 = []
for x in data:
    result2.append(x ** 2)
print(f"for 循环: {result2}")

# map + lambda（返回迭代器，需 list 转换）
result3 = list(map(lambda x: x ** 2, data))
print(f"map: {result3}")

print("提示：推导式通常比 for 循环更快，也比 map+lambda 更易读")


if __name__ == "__main__":
    print("\n--- list_comprehension.py 演示结束 ---")
