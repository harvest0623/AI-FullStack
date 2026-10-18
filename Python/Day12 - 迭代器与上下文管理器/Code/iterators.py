# 文件用途：自定义迭代器练习
# 实现 __iter__/__next__，演示迭代协议
# 电商场景：ProductIterator 遍历商品、PageIterator 分页迭代器、反向迭代器
# 运行方式：python iterators.py

from collections.abc import Iterable, Iterator


# ====== 模拟电商数据 ======
PRODUCTS = [
    {'id': 1, 'name': '手机', 'price': 2999.0, 'stock': 100, 'category': '电子'},
    {'id': 2, 'name': '蓝牙耳机', 'price': 399.0, 'stock': 50, 'category': '电子'},
    {'id': 3, 'name': '机械键盘', 'price': 599.0, 'stock': 30, 'category': '电子'},
    {'id': 4, 'name': '纯棉T恤', 'price': 89.0, 'stock': 200, 'category': '服装'},
    {'id': 5, 'name': '运动鞋', 'price': 459.0, 'stock': 80, 'category': '服装'},
    {'id': 6, 'name': '巧克力', 'price': 49.9, 'stock': 500, 'category': '食品'},
    {'id': 7, 'name': '鼠标垫', 'price': 29.9, 'stock': 300, 'category': '电子'},
]


# ====== 自定义迭代器：商品迭代器 ======
class ProductIterator:
    """商品迭代器：遍历商品列表

    实现 __iter__ 和 __next__ 双协议。
    """

    def __init__(self, products: list, reverse: bool = False):
        self._products = products
        self._reverse = reverse
        self._index = len(products) - 1 if reverse else 0

    def __iter__(self):
        # 迭代器的 __iter__ 返回自身
        return self

    def __next__(self):
        if self._reverse:
            if self._index < 0:
                raise StopIteration
            value = self._products[self._index]
            self._index -= 1
            return value
        else:
            if self._index >= len(self._products):
                raise StopIteration
            value = self._products[self._index]
            self._index += 1
            return value


# ====== 分页迭代器 ======
class PageIterator:
    """分页迭代器：每次产出一页

    可迭代对象风格：__iter__ 每次返回一个新的迭代器，
    因此可重复遍历（与上面的 ProductIterator 不同）。
    """

    def __init__(self, items: list, page_size: int = 3):
        self._items = items
        self._page_size = page_size

    def __iter__(self):
        # 每次迭代都从第 0 页开始，返回新的迭代器对象
        total = len(self._items)
        for start in range(0, total, self._page_size):
            page_num = start // self._page_size + 1
            page = self._items[start:start + self._page_size]
            yield {
                'page': page_num,
                'items': page,
                'count': len(page),
                'total': total,
            }


# ====== 反向迭代器：用 __reversed__ 支持 reversed() ======
class ReversedList:
    """支持 reversed() 的可迭代对象"""

    def __init__(self, items: list):
        self._items = items

    def __iter__(self):
        # 正向迭代
        return iter(self._items)

    def __reversed__(self):
        # 反向迭代：reversed() 调用此方法
        for i in range(len(self._items) - 1, -1, -1):
            yield self._items[i]


# ====== 演示函数 ======
def demo_iter_protocol() -> None:
    """迭代协议基础：iter() 与 next()"""
    print('=== 迭代协议基础 ===')
    lst = [1, 2, 3]

    # 列表是 Iterable，但不是 Iterator
    print(f'  list 是 Iterable: {isinstance(lst, Iterable)}')
    print(f'  list 是 Iterator: {isinstance(lst, Iterator)}')

    # 用 iter() 获取迭代器
    it = iter(lst)
    print(f'  iter(list) 是 Iterator: {isinstance(it, Iterator)}')
    print(f'  next: {next(it)}, {next(it)}, {next(it)}')

    # 耗尽后抛 StopIteration
    try:
        next(it)
    except StopIteration:
        print('  StopIteration（迭代器耗尽）')

    # next 带默认值
    it2 = iter([1])
    print(f'  带默认值: {next(it2, "空")}, {next(it2, "空")}')


