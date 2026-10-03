# 文件用途：循环练习，演示 for+range、while、break/continue/pass、for-else、enumerate、zip，用电商商品遍历
# 语法：python loops.py

# ============================================================
# 1. for + range
# ============================================================
print("=== 1. for + range ===")
# range(start, stop, step)
for i in range(5):            # 0,1,2,3,4
    print(i, end=" ")
print()

for i in range(10, 0, -2):    # 10,8,6,4,2
    print(i, end=" ")
print()

# 遍历字符串
for ch in "eshop":
    print(ch, end="-")
print()

# 遍历列表
for name in ["iPhone", "MacBook", "AirPods"]:
    print(name, end=" | ")
print()

# 遍历字典
product = {"id": 1001, "name": "iPhone 15", "price": 5999}
print("遍历键:")
for key in product:
    print(f"  {key}")
print("遍历键值:")
for key, value in product.items():
    print(f"  {key}: {value}")

# ============================================================
# 2. while 循环
# ============================================================
print("\n=== 2. while 循环 ===")
count = 3
while count > 0:
    print(f"倒计时: {count}")
    count -= 1
print("发射！")

# ============================================================
# 3. break / continue / pass
# ============================================================
print("\n=== 3. break / continue / pass ===")
# break：跳出循环
for i in range(10):
    if i == 5:
        print(f"  遇到 {i}，break 跳出")
        break
    print(f"  i = {i}")

# continue：跳过本次
print("\n跳过偶数:")
for i in range(6):
    if i % 2 == 0:
        continue
    print(f"  奇数: {i}")

# pass：空占位（常用于空函数/类的占位）
print("\npass 占位演示:")
for i in range(3):
    pass   # 什么都不做，但语法上需要一个语句
print("  循环执行完毕（pass 不影响）")

# ============================================================
# 4. for-else（循环正常结束才执行 else）
# ============================================================
print("\n=== 4. for-else ===")
# 查找目标，没 break 才执行 else
target = "MacBook"
products = ["iPhone", "iPad", "AirPods"]
for p in products:
    if p == target:
        print(f"  找到: {target}")
        break
else:
    print(f"  没找到 {target}")   # 循环正常结束（没 break）才执行

# 再次查找（这次能找到）
target = "iPhone"
for p in products:
    if p == target:
        print(f"  找到: {target}")
        break
else:
    print(f"  没找到 {target}")   # break 了，不执行

# ============================================================
# 5. while-else
# ============================================================
print("\n=== 5. while-else ===")
n = 5
while n > 0:
    n -= 1
    if n == 2:
        break
    print(f"  n = {n}")
else:
    print("  while 正常结束")   # break 了，不执行

# 不 break 的情况
n = 3
while n > 0:
    print(f"  n = {n}")
    n -= 1
else:
    print("  while 正常结束")   # 正常结束，执行

# ============================================================
# 6. enumerate：同时获取索引和值
# ============================================================
print("\n=== 6. enumerate ===")
products = ["iPhone", "MacBook", "AirPods"]
for index, name in enumerate(products):
    print(f"  [{index}] {name}")

# 指定起始索引
for index, name in enumerate(products, start=1):
    print(f"  商品 {index}: {name}")

# ============================================================
# 7. zip：并行遍历多个序列
# ============================================================
print("\n=== 7. zip 并行遍历 ===")
names = ["iPhone", "MacBook", "AirPods"]
prices = [5999, 12999, 1999]
stocks = [50, 20, 100]
for name, price, stock in zip(names, prices, stocks):
    print(f"  {name}: {price} 元, 库存 {stock}")

# zip 长度不等时以最短为准
short = [1, 2]
long = [10, 20, 30, 40]
for s, l in zip(short, long):
    print(f"  ({s}, {l})")

# ============================================================
# 8. eshop 场景：遍历商品列表计算总价
# ============================================================
print("\n=== 8. eshop 商品总价计算 ===")
cart = [
    ("iPhone 15", 5999, 2),
    ("AirPods Pro", 1999, 1),
    ("保护壳", 99, 3),
]
total = 0
for name, price, qty in cart:
    subtotal = price * qty
    total += subtotal
    print(f"  {name} x{qty} = {subtotal}")
print(f"  总计: {total}")

# 用 enumerate 带序号展示
print("\n带序号展示购物车:")
for idx, (name, price, qty) in enumerate(cart, 1):
    print(f"  {idx}. {name} - {price} 元 x {qty}")

# ============================================================
# 9. eshop 场景：查找库存不足商品
# ============================================================
print("\n=== 9. 查找库存不足商品 ===")
products = [
    {"name": "iPhone", "stock": 50},
    {"name": "MacBook", "stock": 0},
    {"name": "AirPods", "stock": 30},
    {"name": "iPad", "stock": 0},
]

# 用 for-else 查找第一个缺货商品
for p in products:
    if p["stock"] == 0:
        print(f"  发现缺货: {p['name']}")
        break
else:
    print("  全部有货")

# 查找所有缺货商品
print("所有缺货商品:")
for p in products:
    if p["stock"] == 0:
        print(f"  - {p['name']}")

# ============================================================
# 10. 循环常见模式：累加 / 过滤 / 查找
# ============================================================
print("\n=== 10. 循环常见模式 ===")
data = [12, 5, 8, 20, 3, 15, 7]

# 累加
s = 0
for x in data:
    s += x
print(f"  求和: {s}")

# 过滤（提取大于 10 的）
big_nums = []
for x in data:
    if x > 10:
        big_nums.append(x)
print(f"  大于 10 的: {big_nums}")

# 查找最大值（不用 max）
max_val = data[0]
for x in data[1:]:
    if x > max_val:
        max_val = x
print(f"  最大值: {max_val}")


if __name__ == "__main__":
    print("\n--- loops.py 演示结束 ---")
