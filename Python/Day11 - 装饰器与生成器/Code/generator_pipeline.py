# 文件用途：生成器管道练习
# 演示读取大CSV→过滤→转换→输出的流水线、惰性求值内存对比
# 电商场景：流式处理百万级订单数据
# 运行方式：python generator_pipeline.py

import csv
import sys
import time
from pathlib import Path


# ====== 生成器管道组件 ======
def read_csv_rows(path: Path):
    """管道第1级：逐行读取 CSV（生成器）

    每次只读一行，不一次性载入整个文件。
    """
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def filter_amount(rows, min_amount: float):
    """管道第2级：过滤金额低于阈值的订单"""
    for row in rows:
        if float(row['amount']) >= min_amount:
            yield row


def filter_status(rows, *statuses):
    """管道第2级（可选）：按状态过滤"""
    status_set = set(statuses)
    for row in rows:
        if row['status'] in status_set:
            yield row


def transform_rows(rows):
    """管道第3级：转换格式（生成器）"""
    for row in rows:
        yield {
            'order_id': row['order_id'],
            'customer': row['customer'],
            'amount': float(row['amount']),
            'amount_str': f"¥{float(row['amount']):,.2f}",
        }


def aggregate_by_customer(rows):
    """管道第4级：按客户聚合（生成器）

    注意：聚合需要遍历全部数据，但仍然逐条消费上游。
    """
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for row in rows:
        customer = row['customer']
        totals[customer] = totals.get(customer, 0) + row['amount']
        counts[customer] = counts.get(customer, 0) + 1
    # 聚合完再产出
    for customer in sorted(totals, key=lambda c: totals[c], reverse=True):
        yield {
            'customer': customer,
            'order_count': counts[customer],
            'total_amount': round(totals[customer], 2),
        }


# ====== 工具函数 ======
def generate_large_csv(path: Path, n: int = 100_000) -> None:
    """生成大 CSV 文件用于演示"""
    import random
    random.seed(42)
    customers = ['张三', '李四', '王五', '赵六', '钱七']
    statuses = ['paid', 'pending', 'shipped', 'refunded']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['order_id', 'customer', 'amount', 'status'])
        writer.writeheader()
        for i in range(1, n + 1):
            writer.writerow({
                'order_id': 10000 + i,
                'customer': random.choice(customers),
                'amount': round(random.uniform(10, 5000), 2),
                'status': random.choice(statuses),
            })


# ====== 演示函数 ======
def demo_pipeline_basic() -> None:
    """基本管道：读取 → 过滤 → 转换 → 输出"""
    print('=== 生成器管道基础 ===')
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    csv_path = data_dir / 'orders_pipeline.csv'

    # 生成 1000 行测试数据
    generate_large_csv(csv_path, n=1000)

    # 构建管道：每一步都是生成器，惰性求值
    pipeline = transform_rows(
        filter_amount(
            filter_status(read_csv_rows(csv_path), 'paid', 'shipped'),
            min_amount=100,
        )
    )

    # 消费管道：逐条取出
    print(f'过滤金额>=100 且状态为 paid/shipped 的订单:')
    count = 0
    for item in pipeline:
        if count < 5:
            print(f'  {item["order_id"]} {item["customer"]} {item["amount_str"]}')
        count += 1
    print(f'  ... 共 {count} 条满足条件')


def demo_pipeline_aggregate() -> None:
    """管道聚合：按客户统计"""
    print('=== 管道聚合（按客户统计） ===')
    data_dir = Path('data')
    csv_path = data_dir / 'orders_pipeline.csv'

    # 管道：读取 → 过滤金额 → 转换 → 按客户聚合
    pipeline = aggregate_by_customer(
        transform_rows(
            filter_amount(read_csv_rows(csv_path), min_amount=500)
        )
    )

    print('金额 >= 500 的客户消费排名:')
    for i, stat in enumerate(pipeline, start=1):
        print(f'  第{i}名 {stat["customer"]}: '
              f'{stat["order_count"]} 单，合计 ¥{stat["total_amount"]:,.2f}')


