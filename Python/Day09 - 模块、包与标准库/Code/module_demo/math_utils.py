# 文件用途：数学工具函数模块
# 演示模块定义、函数导出，供 __init__.py 聚合或被其他模块直接导入


def add(a: float, b: float) -> float:
    """两数相加"""
    return a + b


def multiply(a: float, b: float) -> float:
    """两数相乘"""
    return a * b


def factorial(n: int) -> int:
    """计算阶乘 n!（非递归实现）"""
    if n < 0:
        raise ValueError('阶乘要求 n >= 0')
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def square_sum(*nums: float) -> float:
    """平方和：sum(x^2)"""
    return sum(x * x for x in nums)


# 内部辅助函数（下划线开头，不会被 __all__ 导出，也不建议外部使用）
_internal_version = '1.0.0'


def _debug_info() -> str:
    """内部调试信息，不对外暴露"""
    return f'math_utils v{_internal_version}'


# __name__ == '__main__' 机制：直接运行本文件时执行自测
if __name__ == '__main__':
    print('直接运行 math_utils.py 进行自测')
    print(f'add(2, 3) = {add(2, 3)}')
    print(f'multiply(4, 5) = {multiply(4, 5)}')
    print(f'factorial(5) = {factorial(5)}')
    print(f'square_sum(1, 2, 3) = {square_sum(1, 2, 3)}')
    print(f'模块名: {__name__}')
else:
    # 被导入时 __name__ 为 'module_demo.math_utils'
    print(f'[模块加载] {__name__}')
