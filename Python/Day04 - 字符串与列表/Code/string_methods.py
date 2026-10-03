# 文件用途：字符串方法练习，演示大小写/查找/判断/替换/分割/去空白/对齐填充，用电商场景解析CSV、格式化报告、验证邮箱
# 语法：python string_methods.py

import re

# ============================================================
# 1. 大小写转换
# ============================================================
print("=== 1. 大小写转换 ===")
s = "Hello eshop World"
print(f"upper(): {s.upper()}")          # HELLO ESHOP WORLD
print(f"lower(): {s.lower()}")          # hello eshop world
print(f"title(): {s.title()}")          # Hello Eshop World
print(f"capitalize(): {s.capitalize()}")# Hello eshop world
print(f"swapcase(): {s.swapcase()}")    # hELLO ESHOP wORLD

# eshop 场景：统一商品名大小写
product_name = "iphone 15 pro"
print(f"规范化: {product_name.title()}")  # Iphone 15 Pro

# ============================================================
# 2. 查找
# ============================================================
print("\n=== 2. 查找 ===")
s = "eshop-cli-eshop-tool"
print(f"find('eshop'): {s.find('eshop')}")        # 0（首次出现位置）
print(f"rfind('eshop'): {s.rfind('eshop')}")      # 10（最后一次出现）
print(f"find('xyz'): {s.find('xyz')}")            # -1（找不到）
print(f"count('eshop'): {s.count('eshop')}")      # 2（出现次数）
print(f"count('-'): {s.count('-')}")              # 3

# index 与 find 区别：index 找不到会抛 ValueError
print(f"index('cli'): {s.index('cli')}")          # 6
# s.index('xyz')  # ValueError

# ============================================================
# 3. 判断
# ============================================================
print("\n=== 3. 判断 ===")
print(f"'123'.isdigit(): {'123'.isdigit()}")       # True
print(f"'12.3'.isdigit(): {'12.3'.isdigit()}")    # False
print(f"'abc'.isalpha(): {'abc'.isalpha()}")      # True
print(f"'abc123'.isalnum(): {'abc123'.isalnum()}")# True
print(f"'   '.isspace(): {'   '.isspace()}")      # True

# startswith / endswith
filename = "products.csv"
print(f"\n'products.csv'.endswith('.csv'): {filename.endswith('.csv')}")
print(f"'ORD5001'.startswith('ORD'): {'ORD5001'.startswith('ORD')}")

# eshop 场景：判断订单号格式
order_no = "ORD5001"
if order_no.startswith("ORD") and order_no[3:].isdigit():
    print(f"{order_no} 是合法订单号")

# ============================================================
# 4. 替换与分割
# ============================================================
print("\n=== 4. 替换与分割 ===")
s = "a-b-c-d"
print(f"replace('-', '_'): {s.replace('-', '_')}")   # a_b_c_d
print(f"replace('-', '_', 1): {s.replace('-', '_', 1)}")  # a_b-c-d（只替换1次）

# split：分割成列表
csv_line = "1001,iPhone 15,5999,50"
parts = csv_line.split(",")
print(f"split: {parts}")   # ['1001', 'iPhone 15', '5999', '50']

# rsplit：从右分割，限制次数
print(f"rsplit('-', 1): {'a-b-c-d'.rsplit('-', 1)}")  # ['a-b-c', 'd']

# partition：分成三段（分隔符前/分隔符/分隔符后）
print(f"partition('='): {'name=eshop'.partition('=')}")  # ('name', '=', 'eshop')

# join：用字符串连接列表
names = ["iPhone", "MacBook", "AirPods"]
print(f"join: {' | '.join(names)}")   # iPhone | MacBook | AirPods

# ============================================================
# 5. 去空白
# ============================================================
print("\n=== 5. 去空白 ===")
s = "  eshop  \n\t"
print(f"原始: {s!r}")
print(f"strip(): {s.strip()!r}")      # 去两端
print(f"lstrip(): {s.lstrip()!r}")    # 去左端
print(f"rstrip(): {s.rstrip()!r}")    # 去右端

# 去指定字符
s2 = "###eshop###"
print(f"strip('#'): {s2.strip('#')!r}")   # eshop

# ============================================================
# 6. 对齐与填充
# ============================================================
print("\n=== 6. 对齐与填充 ===")
s = "eshop"
print(f"center(11, '-'): {s.center(11, '-')}")   # ---eshop---
print(f"ljust(10, '.'): {s.ljust(10, '.')!r}")   # eshop.....
print(f"rjust(10, '.'): {s.rjust(10, '.')!r}")   # .....eshop
print(f"zfill(10): {s.zfill(10)!r}")             # 00000eshop
print(f"'42'.zfill(5): {'42'.zfill(5)!r}")       # 00042

# ============================================================
# 7. eshop 场景：解析商品 CSV 行
# ============================================================
print("\n=== 7. eshop 解析 CSV 行 ===")


def parse_product_csv(line: str) -> dict:
    """解析商品 CSV 行，返回商品字典。

    输入格式: id,name,price,stock,category
    """
    # 去除首尾空白与可能的换行符
    line = line.strip()
    # 按逗号分割
    parts = line.split(",")
    if len(parts) != 5:
        return None
    pid, name, price, stock, category = parts
    return {
        "id": int(pid.strip()),
        "name": name.strip(),
        "price": float(price.strip()),
        "stock": int(stock.strip()),
        "category": category.strip(),
    }


csv_lines = [
    "1001, iPhone 15, 5999, 50, 手机\n",
    "1002, MacBook Pro, 12999, 20, 笔记本",
    "1003, AirPods, 1999, 100, 耳机",
]
for line in csv_lines:
    product = parse_product_csv(line)
    if product:
        print(f"  {product}")

# ============================================================
# 8. eshop 场景：格式化报告标题
# ============================================================
print("\n=== 8. 格式化报告标题 ===")


def make_report_title(title: str, width: int = 40) -> str:
    """生成居中的报告标题。"""
    return title.center(width, "=")


print(make_report_title("eshop 销售日报"))
print(make_report_title("库存盘点表", 30))
print(make_report_title("VIP 客户清单", 50))

# ============================================================
# 9. eshop 场景：验证邮箱格式（正则预览）
# ============================================================
print("\n=== 9. 邮箱格式验证 ===")


def is_valid_email(email: str) -> bool:
    """简单验证邮箱格式。"""
    email = email.strip()
    # 简单正则：字母数字@字母数字.字母
    pattern = r"^[\w.+-]+@[\w-]+\.[\w.-]+$"
    return bool(re.match(pattern, email))


test_emails = [
    "user@eshop.com",
    "admin.name@company.co.jp",
    "invalid-email",
    "@no-user.com",
    "user@",
]
for e in test_emails:
    print(f"  {e:25} -> {'有效' if is_valid_email(e) else '无效'}")

# ============================================================
# 10. 综合应用：清洗用户输入
# ============================================================
print("\n=== 10. 清洗用户输入 ===")


def clean_input(raw: str) -> str:
    """清洗用户输入：去空白、首字母大写、替换多个空格为单个。"""
    raw = raw.strip()
    raw = " ".join(raw.split())   # split 无参数会按任意空白分割，再用单空格连接
    return raw.capitalize()


inputs = ["  iphone   15   pro  ", "\teshop\n商城 ", "  MacBook  Pro  "]
for raw in inputs:
    print(f"  {raw!r} -> {clean_input(raw)!r}")


if __name__ == "__main__":
    print("\n--- string_methods.py 演示结束 ---")
