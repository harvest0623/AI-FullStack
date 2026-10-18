# 文件用途：文件 IO 练习
# 演示 open 读写、with 语句、逐行读取大文件、pathlib 读写
# 电商场景：读写商品列表到文件、日志文件追加
# 运行方式：python file_io.py

from pathlib import Path


# ====== 基本读写 ======
def demo_basic_write_read() -> None:
    """基本写读：w 模式覆盖、r 模式读取"""
    print('=== 基本写读 ===')
    path = Path('data') / 'basic.txt'
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写文件（覆盖模式）
    with open(path, 'w', encoding='utf-8') as f:
        f.write('第一行：商品入库\n')
        f.write('第二行：订单生成\n')
        f.writelines(['第三行：发货\n', '第四行：签收\n'])

    # 读文件
    with open(path, encoding='utf-8') as f:
        content = f.read()
    print(f'全部内容:\n{content}')

    # 再次 w 模式会覆盖
    with open(path, 'w', encoding='utf-8') as f:
        f.write('已覆盖\n')
    print(f'覆盖后: {path.read_text(encoding="utf-8")}')


def demo_append_mode() -> None:
    """追加模式：日志追加"""
    print('=== 追加模式（日志） ===')
    log_path = Path('data') / 'access.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 多次追加，模拟日志写入
    from datetime import datetime
    for i in range(3):
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().strftime("%H:%M:%S")}] 第 {i+1} 条日志\n')

    print(f'日志内容:\n{log_path.read_text(encoding="utf-8")}')


def demo_read_methods() -> None:
    """读取方式对比：read / readline / readlines / 迭代"""
    print('=== 读取方式 ===')
    path = Path('data') / 'lines.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('苹果\n香蕉\n橙子\n葡萄\n', encoding='utf-8')

    # read() 一次读全部
    with open(path, encoding='utf-8') as f:
        print(f'read(): {f.read()!r}')

    # readline() 读一行
    with open(path, encoding='utf-8') as f:
        print(f'readline(): {f.readline()!r}')

    # readlines() 读所有行成列表
    with open(path, encoding='utf-8') as f:
        print(f'readlines(): {f.readlines()}')

    # 迭代文件对象（大文件首选）
    with open(path, encoding='utf-8') as f:
        print('迭代:', [line.strip() for line in f])


def demo_large_file() -> None:
    """大文件逐行处理：内存友好"""
    print('=== 大文件逐行处理 ===')
    path = Path('data') / 'large_orders.log'
    path.parent.mkdir(parents=True, exist_ok=True)

    # 生成 1000 行模拟数据
    with open(path, 'w', encoding='utf-8') as f:
        for i in range(1, 1001):
            f.write(f'order_{i}|customer_{i % 50}|{i * 10.5:.2f}\n')
    print(f'已生成 {path.stat().st_size} 字节日志')

    # 逐行读取统计（内存只保留一行）
    total = 0.0
    count = 0
    with open(path, encoding='utf-8') as f:
        for line in f:                 # 逐行迭代，不一次性载入
            _, _, amount_str = line.strip().split('|')
            total += float(amount_str)
            count += 1
    print(f'共 {count} 笔订单，总额 {total:.2f}，平均 {total / count:.2f}')


def demo_pathlib_io() -> None:
    """pathlib 读写：简洁的 API"""
    print('=== pathlib 读写 ===')
    p = Path('data') / 'config.txt'
    p.parent.mkdir(parents=True, exist_ok=True)

    # 一次写完
    p.write_text('eshop 配置\nversion=1.0\ndebug=true\n', encoding='utf-8')
    # 一次读完
    text = p.read_text(encoding='utf-8')
    print(f'配置:\n{text}')

    # 二进制读写
    p2 = Path('data') / 'flag.bin'
    p2.write_bytes(b'\x89PNG\r\n\x1a\n')
    print(f'二进制: {p2.read_bytes()!r}')


def demo_eshop_products() -> None:
    """电商场景：读写商品列表到纯文本文件"""
    print('=== 电商场景：商品列表 ===')
    products = [
        ('手机', 2999.0, 100),
        ('耳机', 399.0, 50),
        ('键盘', 599.0, 30),
    ]

    path = Path('data') / 'products.txt'
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写：每行一个商品，字段用 | 分隔
    with open(path, 'w', encoding='utf-8') as f:
        for name, price, stock in products:
            f.write(f'{name}|{price}|{stock}\n')

    # 读：解析回结构
    loaded = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            name, price_str, stock_str = line.strip().split('|')
            loaded.append((name, float(price_str), int(stock_str)))

    print('读回的商品:')
    for name, price, stock in loaded:
        print(f'  {name}: ¥{price} 库存{stock}')


def main() -> None:
    demos = [
        demo_basic_write_read,
        demo_append_mode,
        demo_read_methods,
        demo_large_file,
        demo_pathlib_io,
        demo_eshop_products,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
