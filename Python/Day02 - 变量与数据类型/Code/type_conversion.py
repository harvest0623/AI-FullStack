# 文件用途：类型转换练习，演示 int/float/str/bool 转换、isinstance vs type、Truthy/Falsy 测试
# 语法：python type_conversion.py

# ============================================================
# 1. int() 转换
# ============================================================
print("=== 1. int() 转换 ===")
print(f"int('123') = {int('123')}")          # 字符串转整数
print(f"int(3.9) = {int(3.9)}")              # float 转整数（直接截断）
print(f"int(-3.9) = {int(-3.9)}")            # 负数截断（向 0 取整）
print(f"int('0xff', 16) = {int('0xff', 16)}")  # 按十六进制解析
print(f"int(True) = {int(True)}")

# 错误示例（取消注释会报 ValueError）
# int('abc')      # 无法解析
# int('12.3')     # 字符串含小数点，需先 float

# 正确做法：先 float 再 int
print(f"int(float('12.3')) = {int(float('12.3'))}")

# ============================================================
# 2. float() 转换
# ============================================================
print("\n=== 2. float() 转换 ===")
print(f"float('3.14') = {float('3.14')}")
print(f"float(5) = {float(5)}")
print(f"float('1e5') = {float('1e5')}")      # 科学计数法
print(f"float(True) = {float(True)}")

# ============================================================
# 3. str() 转换
# ============================================================
print("\n=== 3. str() 转换 ===")
print(f"str(123) = {str(123)!r}")
print(f"str(3.14) = {str(3.14)!r}")
print(f"str(True) = {str(True)!r}")
print(f"str([1, 2, 3]) = {str([1, 2, 3])!r}")
print(f"str(None) = {str(None)!r}")

# ============================================================
# 4. bool() 转换与 Falsy 值
# ============================================================
print("\n=== 4. bool() 转换 ===")
# Falsy 值：False / 0 / 0.0 / "" / [] / {} / () / None
falsy_values = [False, 0, 0.0, "", '', [], {}, (), None, 0j, b""]
print("Falsy 值清单：")
for v in falsy_values:
    print(f"  bool({v!r}) = {bool(v)}")

# Truthy 值示例
print("\nTruthy 值示例：")
truthy_values = [True, 1, -1, 0.0001, "0", "False", [0], {"a": 0}, (0,)]
for v in truthy_values:
    print(f"  bool({v!r}) = {bool(v)}")

# 注意：bool("0") 是 True！因为非空字符串都是 Truthy
print(f"\n注意：bool('0') = {bool('0')}（非空字符串是 Truthy）")

# ============================================================
# 5. type() vs isinstance()
# ============================================================
print("\n=== 5. type() vs isinstance() ===")
x = True
print(f"x = True")
print(f"type(x) == int: {type(x) == int}")          # False（精确匹配）
print(f"type(x) == bool: {type(x) == bool}")        # True
print(f"isinstance(x, int): {isinstance(x, int)}")  # True（考虑继承）
print(f"isinstance(x, bool): {isinstance(x, bool)}")# True

# isinstance 支持传入元组，判断多个类型
y = 3.14
print(f"\ny = 3.14")
print(f"isinstance(y, (int, float)): {isinstance(y, (int, float))}")

# 继承场景演示
class Animal:
    pass


class Dog(Animal):
    pass


d = Dog()
print(f"\nd = Dog()")
print(f"type(d) == Animal: {type(d) == Animal}")          # False
print(f"isinstance(d, Animal): {isinstance(d, Animal)}")  # True（继承）

# ============================================================
# 6. eshop 场景：类型转换实战
# ============================================================
print("\n=== 6. eshop 场景：类型转换 ===")
# 从 CSV/表单读到的数据都是字符串，需要转换
raw_data = ["1001", "iPhone 15", "5999", "120", "1"]
product_id = int(raw_data[0])           # 转商品ID
name = raw_data[1]                       # 名称保持字符串
price = float(raw_data[2])               # 价格转 float
stock = int(raw_data[3])                 # 库存转 int
in_stock = bool(int(raw_data[4]))        # 是否有货转 bool
print(f"商品: ID={product_id}, 名称={name}, 价格={price}, 库存={stock}, 有货={in_stock}")

# 真值测试：库存为 0 时判断缺货
stock = 0
if stock:
    print(f"库存 {stock}：有货")
else:
    print(f"库存 {stock}：缺货（0 是 Falsy）")

# 备注字段可能为空字符串或 None
def format_remark(remark):
    """格式化订单备注，空值返回默认提示。"""
    if remark:                  # 真值测试：空字符串是 Falsy
        return f"备注: {remark}"
    return "备注: 无"


print(format_remark("加急发货"))
print(format_remark(""))
print(format_remark(None))

# ============================================================
# 7. 转换中的常见陷阱
# ============================================================
print("\n=== 7. 转换陷阱 ===")
# 陷阱1：input() 返回的是字符串，必须转换才能做运算
user_input = "100"
# total = user_input * 2   # 字符串乘法会变成 "100100"
total = int(user_input) * 2
print(f"用户输入 100，乘 2 = {total}")

# 陷阱2：float 转 int 是截断，不是四舍五入
print(f"int(2.9) = {int(2.9)}（不是 3，是截断）")
# 如需四舍五入用 round
print(f"round(2.9) = {round(2.9)}")


if __name__ == "__main__":
    print("\n--- type_conversion.py 演示结束 ---")
