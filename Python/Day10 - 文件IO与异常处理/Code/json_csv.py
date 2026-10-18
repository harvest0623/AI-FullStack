# 文件用途：JSON 与 CSV 读写练习
# 演示 json dump/load、csv DictReader/DictWriter
# 电商场景：商品数据导出 JSON、订单数据导出 CSV、从 CSV 导入商品列表
# 运行方式：python json_csv.py

import csv
import json
from datetime import datetime
from pathlib import Path


# ====== 模拟电商数据 ======
PRODUCTS = [
    {'id': 1, 'name': '手机', 'price': 2999.0, 'stock': 100, 'category': '电子'},
    {'id': 2, 'name': '蓝牙耳机', 'price': 399.0, 'stock': 50, 'category': '电子'},
    {'id': 3, 'name': '机械键盘', 'price': 599.0, 'stock': 30, 'category': '电子'},
    {'id': 4, 'name': '纯棉T恤', 'price': 89.0, 'stock': 200, 'category': '服装'},
    {'id': 5, 'name': '运动鞋', 'price': 459.0, 'stock': 80, 'category': '服装'},
]

ORDERS = [
    {'id': 1001, 'customer': '张三', 'product_id': 1, 'qty': 2, 'total': 5998.0},
    {'id': 1002, 'customer': '李四', 'product_id': 2, 'qty': 3, 'total': 1197.0},
    {'id': 1003, 'customer': '张三', 'product_id': 4, 'qty': 5, 'total': 445.0},
]


def ensure_data_dir() -> Path:
    """确保 data 目录存在"""
    d = Path('data')
    d.mkdir(exist_ok=True)
    return d


# ====== JSON 读写 ======
def demo_json_string() -> None:
    """JSON 字符串与对象互转"""
    print('=== JSON 字符串互转 ===')
    product = PRODUCTS[0]

    # 序列化为字符串
    # ensure_ascii=False 保留中文，indent=2 美化
    text = json.dumps(product, ensure_ascii=False, indent=2)
    print(f'序列化:\n{text}')

    # 反序列化
    obj = json.loads(text)
    print(f'反序列化: {obj["name"]} 类型={type(obj).__name__}')

    # 对比 ensure_ascii 差异
    ascii_text = json.dumps(product)  # 默认 ensure_ascii=True
    print(f'默认 ASCII: {ascii_text[:60]}...')  # 中文变成 \uXXXX


def demo_json_file() -> None:
    """JSON 文件读写：商品导出"""
    print('=== JSON 文件读写（商品导出） ===')
    data_dir = ensure_data_dir()
    path = data_dir / 'products.json'

    # 写文件：dump(obj, f)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(PRODUCTS, f, ensure_ascii=False, indent=2)
    print(f'已导出 {len(PRODUCTS)} 件商品到 {path}')

    # 读文件：load(f)
    with open(path, encoding='utf-8') as f:
        loaded = json.load(f)
    print(f'读回 {len(loaded)} 件，第一件: {loaded[0]["name"]}')


def demo_json_custom_serializer() -> None:
    """自定义序列化：处理 datetime 等非标准类型"""
    print('=== 自定义序列化 ===')
    record = {
        'order_id': 1001,
        'created_at': datetime.now(),       # JSON 原生不支持
        'customer': '张三',
    }

    # 不加 default 会报 TypeError: Object of type datetime is not JSON serializable
    def default_encoder(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f'无法序列化 {type(obj).__name__}')

    text = json.dumps(record, ensure_ascii=False, default=default_encoder, indent=2)
    print(f'序列化（含 datetime）:\n{text}')

    # 反序列化后需要手动还原 datetime
    loaded = json.loads(text)
    restored_time = datetime.fromisoformat(loaded['created_at'])
    print(f'还原 datetime: {restored_time}')


# ====== CSV 读写 ======
def demo_csv_write() -> None:
    """CSV 写入：订单导出（DictWriter）"""
    print('=== CSV 写入（订单导出） ===')
    data_dir = ensure_data_dir()
    path = data_dir / 'orders.csv'

    # Windows 写 CSV 必须 newline=''，否则行间多空行
    fieldnames = ['id', 'customer', 'product_id', 'qty', 'total']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()                  # 写表头
        for order in ORDERS:
            writer.writerow(order)
    print(f'已导出 {len(ORDERS)} 笔订单到 {path}')

    # 用 csv.writer（列表模式）演示
    path2 = data_dir / 'orders_list.csv'
    with open(path2, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)           # 表头
        for o in ORDERS:
            writer.writerow([o['id'], o['customer'], o['product_id'], o['qty'], o['total']])
    print(f'列表模式写入: {path2}')


def demo_csv_read() -> None:
    """CSV 读取：DictReader 返回字典"""
    print('=== CSV 读取 ===')
    path = ensure_data_dir() / 'orders.csv'

    # DictReader：每行是 dict
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f'表头字段: {reader.fieldnames}')
        for row in reader:
            print(f'  订单{row["id"]} {row["customer"]} ¥{row["total"]}')

    # reader：每行是 list
    print('--- list 模式 ---')
    with open(path, encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue                      # 跳过表头
            print(f'  {row}')


def demo_csv_import_products() -> None:
    """电商场景：从 CSV 导入商品列表"""
    print('=== 从 CSV 导入商品 ===')
    data_dir = ensure_data_dir()
    csv_path = data_dir / 'import_products.csv'

    # 先写一个待导入的 CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'price', 'stock', 'category'])
        writer.writeheader()
        writer.writerow({'name': '鼠标', 'price': 99.0, 'stock': 150, 'category': '电子'})
        writer.writerow({'name': '显示器', 'price': 1599.0, 'stock': 20, 'category': '电子'})
        writer.writerow({'name': '牛仔裤', 'price': 259.0, 'stock': 60, 'category': '服装'})

    # 再读回导入
    imported = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # CSV 读出的值都是字符串，需要手动转换类型
            imported.append({
                'name': row['name'],
                'price': float(row['price']),
                'stock': int(row['stock']),
                'category': row['category'],
            })

    print(f'导入 {len(imported)} 件商品:')
    for p in imported:
        print(f'  {p["name"]} ¥{p["price"]} 库存{p["stock"]} ({p["category"]})')


def demo_csv_custom_delimiter() -> None:
    """自定义分隔符：TSV 用 \\t"""
    print('=== 自定义分隔符（TSV） ===')
    data_dir = ensure_data_dir()
    path = data_dir / 'orders.tsv'

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'customer'], delimiter='\t')
        writer.writeheader()
        writer.writerow({'id': 1, 'customer': '张三'})
        writer.writerow({'id': 2, 'customer': '李四'})

    print(path.read_text(encoding='utf-8'))


def main() -> None:
    demos = [
        demo_json_string,
        demo_json_file,
        demo_json_custom_serializer,
        demo_csv_write,
        demo_csv_read,
        demo_csv_import_products,
        demo_csv_custom_delimiter,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
