# 文件用途：标准库精选示例集合
# 演示 os / sys / pathlib / json / datetime / collections / random / math 等高频标准库
# 运行方式：python stdlib_examples.py

import os
import sys
import json
import math
import random
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from collections import namedtuple, defaultdict, Counter, deque


def demo_os() -> None:
    """os 模块：操作系统接口"""
    print('=== os 模块 ===')
    # 环境变量
    home = os.environ.get('USERPROFILE') or os.environ.get('HOME', '未知')
    print(f'用户主目录: {home}')
    print(f'PATH 是否存在: {"PATH" in os.environ}')
    # 设置临时环境变量
    os.environ['ESHOP_DEBUG'] = 'true'
    print(f'自定义变量 ESHOP_DEBUG = {os.getenv("ESHOP_DEBUG")}')

    # 路径操作（跨平台拼接）
    joined = os.path.join('data', 'products', 'list.json')
    print(f'os.path.join: {joined}')
    print(f'os.path.dirname: {os.path.dirname(joined)}')
    print(f'os.path.basename: {os.path.basename(joined)}')
    print(f'os.path.splitext: {os.path.splitext(joined)}')

    # 当前工作目录
    print(f'os.getcwd(): {os.getcwd()}')
    print(f'os.name: {os.name}')  # Windows 为 'nt'，Linux/macOS 为 'posix'


def demo_sys() -> None:
    """sys 模块：解释器相关"""
    print('=== sys 模块 ===')
    print(f'sys.platform: {sys.platform}')
    print(f'sys.version: {sys.version.split()[0]}')
    print(f'Python 实现路径前缀: {sys.prefix}')
    print(f'sys.argv: {sys.argv}')
    # 模块搜索路径（前 3 条）
    print(f'sys.path[:3]: {sys.path[:3]}')


def demo_pathlib() -> None:
    """pathlib 模块：面向对象路径操作（推荐替代 os.path）"""
    print('=== pathlib 模块 ===')
    # / 运算符拼接路径
    p = Path('data') / 'products.json'
    print(f'Path 拼接: {p}')
    print(f'name={p.name}, stem={p.stem}, suffix={p.suffix}')
    print(f'parent={p.parent}')

    # 当前目录与主目录
    print(f'cwd: {Path.cwd()}')

    # 创建并写入临时文件演示
    demo_file = Path('stdlib_demo_tmp.txt')
    demo_file.write_text('hello pathlib\n中文测试', encoding='utf-8')
    print(f'写入文件: {demo_file} (exists={demo_file.exists()}, size={demo_file.stat().st_size} bytes)')
    content = demo_file.read_text(encoding='utf-8')
    print(f'读回内容: {content!r}')
    # 清理
    demo_file.unlink()
    print(f'删除后 exists={demo_file.exists()}')

    # glob 匹配当前目录下的 py 文件
    py_files = list(Path('.').glob('*.py'))
    print(f'当前目录 py 文件数: {len(py_files)}')


def demo_json() -> None:
    """json 模块：JSON 读写"""
    print('=== json 模块 ===')
    # 电商场景：商品数据
    products = [
        {'id': 1, 'name': '手机', 'price': 2999.0, 'stock': 100},
        {'id': 2, 'name': '耳机', 'price': 399.0, 'stock': 50},
    ]

    # 序列化为字符串
    # ensure_ascii=False 保留中文，indent=2 美化
    text = json.dumps(products, ensure_ascii=False, indent=2)
    print(f'JSON 字符串:\n{text}')

    # 反序列化
    obj = json.loads(text)
    print(f'反序列化类型: {type(obj).__name__}, 商品数: {len(obj)}')

    # 文件读写
    data_file = Path('products_tmp.json')
    data_file.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding='utf-8')
    loaded = json.loads(data_file.read_text(encoding='utf-8'))
    print(f'从文件读回: {loaded[0]["name"]}')
    data_file.unlink()


