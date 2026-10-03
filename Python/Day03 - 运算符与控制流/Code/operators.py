# 文件用途：运算符演示，覆盖算术/比较/逻辑/位/成员/身份运算符、海象运算符、短路求值、小整数缓存
# 语法：python operators.py

# ============================================================
# 1. 算术运算符
# ============================================================
print("=== 1. 算术运算符 ===")
a, b = 17, 5
print(f"{a} + {b} = {a + b}")      # 22
print(f"{a} - {b} = {a - b}")      # 12
print(f"{a} * {b} = {a * b}")      # 85
print(f"{a} / {b} = {a / b}")      # 3.4（真除法）
print(f"{a} // {b} = {a // b}")    # 3（整除，向下取整）
print(f"{a} % {b} = {a % b}")      # 2（取余）
print(f"{a} ** {b} = {a ** b}")    # 1419857（幂）

# 负数整除：向下取整
print(f"-7 // 2 = {-7 // 2}")      # -4（不是 -3）
print(f"-7 % 2 = {-7 % 2}")        # 1（结果符号跟除数）

# divmod：同时返回商和余
print(f"divmod(17, 5) = {divmod(17, 5)}")  # (3, 2)

# abs / round
print(f"abs(-3.5) = {abs(-3.5)}")
print(f"round(3.1415, 2) = {round(3.1415, 2)}")

# ============================================================
# 2. 比较运算符与链式比较
# ============================================================
print("\n=== 2. 比较运算符 ===")
x = 5
print(f"{x} == 5: {x == 5}")
print(f"{x} != 3: {x != 3}")
print(f"{x} > 3: {x > 3}")

# 链式比较（Python 特色）
age = 25
print(f"18 <= {age} <= 60: {18 <= age <= 60}")   # True
# 等价于 18 <= age and age <= 60

# eshop 场景：库存安全区间
stock = 50
if 10 <= stock <= 100:
    print(f"库存 {stock} 处于安全区间")

# ============================================================
# 3. 逻辑运算符与短路求值
# ============================================================
print("\n=== 3. 逻辑运算符 ===")
print(f"True and False: {True and False}")
print(f"True or False: {True or False}")
print(f"not True: {not True}")

# 短路求值：and/or 返回操作数本身，而非布尔值
print(f"\n短路求值演示：")
print(f"0 and 1: {0 and 1!r}")        # 0（0 是 Falsy，短路返回）
print(f"1 and 2: {1 and 2!r}")        # 2（都 Truthy，返回最后一个）
print(f"1 and 0 and 3: {1 and 0 and 3!r}")  # 0
print(f"1 or 2: {1 or 2!r}")          # 1（1 是 Truthy，短路返回）
print(f"0 or 2: {0 or 2!r}")          # 2（0 是 Falsy，继续）
print(f"0 or '' or 3: {0 or '' or 3!r}")    # 3

# eshop 场景：提供默认值
nick = "" or "匿名用户"
print(f"空字符串 or 默认值: {nick}")

# 短路避免错误
data = None
# 若 data 为 None，data.get 会报错；用 and 短路保护
if data and data.get("price"):
    print(data["price"])
else:
    print("数据为空，跳过")

# ============================================================
# 4. 赋值运算符与海象运算符
# ============================================================
print("\n=== 4. 赋值运算符 ===")
total = 100
total += 50    # 等价于 total = total + 50
print(f"total += 50 -> {total}")
total *= 2
print(f"total *= 2 -> {total}")
total //= 3
print(f"total //= 3 -> {total}")

# 海象运算符 :=（3.8+）：表达式内部赋值
print("\n海象运算符演示：")
# 传统写法
text = "eshop"
n = len(text)
if n > 3:
    print(f"长度 {n} 超过 3")

# 海象写法：赋值与判断一次完成
if (n := len(text)) > 3:
    print(f"长度 {n} 超过 3（海象运算符）")

# eshop 场景：读取命令直到 quit
print("\n模拟读取命令（输入 quit 结束）：")
commands = ["list", "add", "quit"]
idx = 0
while (cmd := commands[idx]) != "quit":
    print(f"  执行命令: {cmd}")
    idx += 1
print("  程序退出")

# ============================================================
# 5. 位运算符
# ============================================================
print("\n=== 5. 位运算符 ===")
a, b = 5, 3   # 0b101, 0b011
print(f"{a} & {b} = {a & b}")      # 1（0b001）
print(f"{a} | {b} = {a | b}")      # 7（0b111）
print(f"{a} ^ {b} = {a ^ b}")      # 6（0b110）
print(f"~{a} = {~a}")               # -6
print(f"{a} << 1 = {a << 1}")      # 10
print(f"{a} >> 1 = {a >> 1}")      # 2

# eshop 场景：权限标志位
READ, WRITE, EXECUTE = 1, 2, 4
perm = READ | WRITE              # 可读可写
print(f"\n权限 {perm}: 读={bool(perm & READ)}, 写={bool(perm & WRITE)}, 执行={bool(perm & EXECUTE)}")

# ============================================================
# 6. 成员运算符
# ============================================================
print("\n=== 6. 成员运算符 ===")
print(f"3 in [1, 2, 3]: {3 in [1, 2, 3]}")
print(f"'e' in 'eshop': {'e' in 'eshop'}")
print(f"'price' in {{'price': 99}}: {'price' in {'price': 99}}")
print(f"5 not in [1, 2, 3]: {5 not in [1, 2, 3]}")

# eshop 场景：判断商品类目
category = "手机"
if category in ("手机", "平板", "笔记本"):
    print(f"{category} 属于数码类")

# ============================================================
# 7. 身份运算符 is vs == 与小整数缓存
# ============================================================
print("\n=== 7. 身份运算符 ===")
# is 比较 id()（对象身份），== 比较值
x = [1, 2, 3]
y = [1, 2, 3]
print(f"x == y: {x == y}")     # True（值相等）
print(f"x is y: {x is y}")     # False（不同对象）

# 小整数缓存：-5~256 共享对象
n1 = 256
n2 = 256
print(f"\n256 is 256: {n1 is n2}")   # True（缓存）

n3 = 257
n4 = 257
print(f"257 is 257: {n3 is n4}")     # 可能 False（不缓存）

# None 判断必须用 is
value = None
print(f"\nvalue is None: {value is None}")   # True（推荐）
print(f"value == None: {value == None}")     # True（不推荐）

# ============================================================
# 8. 运算符优先级验证
# ============================================================
print("\n=== 8. 运算符优先级 ===")
# ** 优先级最高
print(f"2 + 3 ** 2 = {2 + 3 ** 2}")   # 11，不是 25
# 用括号改变优先级
print(f"(2 + 3) ** 2 = {(2 + 3) ** 2}")  # 25

# not 优先级高于 and，and 高于 or
print(f"not True or True: {not True or True}")     # True
print(f"not (True or True): {not (True or True)}") # False


if __name__ == "__main__":
    print("\n--- operators.py 演示结束 ---")
