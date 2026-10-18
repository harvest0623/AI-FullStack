# 文件用途：异常处理练习
# 演示 try/except/else/finally、多种异常捕获、异常层级
# 电商场景：文件不存在处理、JSON 解析错误处理、类型转换错误处理
# 运行方式：python exception_handling.py

import json
from pathlib import Path


def demo_basic_try_except() -> None:
    """基本 try/except"""
    print('=== 基本 try/except ===')
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        print(f'捕获到异常: {type(e).__name__}: {e}')


def demo_full_structure() -> None:
    """完整的 try/except/else/finally 四段式"""
    print('=== try/except/else/finally ===')
    data = '{"name": "手机", "price": 2999}'
    try:
        # 可能出错的代码
        product = json.loads(data)
    except json.JSONDecodeError as e:
        print(f'JSON 解析失败: {e}')
    except TypeError as e:
        print(f'类型错误: {e}')
    else:
        # try 没异常时才执行
        print(f'解析成功: {product["name"]}')
    finally:
        # 总是执行（资源清理）
        print('清理完成（finally）')


def demo_multiple_exceptions() -> None:
    """捕获多种异常：元组形式 + 多分支"""
    print('=== 捕获多种异常 ===')

    def parse_int(value):
        try:
            return int(value)
        except (TypeError, ValueError) as e:
            # 一个 except 捕获多种类型
            print(f'  [元组] {value!r} 转换失败: {type(e).__name__}')
            return None

    parse_int('123')         # 正常
    parse_int('abc')         # ValueError
    parse_int([1, 2])        # TypeError

    # 多分支：具体在前，通用在后
    def open_file(path):
        try:
            with open(path, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f'  [多分支] 文件不存在: {path}')
        except PermissionError:
            print(f'  [多分支] 无权限: {path}')
        except OSError as e:    # OSError 是上面两个的父类，兜底
            print(f'  [多分支] 其他 OS 错误: {e}')
        return None

    open_file('不存在的文件.txt')


def demo_eshop_file_not_found() -> None:
    """电商场景：文件不存在处理"""
    print('=== 电商场景：文件不存在 ===')
    path = Path('data') / 'missing_products.json'

    try:
        content = path.read_text(encoding='utf-8')
        products = json.loads(content)
    except FileNotFoundError:
        print(f'商品文件不存在: {path}')
        print('使用默认空列表代替')
        products = []
    else:
        print(f'成功加载 {len(products)} 件商品')

    print(f'当前商品数: {len(products)}')


def demo_eshop_json_parse_error() -> None:
    """电商场景：JSON 解析错误处理"""
    print('=== 电商场景：JSON 解析错误 ===')
    # 故意写一段非法 JSON
    bad_json = '{"name": "手机", "price": 2999,'   # 缺右括号

    path = Path('data') / 'bad_product.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bad_json, encoding='utf-8')

    try:
        text = path.read_text(encoding='utf-8')
        product = json.loads(text)
    except FileNotFoundError:
        print('文件不存在')
    except json.JSONDecodeError as e:
        print(f'JSON 格式错误: {e}')
        print(f'  错误位置: 行 {e.lineno}, 列 {e.colno}')
        print(f'  错误内容: {e.doc[:50]}...')
    else:
        print(f'解析成功: {product}')


def demo_eshop_type_conversion() -> None:
    """电商场景：类型转换错误处理"""
    print('=== 电商场景：类型转换错误 ===')
    # 模拟从用户输入/CSV 读到的数据，可能格式不对
    raw_prices = ['2999.0', '399', 'abc', None, '-50', '0']

    valid_prices = []
    for raw in raw_prices:
        try:
            price = float(raw)
            if price < 0:
                raise ValueError(f'价格不能为负: {price}')
        except TypeError:
            print(f'  跳过 None（类型错误）')
        except ValueError as e:
            print(f'  跳过 {raw!r}: {e}')
        else:
            valid_prices.append(price)

    print(f'有效价格: {valid_prices}')


def demo_exception_hierarchy() -> None:
    """演示异常层级：父类捕获子类"""
    print('=== 异常层级 ===')
    # FileNotFoundError 是 OSError 的子类
    exceptions = [
        FileNotFoundError('文件不存在'),
        PermissionError('无权限'),
        IsADirectoryError('是目录'),
    ]
    for exc in exceptions:
        print(f'  {type(exc).__name__} 是 OSError 子类: {isinstance(exc, OSError)}')
        print(f'  也是 Exception 子类: {isinstance(exc, Exception)}')

    # 用父类兜底
    try:
        raise FileNotFoundError('测试')
    except OSError as e:
        print(f'  OSError 兜底捕获: {type(e).__name__}')


def demo_raise() -> None:
    """主动抛出异常"""
    print('=== 主动 raise ===')

    def set_price(price):
        if not isinstance(price, (int, float)):
            raise TypeError(f'价格必须是数字，收到 {type(price).__name__}')
        if price < 0:
            raise ValueError(f'价格不能为负: {price}')

    for p in [2999.0, -10, 'abc']:
        try:
            set_price(p)
            print(f'  {p} 设置成功')
        except (TypeError, ValueError) as e:
            print(f'  {p!r} 失败: {type(e).__name__}: {e}')


def demo_finally_resource() -> None:
    """finally 用于资源清理"""
    print('=== finally 资源清理 ===')
    f = None
    try:
        f = open('data' / Path('demo_finally.txt'), 'w', encoding='utf-8')
        f.write('test')
        # 模拟中途出错
        result = 1 / 0
    except ZeroDivisionError:
        print('  捕获到除零错误')
    finally:
        # 无论是否异常都关闭文件
        if f and not f.closed:
            f.close()
            print('  finally 已关闭文件')
    print(f'  文件已关闭: {f.closed}')


def main() -> None:
    demos = [
        demo_basic_try_except,
        demo_full_structure,
        demo_multiple_exceptions,
        demo_eshop_file_not_found,
        demo_eshop_json_parse_error,
        demo_eshop_type_conversion,
        demo_exception_hierarchy,
        demo_raise,
        demo_finally_resource,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
