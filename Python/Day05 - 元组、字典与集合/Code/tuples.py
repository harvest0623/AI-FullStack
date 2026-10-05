# 文件用途：元组 tuple 练习，演示元组的创建、索引、解包、namedtuple 等用法
# 电商场景：商品记录用元组存储、函数多返回值、坐标 namedtuple

from collections import namedtuple


# ============ 1. 元组创建 ============
def demo_create():
    """演示元组的各种创建方式"""
    print("===== 1. 元组创建 =====")

    # 空元组
    empty1 = ()
    empty2 = tuple()
    print(f"空元组: {empty1}, 类型: {type(empty1).__name__}")

    # 多元素元组
    t1 = (1, 2, 3)
    t2 = 1, 2, 3              # 括号可省略
    print(f"多元素元组: {t1} == {t2} -> {t1 == t2}")

    # 单元素元组——必须带逗号！
    single_ok = (1,)          # 正确
    single_bad = (1)          # 这只是整数 1
    print(f"单元素元组 (1,): {single_ok}, 类型: {type(single_ok).__name__}")
    print(f"非元组 (1): {single_bad}, 类型: {type(single_bad).__name__}")

    # tuple() 转换
    from_list = tuple([1, 2, 3])
    from_str = tuple("abc")
    print(f"从列表转换: {from_list}")
    print(f"从字符串转换: {from_str}")


# ============ 2. 不可变性与"可变元素"陷阱 ============
def demo_immutable():
    """演示元组的不可变性，以及元素是可变对象时的特殊情况"""
    print("\n===== 2. 不可变性 =====")

    t = (1, 2, 3)
    # t[0] = 10  # TypeError: 'tuple' object does not support item assignment

    # 元组本身不可变，但元素若是可变对象，元素自身仍可修改
    t2 = ([1, 2], [3, 4])
    print(f"修改前: {t2}")
    t2[0].append(99)          # 合法！修改的是列表，不是元组的引用
    print(f"修改后: {t2}")

    # 元组不能增删元素
    # t.append(4)     # AttributeError
    # del t[0]         # TypeError


# ============ 3. 索引与切片 ============
def demo_index_slice():
    """演示元组的索引和切片，与列表一致"""
    print("\n===== 3. 索引与切片 =====")

    # 电商场景：商品记录元组 (id, name, price, stock)
    product = ("P001", "iPhone 15", 5999.0, 50)
    print(f"商品记录: {product}")
    print(f"商品ID: {product[0]}")
    print(f"商品名: {product[1]}")
    print(f"最后一个元素: {product[-1]}")

    # 切片
    info = product[:2]        # 取前两个字段
    print(f"前两字段切片: {info}")
    print(f"反转: {product[::-1]}")

    # 元组的 count / index
    nums = (1, 2, 2, 3, 2)
    print(f"\nnums={nums}, 2出现次数: {nums.count(2)}, 首个2的索引: {nums.index(2)}")


# ============ 4. 打包与解包 ============
def demo_pack_unpack():
    """演示元组的打包与解包"""
    print("\n===== 4. 打包与解包 =====")

    # 打包：电商场景——一次函数调用返回多个统计值
    stats = ("electronics", 120, 58000.0)   # (分类, 订单数, 总销售额)
    print(f"打包 stats: {stats}")

    # 解包
    category, count, total = stats
    print(f"解包: category={category}, count={count}, total={total}")

    # 扩展解包：用 * 收集剩余
    first, *rest = (1, 2, 3, 4, 5)
    print(f"first={first}, rest={rest}")

    head, *middle, tail = (10, 20, 30, 40, 50)
    print(f"head={head}, middle={middle}, tail={tail}")

    # 用 _ 忽略不需要的值
    name, _, price = ("鼠标", "描述", 99.0)
    print(f"忽略中间值: name={name}, price={price}")


