# 文件用途：module_demo 包的初始化文件
# 演示 __init__.py 的作用：包级初始化、聚合子模块、__all__ 控制导出

# 从子模块导入对外暴露的函数（包级聚合）
from .math_utils import add, multiply, factorial, square_sum
from .string_utils import upper, lower, reverse, capitalize_words

# __all__ 控制 from module_demo import * 时只导出以下名字
# 这是声明「公开 API」的标准方式
__all__ = [
    'add',
    'multiply',
    'factorial',
    'square_sum',
    'upper',
    'lower',
    'reverse',
    'capitalize_words',
]

# 包级初始化代码：导入包时执行一次
print('[module_demo] 包已加载，公开 API:', __all__)
