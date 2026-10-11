# 文件用途：module_demo 包的执行入口
# 运行方式：python -m module_demo
# __main__.py 让一个包可以作为模块直接执行

# 相对导入：从当前包导入（. 表示当前包 module_demo）
from .math_utils import add, multiply, factorial, square_sum
from .string_utils import upper, reverse, capitalize_words


def demo_math() -> None:
    """演示数学工具"""
    print('=== 数学工具 ===')
    print(f'add(10, 20) = {add(10, 20)}')
    print(f'multiply(6, 7) = {multiply(6, 7)}')
    print(f'factorial(6) = {factorial(6)}')
    print(f'square_sum(3, 4, 5) = {square_sum(3, 4, 5)}')


def demo_string() -> None:
    """演示字符串工具"""
    print('=== 字符串工具 ===')
    print(f'upper("eshop") = {upper("eshop")}')
    print(f'reverse("Python") = {reverse("Python")}')
    print(f'capitalize_words("hello world") = {capitalize_words("hello world")}')


def demo_eshop_scenario() -> None:
    """电商场景演示：用工具函数计算订单"""
    print('=== 电商场景 ===')
    # 模拟三个商品价格
    prices = [99.5, 199.0, 49.9]
    total = 0.0
    for i, price in enumerate(prices, start=1):
        # multiply 计算单价 × 数量
        total = add(total, multiply(price, 2))  # 每个商品买 2 件
        print(f'商品{i}: {price} × 2 = {multiply(price, 2):.2f}')
    print(f'订单总额: {total:.2f}')


def main() -> None:
    """包主入口"""
    print('=' * 50)
    print('module_demo 包演示（python -m module_demo）')
    print(f'当前 __name__: {__name__}')
    print('=' * 50)
    demo_math()
    print()
    demo_string()
    print()
    demo_eshop_scenario()
    print('=' * 50)


# 作为 __main__.py，被 python -m 执行时 __name__ 就是 '__main__'
if __name__ == '__main__':
    main()