# ============ 5. 函数多返回值（本质是返回元组）============
def calc_order_summary(items: list[tuple[float, int]]) -> tuple[int, float, float]:
    """计算订单汇总：返回 (商品数, 总价, 平均价)——本质返回一个元组"""
    total_qty = sum(qty for _, qty in items)
    total_price = sum(price * qty for price, qty in items)
    avg_price = total_price / total_qty if total_qty else 0
    return total_qty, total_price, avg_price    # 返回元组


def demo_multi_return():
    """演示函数多返回值"""
    print("\n===== 5. 函数多返回值 =====")
    # items: [(单价, 数量), ...]
    items = [(5999.0, 2), (199.0, 3), (49.0, 5)]
    qty, total, avg = calc_order_summary(items)
    print(f"订单商品数: {qty}")
    print(f"订单总价: {total:.2f}")
    print(f"平均单价: {avg:.2f}")


# ============ 6. namedtuple 命名元组 ============
# 定义商品记录的命名元组，比普通元组更可读
Product = namedtuple("Product", ["id", "name", "price", "stock", "category"])

# 坐标 namedtuple
Point = namedtuple("Point", ["x", "y"])
# 3.7+ 可用 typing.NamedTuple 写类型注解，这里先用 namedtuple


def demo_namedtuple():
    """演示 namedtuple 的用法"""
    print("\n===== 6. namedtuple =====")

    # 创建商品
    p = Product(id="P001", name="iPhone 15", price=5999.0, stock=50, category="phone")
    print(f"商品: {p}")

    # 用字段名访问，比 p[0] / p[1] 清晰得多
    print(f"名称: {p.name}, 价格: {p.price}, 库存: {p.stock}")

    # 仍然支持下标访问
    print(f"下标访问 p[0]: {p[0]}")

    # _asdict() 转为字典
    print(f"_asdict(): {p._asdict()}")

    # _replace() 创建新实例（元组不可变，只能替换生成新的）
    p_updated = p._replace(stock=40)
    print(f"更新库存后: {p_updated}")
    print(f"原对象不变: {p}")

    # _fields 查看所有字段名
    print(f"所有字段: {Product._fields}")

    # 坐标示例
    pt1 = Point(3, 4)
    pt2 = Point(0, 0)
    dist = ((pt1.x - pt2.x) ** 2 + (pt1.y - pt2.y) ** 2) ** 0.5
    print(f"\n点 {pt1} 到 {pt2} 的距离: {dist}")


# ============ 7. 元组作字典键 ============
def demo_tuple_as_key():
    """演示元组可哈希、可作字典键"""
    print("\n===== 7. 元组作字典键 =====")

    # 电商场景：用 (年份, 月份) 作键存储销售额
    sales = {
        (2024, 1): 120000,
        (2024, 2): 135000,
        (2024, 3): 158000,
    }
    print(f"2024年2月销售额: {sales[(2024, 2)]}")

    # 列表不能作键（不可哈希）
    # sales_list = {[2024, 1]: 120000}  # TypeError: unhashable type: 'list'


# ============ 8. 元组 vs 列表 性能与语义 ============
def demo_tuple_vs_list():
    """对比元组与列表"""
    print("\n===== 8. 元组 vs 列表 =====")

    import sys

    lst = [1, 2, 3, 4, 5]
    tup = (1, 2, 3, 4, 5)
    print(f"列表内存: {sys.getsizeof(lst)} bytes")
    print(f"元组内存: {sys.getsizeof(tup)} bytes")

    # 语义对比：
    # - 列表：同质、可变序列，如 [1,2,3,4,5] 一组数字
    # - 元组：异质、不可变记录，如 ("P001", "iPhone", 5999, 50) 一条记录


if __name__ == "__main__":
    demo_create()
    demo_immutable()
    demo_index_slice()
    demo_pack_unpack()
    demo_multi_return()
    demo_namedtuple()
    demo_tuple_as_key()
    demo_tuple_vs_list()
    print("\n✅ 元组练习全部完成")
