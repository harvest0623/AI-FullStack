# 文件用途：生成器练习
# 演示 yield 基础、next/send、yield from、无限生成器
# 电商场景：大数据商品列表分页生成器、订单流处理
# 运行方式：python generators.py

import sys
from itertools import islice


# ====== yield 基础 ======
def simple_gen():
    """简单生成器：逐个产出值"""
    print('  生成器启动')
    yield 1
    print('  产出 1 后')
    yield 2
    print('  产出 2 后')
    yield 3
    print('  产出 3 后（即将结束）')


def demo_yield_basic() -> None:
    """yield 基础：惰性求值"""
    print('=== yield 基础 ===')
    g = simple_gen()       # 创建生成器，不执行任何代码
    print(f'生成器类型: {type(g).__name__}')
    print(f'大小: {sys.getsizeof(g)} bytes')

    print('调用 next(g):')
    print(f'  得到: {next(g)}')   # 打印"生成器启动"，返回 1
    print(f'  得到: {next(g)}')   # 打印"产出 1 后"，返回 2
    print(f'  得到: {next(g)}')   # 打印"产出 2 后"，返回 3

    # 第 4 次 next 会抛 StopIteration
    try:
        next(g)
    except StopIteration:
        print('  生成器已耗尽（StopIteration）')


def demo_generator_vs_list() -> None:
    """生成器 vs 列表：内存对比"""
    print('=== 生成器 vs 列表（内存对比） ===')
    n = 1_000_000
    lst = [x for x in range(n)]
    gen = (x for x in range(n))

    print(f'  列表大小: {sys.getsizeof(lst):,} bytes（约 {sys.getsizeof(lst)/1024/1024:.1f} MB）')
    print(f'  生成器大小: {sys.getsizeof(gen)} bytes')
    print(f'  内存差距: {sys.getsizeof(lst) // sys.getsizeof(gen)} 倍')

    # 生成器只能遍历一次
    gen2 = (x for x in range(3))
    print(f'  第一次遍历: {list(gen2)}')
    print(f'  第二次遍历: {list(gen2)}  ← 空了！生成器只能用一次')


# ====== send() 与生成器交互 ======
def accumulator():
    """累加器生成器：接收 send 的值并累加"""
    total = 0
    while True:
        # yield 返回当前 total，并暂停等待 send 进来的 value
        value = yield total
        if value is None:
            break
        total += value


def demo_send() -> None:
    """send() 与生成器交互"""
    print('=== send() 与生成器交互 ===')
    acc = accumulator()

    # 启动生成器（必须先 next 或 send(None)）
    initial = next(acc)
    print(f'  启动，初始值: {initial}')

    # send 传值
    print(f'  send(10) → {acc.send(10)}')
    print(f'  send(20) → {acc.send(20)}')
    print(f'  send(5)  → {acc.send(5)}')

    # 关闭生成器
    acc.close()
    print('  生成器已关闭')


# ====== yield from 委托生成器 ======
def flatten(nested):
    """扁平化嵌套列表：yield from 递归委托"""
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)   # 委托给子生成器
        else:
            yield item


def chunked(iterable, size):
    """分块生成器：用 yield from 委托"""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield from chunk           # 逐个产出 chunk 里的元素
            chunk = []
    if chunk:
        yield from chunk


def demo_yield_from() -> None:
    """yield from 委托生成器"""
    print('=== yield from 委托 ===')
    nested = [1, [2, [3, 4], 5], 6, [7, 8]]
    flat = list(flatten(nested))
    print(f'  嵌套 {nested} → 扁平化 {flat}')

    # 用 yield from 拼接多个生成器
    def gen1():
        yield from [1, 2, 3]

    def gen2():
        yield from [4, 5, 6]

    def combined():
        yield from gen1()
        yield from gen2()

    print(f'  组合生成器: {list(combined())}')


# ====== 无限生成器 ======
def counter(start: int = 0, step: int = 1):
    """无限计数器"""
    i = start
    while True:
        yield i
        i += step


def fibonacci():
    """无限斐波那契数列"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def demo_infinite() -> None:
    """无限生成器"""
    print('=== 无限生成器 ===')
    # 用 islice 取有限个，避免无限循环
    print(f'  counter 从 10 起: {list(islice(counter(10), 5))}')
    print(f'  counter 步长 2: {list(islice(counter(0, 2), 8))}')
    print(f'  fibonacci 前 10: {list(islice(fibonacci(), 10))}')

    # 销售编号生成器
    def order_id_gen(start: int = 1001):
        while True:
            yield start
            start += 1

    ids = order_id_gen()
    print(f'  订单编号: {[next(ids) for _ in range(5)]}')


# ====== 电商场景：分页生成器 ======
def paginate_products(products: list, page_size: int = 10):
    """商品分页生成器：每次产出一页

    惰性产出，调用方按需取页，不一次性返回全部。
    """
    total = len(products)
    for start in range(0, total, page_size):
        page_num = start // page_size + 1
        page = products[start:start + page_size]
        yield {
            'page': page_num,
            'items': page,
            'total': total,
            'has_next': start + page_size < total,
        }


def demo_eshop_pagination() -> None:
    """电商场景：大数据商品列表分页"""
    print('=== 电商场景：商品分页生成器 ===')
    # 模拟 25 件商品
    products = [
        {'id': i, 'name': f'商品{i:02d}', 'price': i * 10}
        for i in range(1, 26)
    ]

    # 分页，每页 10 件
    for page in paginate_products(products, page_size=10):
        print(f'  第 {page["page"]} 页: {len(page["items"])} 件，'
              f'有下一页={page["has_next"]}')
        for item in page['items'][:3]:   # 只展示前 3 件
            print(f'    {item}')
        if len(page['items']) > 3:
            print(f'    ... 还有 {len(page["items"]) - 3} 件')


def demo_eshop_order_stream() -> None:
    """电商场景：订单流处理"""
    print('=== 电商场景：订单流处理 ===')

    def order_stream(n: int):
        """生成 n 笔模拟订单（流式）"""
        for i in range(1, n + 1):
            yield {
                'order_id': 1000 + i,
                'amount': round((i * 37.5) % 500 + 10, 2),
                'status': 'paid' if i % 5 else 'pending',
            }

    # 流式统计：不一次性载入所有订单
    total = 0.0
    paid_count = 0
    pending_count = 0

    for order in order_stream(1000):
        total += order['amount']
        if order['status'] == 'paid':
            paid_count += 1
        else:
            pending_count += 1

    print(f'  处理 1000 笔订单:')
    print(f'    总金额: ¥{total:.2f}')
    print(f'    已支付: {paid_count} 笔')
    print(f'    待处理: {pending_count} 笔')
    print(f'  （全程内存只保留 1 笔订单）')


def main() -> None:
    demos = [
        demo_yield_basic,
        demo_generator_vs_list,
        demo_send,
        demo_yield_from,
        demo_infinite,
        demo_eshop_pagination,
        demo_eshop_order_stream,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
