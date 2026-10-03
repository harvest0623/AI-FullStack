# 文件用途：列表操作练习，演示增删改查/排序/反转、嵌套列表、浅拷贝vs深拷贝、列表解包，用电商场景操作购物车
# 语法：python lists.py

import copy

# ============================================================
# 1. 列表创建
# ============================================================
print("=== 1. 列表创建 ===")
empty = []
nums = [1, 2, 3]
mixed = [1, "a", True, None]
from_range = list(range(5))
print(f"空列表: {empty}")
print(f"混合列表: {mixed}")
print(f"list(range(5)): {from_range}")

# ============================================================
# 2. 索引与切片
# ============================================================
print("\n=== 2. 索引与切片 ===")
lst = ["iPhone", "MacBook", "iPad", "AirPods", "Watch"]
print(f"lst[0] = {lst[0]}")          # iPhone
print(f"lst[-1] = {lst[-1]}")        # Watch
print(f"lst[1:4] = {lst[1:4]}")      # ['MacBook', 'iPad', 'AirPods']
print(f"lst[::-1] = {lst[::-1]}")    # 反转

# ============================================================
# 3. 增：append / extend / insert
# ============================================================
print("\n=== 3. 增 ===")
cart = []
cart.append("iPhone")               # 末尾追加单个
print(f"append: {cart}")
cart.extend(["MacBook", "iPad"])     # 末尾追加多个
print(f"extend: {cart}")
cart.insert(0, "AirPods")           # 在索引0处插入
print(f"insert(0, AirPods): {cart}")

# 注意 append vs extend 区别
a = [1, 2]
a.append([3, 4])     # 把列表作为一个元素追加
print(f"append([3,4]): {a}")        # [1, 2, [3, 4]]
b = [1, 2]
b.extend([3, 4])     # 把列表元素逐个追加
print(f"extend([3,4]): {b}")        # [1, 2, 3, 4]

# ============================================================
# 4. 删：remove / pop / del / clear
# ============================================================
print("\n=== 4. 删 ===")
lst = ["iPhone", "MacBook", "iPad", "MacBook"]
lst.remove("MacBook")    # 删除第一个匹配项
print(f"remove('MacBook'): {lst}")   # ['iPhone', 'iPad', 'MacBook']

popped = lst.pop()       # 弹出末尾元素
print(f"pop() -> {popped}, 列表: {lst}")

popped = lst.pop(0)      # 弹出索引0
print(f"pop(0) -> {popped}, 列表: {lst}")

del lst[0]               # 删除索引0
print(f"del lst[0]: {lst}")

lst.clear()              # 清空
print(f"clear(): {lst}")

# ============================================================
# 5. 改
# ============================================================
print("\n=== 5. 改 ===")
lst = [1, 2, 3, 4, 5]
lst[0] = 10
print(f"lst[0]=10: {lst}")          # [10, 2, 3, 4, 5]
lst[1:3] = [20, 30, 40]             # 切片替换
print(f"lst[1:3]=[...]: {lst}")     # [10, 20, 30, 40, 4, 5]

# ============================================================
# 6. 查：in / index / count
# ============================================================
print("\n=== 6. 查 ===")
lst = ["iPhone", "MacBook", "iPad", "iPhone"]
print(f"'iPad' in lst: {'iPad' in lst}")        # True
print(f"index('MacBook'): {lst.index('MacBook')}")  # 1
print(f"count('iPhone'): {lst.count('iPhone')}")    # 2
# lst.index('xyz')  # ValueError（找不到）

# ============================================================
# 7. 排序与反转
# ============================================================
print("\n=== 7. 排序与反转 ===")
nums = [3, 1, 4, 1, 5, 9, 2, 6]
# sort 原地排序
nums.sort()
print(f"sort 升序: {nums}")
nums.sort(reverse=True)
print(f"sort 降序: {nums}")

# sorted 返回新列表（不改原列表）
original = [3, 1, 2]
new_list = sorted(original)
print(f"sorted: 原列表{original}, 新列表{new_list}")

# 按 key 排序（eshop 场景：按价格排序商品）
products = [
    {"name": "iPhone", "price": 5999},
    {"name": "AirPods", "price": 1999},
    {"name": "MacBook", "price": 12999},
]
products.sort(key=lambda p: p["price"])
print(f"按价格升序: {[p['name'] for p in products]}")
products.sort(key=lambda p: p["price"], reverse=True)
print(f"按价格降序: {[p['name'] for p in products]}")