def demo_for_loop_essence() -> None:
    """for 循环的本质"""
    print('=== for 循环的本质 ===')
    print('  for x in lst 等价于:')
    print('    it = iter(lst)')
    print('    while True:')
    print('        try: x = next(it)')
    print('        except StopIteration: break')

    # 手动模拟 for 循环
    lst = ['手机', '耳机', '键盘']
    it = iter(lst)
    while True:
        try:
            item = next(it)
            print(f'    处理: {item}')
        except StopIteration:
            break


def demo_product_iterator() -> None:
    """电商场景：商品迭代器"""
    print('=== 电商场景：商品迭代器 ===')
    # 正向遍历
    print('  正向遍历:')
    for p in ProductIterator(PRODUCTS):
        print(f'    {p["id"]}. {p["name"]} ¥{p["price"]}')

    # 反向遍历
    print('  反向遍历:')
    for p in ProductIterator(PRODUCTS, reverse=True):
        print(f'    {p["id"]}. {p["name"]} ¥{p["price"]}')


def demo_page_iterator() -> None:
    """电商场景：分页迭代器"""
    print('=== 电商场景：分页迭代器 ===')
    pager = PageIterator(PRODUCTS, page_size=3)

    # 可重复遍历（每次 __iter__ 返回新迭代器）
    print('  第一遍遍历:')
    for page in pager:
        print(f'    第{page["page"]}页: {page["count"]}件 - '
              f'{[p["name"] for p in page["items"]]}')

    print('  第二遍遍历（可重复）:')
    for page in pager:
        names = [p["name"] for p in page["items"]]
        print(f'    第{page["page"]}页: {names}')


def demo_reversed() -> None:
    """反向迭代器：reversed() 支持"""
    print('=== 反向迭代器 ===')
    rl = ReversedList(PRODUCTS)

    print('  正向 (for x in rl):')
    for p in rl:
        print(f'    {p["name"]}', end=' ')
    print()

    print('  反向 (reversed(rl)):')
    for p in reversed(rl):
        print(f'    {p["name"]}', end=' ')
    print()


def demo_iterator_exhaustion() -> None:
    """迭代器的一次性：耗尽即止"""
    print('=== 迭代器的一次性 ===')
    it = iter([10, 20, 30])
    print(f'  第一次遍历: {list(it)}')
    print(f'  第二次遍历: {list(it)}  ← 空了！')

    # 可迭代对象（如列表）每次 for 都新建迭代器，可重复
    lst = [10, 20, 30]
    print(f'  列表第一次: {list(lst)}')
    print(f'  列表第二次: {list(lst)}  ← 可重复')


def demo_eshop_stock_check() -> None:
    """电商场景：用迭代器检查库存"""
    print('=== 电商场景：库存检查迭代器 ===')

    class LowStockIterator:
        """低库存商品迭代器：只产出库存低于阈值的商品"""

        def __init__(self, products: list, threshold: int = 50):
            self._products = products
            self._threshold = threshold
            self._index = 0

        def __iter__(self):
            return self

        def __next__(self):
            while self._index < len(self._products):
                p = self._products[self._index]
                self._index += 1
                if p['stock'] < self._threshold:
                    return p
            raise StopIteration

    print(f'  库存低于 50 的商品:')
    for p in LowStockIterator(PRODUCTS, threshold=50):
        print(f'    {p["name"]}: 仅剩 {p["stock"]} 件')


def main() -> None:
    demos = [
        demo_iter_protocol,
        demo_for_loop_essence,
        demo_product_iterator,
        demo_page_iterator,
        demo_reversed,
        demo_iterator_exhaustion,
        demo_eshop_stock_check,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
