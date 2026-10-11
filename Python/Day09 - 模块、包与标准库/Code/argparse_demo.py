# 文件用途：argparse 命令行工具演示
# 电商场景：eshop CLI 工具，支持 --product/--order/--export 与子命令 subparsers
# 运行示例：
#   python argparse_demo.py --help
#   python argparse_demo.py product list
#   python argparse_demo.py product search --name 手机
#   python argparse_demo.py order stats --top 3
#   python argparse_demo.py export --format json --output out.json

import argparse
import json
import sys
from pathlib import Path
from collections import Counter


# ====== 模拟电商数据 ======
PRODUCTS = [
    {'id': 1, 'name': '手机', 'price': 2999.0, 'stock': 100, 'category': '电子'},
    {'id': 2, 'name': '蓝牙耳机', 'price': 399.0, 'stock': 50, 'category': '电子'},
    {'id': 3, 'name': '机械键盘', 'price': 599.0, 'stock': 30, 'category': '电子'},
    {'id': 4, 'name': '纯棉T恤', 'price': 89.0, 'stock': 200, 'category': '服装'},
    {'id': 5, 'name': '运动鞋', 'price': 459.0, 'stock': 80, 'category': '服装'},
    {'id': 6, 'name': '巧克力', 'price': 49.9, 'stock': 500, 'category': '食品'},
]

ORDERS = [
    {'id': 1001, 'customer': '张三', 'product_id': 1, 'qty': 2, 'total': 5998.0},
    {'id': 1002, 'customer': '李四', 'product_id': 2, 'qty': 3, 'total': 1197.0},
    {'id': 1003, 'customer': '张三', 'product_id': 4, 'qty': 5, 'total': 445.0},
    {'id': 1004, 'customer': '王五', 'product_id': 3, 'qty': 1, 'total': 599.0},
    {'id': 1005, 'customer': '李四', 'product_id': 6, 'qty': 10, 'total': 499.0},
    {'id': 1006, 'customer': '张三', 'product_id': 5, 'qty': 2, 'total': 918.0},
]


# ====== product 子命令实现 ======
def cmd_product_list(args: argparse.Namespace) -> None:
    """列出商品"""
    products = PRODUCTS
    # 按分类过滤
    if args.category:
        products = [p for p in products if p['category'] == args.category]
    # 限制数量
    products = products[: args.limit]

    print(f'商品列表（共 {len(products)} 件，limit={args.limit}）')
    print('-' * 60)
    print(f'{"ID":<6}{"名称":<12}{"价格":<10}{"库存":<8}{"分类"}')
    print('-' * 60)
    for p in products:
        print(f'{p["id"]:<6}{p["name"]:<12}{p["price"]:<10}{p["stock"]:<8}{p["category"]}')


def cmd_product_search(args: argparse.Namespace) -> None:
    """按名称搜索商品"""
    keyword = args.name
    matched = [p for p in PRODUCTS if keyword in p['name']]
    if not matched:
        print(f'未找到包含 "{keyword}" 的商品')
        return
    print(f'搜索 "{keyword}" 命中 {len(matched)} 件商品：')
    for p in matched:
        print(f'  #{p["id"]} {p["name"]} ¥{p["price"]} 库存{p["stock"]}')


# ====== order 子命令实现 ======
def cmd_order_stats(args: argparse.Namespace) -> None:
    """订单统计：按客户聚合，取 top N"""
    # 按客户聚合
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for o in ORDERS:
        totals[o['customer']] = totals.get(o['customer'], 0) + o['total']
        counts[o['customer']] = counts.get(o['customer'], 0) + 1

    # 按金额排序取 top
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    top = ranked[: args.top]

    print(f'订单统计 TOP {args.top} 客户')
    print('-' * 50)
    print(f'{"排名":<6}{"客户":<10}{"订单数":<10}{"消费总额"}')
    print('-' * 50)
    for rank, (customer, total) in enumerate(top, start=1):
        print(f'{rank:<6}{customer:<10}{counts[customer]:<10}¥{total:.2f}')

    # 用 Counter 演示
    counter = Counter(o['customer'] for o in ORDERS)
    print(f'\n客户订单频次: {dict(counter)}')


# ====== export 子命令实现 ======
def cmd_export(args: argparse.Namespace) -> None:
    """导出数据到文件"""
    fmt = args.format
    output = Path(args.output)

    if fmt == 'json':
        data = {'products': PRODUCTS, 'orders': ORDERS}
        output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f'已导出 JSON 到 {output}（商品 {len(PRODUCTS)} 件，订单 {len(ORDERS)} 笔）')
    elif fmt == 'csv':
        import csv
        with output.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'price', 'stock', 'category'])
            writer.writeheader()
            for p in PRODUCTS:
                writer.writerow(p)
        print(f'已导出 CSV 到 {output}（商品 {len(PRODUCTS)} 件）')
    else:
        print(f'不支持的格式: {fmt}（可选 json / csv）')
        sys.exit(1)


# ====== 构建解析器 ======
def build_parser() -> argparse.ArgumentParser:
    """构建 eshop CLI 解析器，含子命令"""
    parser = argparse.ArgumentParser(
        prog='eshop',
        description='eshop 电商数据处理 CLI 工具',
        epilog='示例：eshop product list --category 电子',
    )
    # 全局参数
    parser.add_argument('--verbose', action='store_true', help='输出详细日志')
    parser.add_argument('--version', action='version', version='eshop 1.0.0')

    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用子命令', required=True)

    # ---- product 子命令 ----
    product_parser = subparsers.add_parser('product', help='商品管理')
    product_sub = product_parser.add_subparsers(dest='product_action', help='商品子操作', required=True)

    # product list
    p_list = product_sub.add_parser('list', help='列出商品')
    p_list.add_argument('--category', help='按分类过滤（电子/服装/食品）')
    p_list.add_argument('--limit', type=int, default=10, help='返回数量上限（默认 10）')
    p_list.set_defaults(func=cmd_product_list)

    # product search
    p_search = product_sub.add_parser('search', help='按名称搜索商品')
    p_search.add_argument('--name', required=True, help='商品名称关键词')
    p_search.set_defaults(func=cmd_product_search)

    # ---- order 子命令 ----
    order_parser = subparsers.add_parser('order', help='订单管理')
    order_sub = order_parser.add_subparsers(dest='order_action', help='订单子操作', required=True)

    # order stats
    o_stats = order_sub.add_parser('stats', help='订单统计')
    o_stats.add_argument('--top', type=int, default=5, help='取消费额前 N 名客户（默认 5）')
    o_stats.set_defaults(func=cmd_order_stats)

    # ---- export 子命令 ----
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='导出格式（默认 json）')
    export_parser.add_argument('--output', default='export.json', help='输出文件路径')
    export_parser.set_defaults(func=cmd_export)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 全局 verbose 标志
    if getattr(args, 'verbose', False):
        print(f'[debug] 解析到的参数: {vars(args)}')

    # 调用子命令对应的处理函数
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # 未指定子操作时打印帮助
        parser.print_help()


if __name__ == '__main__':
    main()