# reverse 原地反转
lst = [1, 2, 3]
lst.reverse()
print(f"reverse: {lst}")    # [3, 2, 1]

# ============================================================
# 8. 嵌套列表（矩阵）
# ============================================================
print("\n=== 8. 嵌套列表 ===")
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
print(f"matrix[1][2] = {matrix[1][2]}")   # 6

# 遍历矩阵
for row in matrix:
    for cell in row:
        print(cell, end=" ")
    print()

# 取每一列（转置）
transposed = [[row[i] for row in matrix] for i in range(3)]
print(f"转置: {transposed}")

# ============================================================
# 9. 浅拷贝 vs 深拷贝
# ============================================================
print("\n=== 9. 浅拷贝 vs 深拷贝 ===")
# 引用赋值（完全同一对象）
a = [1, 2, 3]
b = a
b[0] = 99
print(f"引用赋值: a={a}, b={b}（改 b 影响 a）")

# 浅拷贝：外层新对象，内层共享引用
a = [[1, 2], [3, 4]]
b = a.copy()            # 等价 a[:] 或 copy.copy(a)
b[0][0] = 99            # 改内层元素
print(f"浅拷贝改内层: a={a}, b={b}（内层共享，a 也变）")
b.append([5, 6])        # 改外层元素
print(f"浅拷贝改外层: a={a}, b={b}（外层独立，a 不变）")

# 深拷贝：递归复制所有层级
a = [[1, 2], [3, 4]]
b = copy.deepcopy(a)
b[0][0] = 99
print(f"深拷贝改内层: a={a}, b={b}（完全独立）")

# ============================================================
# 10. 列表解包
# ============================================================
print("\n=== 10. 列表解包 ===")
first, *rest = [1, 2, 3, 4]
print(f"first={first}, rest={rest}")           # first=1, rest=[2,3,4]

first, *mid, last = [1, 2, 3, 4]
print(f"first={first}, mid={mid}, last={last}")  # first=1, mid=[2,3], last=4

# 忽略中间
first, *_ = [1, 2, 3, 4]
print(f"只要 first: {first}")

# ============================================================
# 11. 常用内置函数
# ============================================================
print("\n=== 11. 常用内置函数 ===")
nums = [3, 1, 4, 1, 5, 9, 2, 6]
print(f"len: {len(nums)}")
print(f"max: {max(nums)}")
print(f"min: {min(nums)}")
print(f"sum: {sum(nums)}")
print(f"any([0, 0, 1]): {any([0, 0, 1])}")    # True（有 Truthy）
print(f"all([1, 2, 3]): {all([1, 2, 3])}")    # True（全 Truthy）
print(f"all([1, 0, 3]): {all([1, 0, 3])}")    # False

# ============================================================
# 12. eshop 场景：购物车列表操作
# ============================================================
print("\n=== 12. eshop 购物车 ===")
cart = []

# 添加商品
cart.append({"name": "iPhone 15", "price": 5999, "qty": 1})
cart.append({"name": "AirPods", "price": 1999, "qty": 2})
cart.append({"name": "保护壳", "price": 99, "qty": 1})
print("购物车:")
for item in cart:
    print(f"  {item['name']} x{item['qty']} = {item['price'] * item['qty']}")

# 计算总价
total = sum(item["price"] * item["qty"] for item in cart)
print(f"总价: {total}")

# 移除商品
cart = [item for item in cart if item["name"] != "保护壳"]
print(f"移除保护壳后: {[i['name'] for i in cart]}")

# 按价格排序
cart.sort(key=lambda x: x["price"], reverse=True)
print(f"按价格降序: {[i['name'] for i in cart]}")

# ============================================================
# 13. eshop 场景：商品列表排序
# ============================================================
print("\n=== 13. 商品排序 ===")
products = [
    ("iPhone 15", 5999, 50),
    ("MacBook Pro", 12999, 20),
    ("AirPods", 1999, 100),
    ("iPad", 3999, 30),
]
# 按名称排序
by_name = sorted(products, key=lambda p: p[0])
print(f"按名称: {[p[0] for p in by_name]}")
# 按价格排序
by_price = sorted(products, key=lambda p: p[1])
print(f"按价格升序: {[p[0] for p in by_price]}")
# 按库存降序
by_stock = sorted(products, key=lambda p: p[2], reverse=True)
print(f"按库存降序: {[p[0] for p in by_stock]}")


if __name__ == "__main__":
    print("\n--- lists.py 演示结束 ---")
