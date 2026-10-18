# 文件用途：itertools 练习
# 演示 chain/combinations/permutations/product/groupby/islice/count/cycle/repeat/accumulate
# 电商场景：商品组合推荐、按分类分组、批量处理
# 运行方式：python itertools_demo.py

from itertools import (
    chain, combinations, permutations, product, groupby,
    islice, count, cycle, repeat, accumulate,
    takewhile, dropwhile,
)


# ====== 模拟电商数据 ======
PRODUCTS = [
    {'id': 1, 'name': '手机', 'price': 2999.0, 'category': '电子'},
    {'id': 2, 'name': '耳机', 'price': 399.0, 'category': '电子'},
    {'id': 3, 'name': '键盘', 'price': 599.0, 'category': '电子'},
    {'id': 4, 'name': 'T恤', 'price': 89.0, 'category': '服装'},
    {'id': 5, 'name': '运动鞋', 'price': 459.0, 'category': '服装'},
    {'id': 6, 'name': '巧克力', 'price': 49.9, 'category': '食品'},
]


# ====== 演示函数 ======
def demo_chain() -> None:
    """chain：串联多个迭代器"""
    print('=== chain 串联 ===')
    electronics = ['手机', '耳机', '键盘']
    clothing = ['T恤', '运动鞋']
    food = ['巧克力']

    # 串联三个列表为一个迭代器
    all_products = chain(electronics, clothing, food)
    print(f'  串联: {list(all_products)}')

    # chain.from_iterable 接收一个可迭代对象的可迭代对象
    groups = [electronics, clothing, food]
    print(f'  from_iterable: {list(chain.from_iterable(groups))}')


def demo_combinations() -> None:
    """combinations：组合 C(n,r)"""
    print('=== combinations 组合 ===')
    # 从 3 个商品中选 2 个的组合（不重复，顺序无关）
    items = ['A', 'B', 'C']
    combos = list(combinations(items, 2))
    print(f'  C(3,2) = {len(combos)}: {combos}')

    # 电商场景：商品套餐组合
    print('  电商场景：从 4 件商品选 2 件组成套餐')
    products = ['手机', '耳机', '键盘', '鼠标']
    for combo in combinations(products, 2):
        print(f'    套餐: {" + ".join(combo)}')


def demo_permutations() -> None:
    """permutations：排列 P(n,r)"""
    print('=== permutations 排列 ===')
    items = ['A', 'B', 'C']
    perms = list(permutations(items, 2))
    print(f'  P(3,2) = {len(perms)}: {perms}')

    # 电商场景：首页推荐位排列
    print('  电商场景：3 个商品在 2 个推荐位的排列')
    products = ['爆款A', '爆款B', '爆款C']
    for i, perm in enumerate(permutations(products, 2), start=1):
        print(f'    方案{i}: 位1={perm[0]}, 位2={perm[1]}')


def demo_product() -> None:
    """product：笛卡尔积"""
    print('=== product 笛卡尔积 ===')
    # 颜色 × 尺寸
    colors = ['红', '蓝']
    sizes = ['S', 'M', 'L']
    sku_list = list(product(colors, sizes))
    print(f'  颜色×尺寸 = {len(sku_list)} 个 SKU:')
    for color, size in sku_list:
        print(f'    {color}-{size}')

    # repeat 参数
    print(f'  product("AB", repeat=2): {list(product("AB", repeat=2))}')


def demo_groupby() -> None:
    """groupby：分组（需先按 key 排序）"""
    print('=== groupby 分组 ===')
    # groupby 只对连续相同的 key 分组，所以必须先排序
    sorted_products = sorted(PRODUCTS, key=lambda p: p['category'])

    print('  电商场景：按分类分组')
    for category, group in groupby(sorted_products, key=lambda p: p['category']):
        names = [p['name'] for p in group]
        print(f'    [{category}] {names}')

    # 不排序会怎样：相邻同组才合并
    print('  不排序（相邻同组才合并）:')
    for cat, group in groupby(PRODUCTS, key=lambda p: p['category']):
        print(f'    [{cat}] {[p["name"] for p in group]}')


def demo_islice() -> None:
    """islice：切片（对迭代器取前 N 个）"""
    print('=== islice 切片 ===')
    # 取前 3 个
    print(f'  range(10) 前 3: {list(islice(range(10), 3))}')
    # 带起止
    print(f'  range(10) [2:5]: {list(islice(range(10), 2, 5))}')
    # 带步长
    print(f'  range(10) [0:10:2]: {list(islice(range(10), 0, 10, 2))}')

    # 电商场景：商品列表分页（取第 2 页，每页 3 件）
    print('  电商场景：取第 2 页（每页 3 件）')
    page2 = list(islice(PRODUCTS, 3, 6))
    for p in page2:
        print(f'    {p["name"]}')


