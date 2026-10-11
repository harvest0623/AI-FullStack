# 文件用途：字符串工具函数模块
# 演示模块定义，与 math_utils 并列，共同构成 module_demo 包


def upper(s: str) -> str:
    """转大写"""
    return s.upper()


def lower(s: str) -> str:
    """转小写"""
    return s.lower()


def reverse(s: str) -> str:
    """反转字符串"""
    return s[::-1]


def capitalize_words(s: str) -> str:
    """每个单词首字母大写"""
    return s.title()


def count_vowels(s: str) -> int:
    """统计元音字母数量（不对外导出，演示私有函数）"""
    return sum(1 for ch in s.lower() if ch in 'aeiou')


if __name__ == '__main__':
    print('直接运行 string_utils.py 进行自测')
    print(f'upper("hello") = {upper("hello")}')
    print(f'reverse("Python") = {reverse("Python")}')
    print(f'capitalize_words("hello world") = {capitalize_words("hello world")}')
    print(f'count_vowels("hello") = {count_vowels("hello")}')
    print(f'模块名: {__name__}')
else:
    print(f'[模块加载] {__name__}')
