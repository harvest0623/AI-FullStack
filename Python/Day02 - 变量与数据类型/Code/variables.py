# 文件用途：变量赋值与命名规则练习，演示多变量赋值、变量交换、type()/id()、动态类型
# 语法：python variables.py

# ============================================================
# 1. 基本赋值与命名规则
# ============================================================
# 合法命名：字母/数字/下划线，不能数字开头，不能用关键字
product_id = 1001
product_name = "iPhone 15"
price = 5999
_stock = 120          # 下划线开头表示内部变量（约定）
MAX_STOCK = 9999      # 常量全大写（约定）

print("=== 1. 基本赋值 ===")
print(f"商品ID: {product_id}, 名称: {product_name}, 价格: {price}")

# 以下为非法命名示例（取消注释会报 SyntaxError）
# 1product = 100      # 不能数字开头
# product-name = 99   # 不能用连字符（会被解析成减法）
# class = "电子产品"    # 不能用关键字

# ============================================================
# 2. 多变量赋值
# ============================================================
print("\n=== 2. 多变量赋值 ===")
# 元组解包：同时给多个变量赋值
order_id, customer_id, total = 5001, 88, 299.5
print(f"订单 {order_id}，客户 {customer_id}，金额 {total}")

# 链式赋值：同一值赋给多个变量
a = b = c = 0
print(f"链式赋值: a={a}, b={b}, c={c}")

# ============================================================
# 3. 变量交换（无需中间变量）
# ============================================================
print("\n=== 3. 变量交换 ===")
x, y = 10, 20
print(f"交换前: x={x}, y={y}")
x, y = y, x
print(f"交换后: x={x}, y={y}")

# eshop 场景：交换两个商品的排序位置
product_a, product_b = "iPhone", "MacBook"
product_a, product_b = product_b, product_a
print(f"交换后: product_a={product_a}, product_b={product_b}")

# ============================================================
# 4. type() 查看类型
# ============================================================
print("\n=== 4. type() 查看类型 ===")
product_id = 1001
product_name = "iPhone 15"
price = 5999.0
in_stock = True
remark = None

print(f"{product_id} -> {type(product_id)}")
print(f"{product_name} -> {type(product_name)}")
print(f"{price} -> {type(price)}")
print(f"{in_stock} -> {type(in_stock)}")
print(f"{remark} -> {type(remark)}")

# ============================================================
# 5. id() 查看对象标识
# ============================================================
print("\n=== 5. id() 查看对象标识 ===")
# 小整数缓存：-5~256 的整数共享同一对象
n1 = 100
n2 = 100
print(f"id(n1)={id(n1)}, id(n2)={id(n2)}, 同一对象: {n1 is n2}")

# 大整数不缓存，每次创建新对象
n3 = 100000
n4 = 100000
print(f"id(n3)={id(n3)}, id(n4)={id(n4)}, 同一对象: {n3 is n4}")

# 字符串驻留（短字符串可能共享）
s1 = "eshop"
s2 = "eshop"
print(f"字符串 s1 is s2: {s1 is s2}")

# ============================================================
# 6. 动态类型演示
# ============================================================
print("\n=== 6. 动态类型演示 ===")
var = 100
print(f"var = {var}, 类型 = {type(var).__name__}")

var = "eshop"
print(f"var = {var}, 类型 = {type(var).__name__}")

var = [1, 2, 3]
print(f"var = {var}, 类型 = {type(var).__name__}")

var = None
print(f"var = {var}, 类型 = {type(var).__name__}")

# ============================================================
# 7. eshop 场景：商品信息变量管理
# ============================================================
print("\n=== 7. eshop 场景 ===")
# 一次解包商品的多维信息
product = (1001, "iPhone 15", 5999, 120, "手机")
pid, pname, pprice, pstock, pcategory = product
print(f"商品: ID={pid}, 名称={pname}, 价格={pprice}, 库存={pstock}, 类目={pcategory}")


if __name__ == "__main__":
    print("\n--- variables.py 演示结束 ---")
