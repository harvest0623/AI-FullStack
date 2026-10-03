# 文件用途：第一个 Python 程序，演示 print、input、f-string 与 __main__ 入口
# 语法：python hello.py

# 1. 最基础的输出
print("Hello, Python!")
print("欢迎来到 eshop 电商数据处理 CLI 工具")

# 2. print 的 sep 与 end 参数
# sep 控制多个参数之间的分隔符，end 控制行末字符
print("商品", "iPhone 15", "价格", 5999, sep=" | ", end="\n\n")

# 3. input 读取用户输入（input 返回的是字符串）
shop_name = input("请输入店铺名称：")
print("您输入的店铺是：", shop_name)

# 4. f-string 格式化字符串（Python 3.6+ 推荐）
product_name = "iPhone 15"
price = 5999
stock = 120
# f-string 可以直接在 {} 中写表达式
print(f"商品：{product_name}，价格：{price} 元，库存：{stock} 件")
# 控制小数位数
discount_price = price * 0.9
print(f"折扣价：{discount_price:.2f} 元")

# 5. 多变量赋值（元组解包）
product_id, product_name, product_price = 1001, "MacBook Pro", 12999
print(f"商品ID={product_id}, 名称={product_name}, 价格={product_price}")

# 6. if __name__ == '__main__' 的作用
# 当脚本被直接运行时，__name__ 等于 '__main__'
# 当脚本被作为模块导入时，__name__ 等于模块名，此处不会执行
# 这是 Python 的惯用入口写法，便于代码复用与测试
def greet(name: str) -> str:
    """返回欢迎语。"""
    return f"Hello, {name}! 欢迎使用 eshop。"


if __name__ == "__main__":
    # 只有直接运行本文件时才会执行下面的代码
    print(greet("eshop 用户"))
    print("本程序运行结束。")