def demo_count() -> None:
    """count：无限计数"""
    print('=== count 无限计数 ===')
    # count(start, step)：无限序列
    print(f'  count(10) 前 5: {list(islice(count(10), 5))}')
    print(f'  count(0, 2) 前 5: {list(islice(count(0, 2), 5))}')
    print(f'  count(100, -5) 前 5: {list(islice(count(100, -5), 5))}')

    # 电商场景：生成订单号
    print('  电商场景：生成订单号')
    order_ids = (f'ORD-{i:06d}' for i in count(1))
    for oid in islice(order_ids, 3):
        print(f'    {oid}')


def demo_cycle() -> None:
    """cycle：无限循环"""
    print('=== cycle 无限循环 ===')
    # cycle 把可迭代对象无限循环
    statuses = ['paid', 'shipped', 'delivered']
    print(f'  cycle({statuses}) 前 7: {list(islice(cycle(statuses), 7))}')

    # 电商场景：轮询分配客服
    print('  电商场景：轮询分配客服')
    agents = ['客服A', '客服B', '客服C']
    customers = ['张三', '李四', '王五', '赵六', '钱七']
    for customer, agent in zip(customers, cycle(agents)):
        print(f'    {customer} → {agent}')


def demo_repeat() -> None:
    """repeat：重复"""
    print('=== repeat 重复 ===')
    print(f'  repeat("x", 3): {list(repeat("x", 3))}')
    # 不指定次数则无限
    print(f'  repeat(0) 前 4: {list(islice(repeat(0), 4))}')

    # 配合 map 使用
    squares = list(map(pow, range(5), repeat(2)))   # 0²,1²,2²,3²,4²
    print(f'  map(pow, range(5), repeat(2)): {squares}')


def demo_accumulate() -> None:
    """accumulate：累积"""
    print('=== accumulate 累积 ===')
    nums = [1, 2, 3, 4, 5]
    print(f'  求和累积: {list(accumulate(nums))}')

    # 自定义累积函数：累积乘
    import operator
    print(f'  累积乘: {list(accumulate(nums, operator.mul))}')

    # 电商场景：累计销售额
    daily_sales = [100, 200, 150, 300, 250]
    cumulative = list(accumulate(daily_sales))
    print(f'  电商场景：每日销售额 {daily_sales}')
    print(f'    累计销售额: {cumulative}')


def demo_takewhile_dropwhile() -> None:
    """takewhile / dropwhile：条件取/舍"""
    print('=== takewhile / dropwhile ===')
    nums = [1, 2, 3, 4, 1, 2]

    # takewhile：取到条件为 False 为止
    print(f'  takewhile(<4, {nums}): {list(takewhile(lambda x: x < 4, nums))}')
    # dropwhile：丢到条件为 False 为止
    print(f'  dropwhile(<4, {nums}): {list(dropwhile(lambda x: x < 4, nums))}')

    # 电商场景：取价格低于 500 的商品（直到遇到贵的）
    prices = [89, 399, 459, 2999, 100]
    print(f'  价格列表: {prices}')
    print(f'  takewhile(<500): {list(takewhile(lambda x: x < 500, prices))}')
    print(f'  dropwhile(<500): {list(dropwhile(lambda x: x < 500, prices))}')


def demo_eshop_combo_recommend() -> None:
    """电商场景：商品组合推荐（总价不超预算）"""
    print('=== 电商场景：组合推荐（预算 3000） ===')
    budget = 3000
    candidates = [
        ('手机', 2999), ('耳机', 399), ('键盘', 599),
        ('鼠标', 99), ('鼠标垫', 30),
    ]

    # 从 5 件商品中选 2 件，总价不超 3000 的组合
    print(f'  候选: {candidates}')
    print(f'  预算: ¥{budget}')
    valid_combos = []
    for combo in combinations(candidates, 2):
        total = sum(p[1] for p in combo)
        if total <= budget:
            valid_combos.append((combo, total))

    print(f'  有效组合（{len(valid_combos)} 个）:')
    for combo, total in sorted(valid_combos, key=lambda x: x[1]):
        names = ' + '.join(p[0] for p in combo)
        print(f'    {names} = ¥{total}')


def main() -> None:
    demos = [
        demo_chain,
        demo_combinations,
        demo_permutations,
        demo_product,
        demo_groupby,
        demo_islice,
        demo_count,
        demo_cycle,
        demo_repeat,
        demo_accumulate,
        demo_takewhile_dropwhile,
        demo_eshop_combo_recommend,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