def demo_datetime() -> None:
    """datetime 模块：日期时间"""
    print('=== datetime 模块 ===')
    now = datetime.now()
    utc = datetime.now(timezone.utc)
    print(f'本地现在: {now}')
    print(f'UTC 现在: {utc}')

    # 格式化与解析
    fmt = '%Y-%m-%d %H:%M:%S'
    s = now.strftime(fmt)
    print(f'格式化: {s}')
    parsed = datetime.strptime('2026-07-30 10:30:00', fmt)
    print(f'解析: {parsed}')

    # timedelta 时间差
    today = date.today()
    week_later = today + timedelta(days=7)
    print(f'今天: {today}, 一周后: {week_later}, 差 { (week_later - today).days } 天')

    # 电商场景：订单创建时间
    order_created = datetime(2026, 7, 30, 14, 30, 0)
    age = now - order_created
    print(f'订单已存在 {age.total_seconds() / 3600:.1f} 小时')


def demo_collections() -> None:
    """collections 模块：容器扩展"""
    print('=== collections 模块 ===')
    # namedtuple 命名元组：电商商品
    Product = namedtuple('Product', ['id', 'name', 'price'])
    p = Product(1, '手机', 2999.0)
    print(f'namedtuple: {p}, p.name={p.name}, p.price={p.price}')

    # defaultdict 默认字典
    orders_by_customer = defaultdict(list)
    orders_by_customer['张三'].append(100)
    orders_by_customer['张三'].append(200)
    orders_by_customer['李四'].append(50)
    print(f'defaultdict: {dict(orders_by_customer)}')

    # Counter 计数器：统计商品分类
    categories = ['电子', '电子', '服装', '电子', '食品', '服装', '电子']
    counter = Counter(categories)
    print(f'Counter: {counter}')
    print(f'最多的分类: {counter.most_common(2)}')

    # deque 双端队列
    dq = deque([1, 2, 3])
    dq.appendleft(0)
    dq.append(4)
    print(f'deque: {dq}, popleft -> {dq.popleft()}')


def demo_random() -> None:
    """random 模块：随机数"""
    print('=== random 模块 ===')
    random.seed(42)  # 固定种子，结果可复现
    print(f'random(): {random.random():.4f}')
    print(f'randint(1, 100): {random.randint(1, 100)}')

    products = ['手机', '耳机', '键盘', '鼠标', '显示器']
    print(f'choice: {random.choice(products)}')
    print(f'sample 3: {random.sample(products, 3)}')

    # 模拟生成 5 笔订单金额
    amounts = [round(random.uniform(10, 1000), 2) for _ in range(5)]
    print(f'模拟订单金额: {amounts}')
    random.shuffle(amounts)
    print(f'打乱后: {amounts}')


def demo_math() -> None:
    """math 模块：数学运算"""
    print('=== math 模块 ===')
    print(f'ceil(3.2) = {math.ceil(3.2)}')
    print(f'floor(3.8) = {math.floor(3.8)}')
    print(f'sqrt(16) = {math.sqrt(16)}')
    print(f'pi = {math.pi:.6f}, e = {math.e:.6f}')
    print(f'factorial(5) = {math.factorial(5)}')
    print(f'gcd(12, 18) = {math.gcd(12, 18)}')
    print(f'log(100, 10) = {math.log(100, 10)}')

    # 电商场景：折扣计算
    price = 299.0
    discount = 0.85  # 85 折
    final = math.ceil(price * discount * 100) / 100  # 向上取整到分
    print(f'折扣价: {price} × {discount} → {final}')


def main() -> None:
    """主函数：依次演示各标准库"""
    demos = [
        demo_os, demo_sys, demo_pathlib, demo_json,
        demo_datetime, demo_collections, demo_random, demo_math,
    ]
    for demo in demos:
        demo()
        print()  # 空行分隔


if __name__ == '__main__':
    main()