def demo_memory_comparison() -> None:
    """内存对比：生成器管道 vs 一次性载入"""
    print('=== 内存对比 ===')
    data_dir = Path('data')
    csv_path = data_dir / 'orders_pipeline.csv'

    # 方式1：一次性读全部到列表（eager）
    start = time.perf_counter()
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)          # 全部载入内存
    total1 = sum(float(r['amount']) for r in all_rows)
    t1 = time.perf_counter() - start
    mem1 = sys.getsizeof(all_rows)
    print(f'  一次性载入: {len(all_rows)} 行，'
          f'列表对象 {mem1:,} bytes，耗时 {t1*1000:.1f} ms')
    print(f'  （注意：列表里每个 dict 还单独占内存，实际占用远大于此）')

    # 方式2：生成器逐行处理（lazy）
    start = time.perf_counter()
    gen = read_csv_rows(csv_path)
    mem2 = sys.getsizeof(gen)
    total2 = 0.0
    count = 0
    for row in gen:
        total2 += float(row['amount'])
        count += 1
    t2 = time.perf_counter() - start
    print(f'  生成器管道: {count} 行，'
          f'生成器对象 {mem2} bytes，耗时 {t2*1000:.1f} ms')

    print(f'  金额一致: {abs(total1 - total2) < 0.01}')
    print(f'  内存优势: 列表 {mem1:,} vs 生成器 {mem2} bytes')


def demo_large_scale() -> None:
    """电商场景：流式处理百万级订单"""
    print('=== 电商场景：流式处理 10 万订单 ===')
    data_dir = Path('data')
    csv_path = data_dir / 'orders_large.csv'

    # 生成 10 万行（演示用，真实场景可百万级）
    print('  生成 10 万行测试数据...')
    generate_large_csv(csv_path, n=100_000)
    file_size_mb = csv_path.stat().st_size / 1024 / 1024
    print(f'  文件大小: {file_size_mb:.1f} MB')

    # 流式处理：统计已支付订单的金额分布
    start = time.perf_counter()
    pipeline = transform_rows(
        filter_status(read_csv_rows(csv_path), 'paid')
    )

    amount_buckets = {'0-100': 0, '100-1000': 0, '1000-5000': 0}
    total_paid = 0.0
    paid_count = 0
    for item in pipeline:
        amt = item['amount']
        total_paid += amt
        paid_count += 1
        if amt < 100:
            amount_buckets['0-100'] += 1
        elif amt < 1000:
            amount_buckets['100-1000'] += 1
        else:
            amount_buckets['1000-5000'] += 1

    elapsed = time.perf_counter() - start
    print(f'  处理完成，耗时 {elapsed*1000:.1f} ms')
    print(f'  已支付订单: {paid_count} 笔，总金额 ¥{total_paid:,.2f}')
    print(f'  金额分布: {amount_buckets}')
    print(f'  （全程内存恒定，不随数据量增长）')


def demo_pipeline_composition() -> None:
    """管道自由组合演示"""
    print('=== 管道自由组合 ===')
    data_dir = Path('data')
    csv_path = data_dir / 'orders_pipeline.csv'

    # 同一数据源，构建不同管道
    source = read_csv_rows(csv_path)

    # 管道A：只看已退款订单
    print('  [管道A] 已退款订单:')
    pipe_a = filter_status(read_csv_rows(csv_path), 'refunded')
    count_a = sum(1 for _ in pipe_a)
    print(f'    共 {count_a} 笔退款')

    # 管道B：大额订单
    print('  [管道B] 大额订单(>3000):')
    pipe_b = filter_amount(read_csv_rows(csv_path), min_amount=3000)
    count_b = sum(1 for _ in pipe_b)
    print(f'    共 {count_b} 笔大额')

    # 管道C：组合过滤
    print('  [管道C] 已支付且金额>1000:')
    pipe_c = filter_amount(
        filter_status(read_csv_rows(csv_path), 'paid'),
        min_amount=1000,
    )
    count_c = sum(1 for _ in pipe_c)
    print(f'    共 {count_c} 笔')

    print('  → 同一数据源可复用，每个管道独立惰性求值')


def main() -> None:
    demos = [
        demo_pipeline_basic,
        demo_pipeline_aggregate,
        demo_memory_comparison,
        demo_large_scale,
        demo_pipeline_composition,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
