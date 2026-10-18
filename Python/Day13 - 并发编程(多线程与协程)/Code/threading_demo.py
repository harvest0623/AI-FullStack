# 文件用途：多线程编程演示
# 演示内容：Thread 创建/start/join、Lock 线程同步、Queue 生产者-消费者模型
# 电商场景：多线程批量抓取商品价格、线程安全的购物车操作、生产者消费者处理订单队列
# Python 3.10+ 可运行

import threading
import time
import random
from queue import Queue
from collections import defaultdict


# ============================================================
# 示例 1：Thread 基础 - 多线程批量抓取商品价格
# ============================================================

def fetch_product_price(product_id: int, results: dict, lock: threading.Lock) -> None:
    """模拟抓取商品价格的网络请求"""
    # 模拟网络延迟
    time.sleep(random.uniform(0.1, 0.3))
    price = round(random.uniform(10.0, 999.9), 2)

    # 使用 Lock 保护共享字典
    with lock:
        results[product_id] = price
    print(f"  [线程 {threading.current_thread().name}] 商品 {product_id} 价格 {price}")


def demo_thread_basic() -> None:
    """演示 Thread 的创建、start、join"""
    print("=" * 60)
    print("示例 1：多线程批量抓取商品价格")
    print("=" * 60)

    product_ids = list(range(1, 11))  # 10 个商品
    results: dict[int, float] = {}
    lock = threading.Lock()
    threads: list[threading.Thread] = []

    start = time.perf_counter()
    for pid in product_ids:
        t = threading.Thread(
            target=fetch_product_price,
            args=(pid, results, lock),
            name=f"Fetcher-{pid}"
        )
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start
    print(f"\n抓取完成：{len(results)} 个商品，耗时 {elapsed:.2f}s")
    print(f"平均价格：{sum(results.values()) / len(results):.2f}")
    print(f"活跃线程数：{threading.active_count()}")


# ============================================================
# 示例 2：线程安全的购物车操作 - Lock 与 RLock
# ============================================================

class SafeCart:
    """线程安全的购物车"""

    def __init__(self) -> None:
        self._items: dict[str, int] = {}
        self._lock = threading.RLock()  # 使用 RLock 支持嵌套调用

    def add_item(self, name: str, qty: int = 1) -> None:
        with self._lock:
            self._items[name] = self._items.get(name, 0) + qty

    def remove_item(self, name: str) -> None:
        with self._lock:
            if name in self._items:
                del self._items[name]

    def total_items(self) -> int:
        with self._lock:
            return sum(self._items.values())

    def checkout(self) -> dict[str, int]:
        """结账 - 演示 RLock 可重入特性"""
        with self._lock:
            # checkout 内部调用了 total_items
            # 如果用 Lock 会死锁，RLock 同线程可多次获取
            print(f"  结账时购物车共 {self.total_items()} 件商品")
            snapshot = dict(self._items)
            self._items.clear()
            return snapshot


def demo_thread_safe_cart() -> None:
    """演示线程安全的购物车操作"""
    print("\n" + "=" * 60)
    print("示例 2：线程安全的购物车操作（Lock / RLock）")
    print("=" * 60)

    cart = SafeCart()
    products = ["iPhone", "MacBook", "AirPods", "iPad", "Watch"]

    def shopper(name: str) -> None:
        for _ in range(random.randint(2, 5)):
            product = random.choice(products)
            qty = random.randint(1, 3)
            cart.add_item(product, qty)
            time.sleep(0.05)

    threads = [threading.Thread(target=shopper, args=(f"用户-{i}",)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n购物车最终状态：{cart.total_items()} 件商品")
    final_cart = cart.checkout()
    print(f"结账明细：{final_cart}")


# ============================================================
# 示例 3：Queue 生产者-消费者模型 - 处理订单队列
# ============================================================

def order_producer(queue: Queue, count: int) -> None:
    """生产者：生成订单并放入队列"""
    for i in range(count):
        order = {
            "order_id": f"ORD-{i + 1:04d}",
            "product": random.choice(["iPhone", "MacBook", "AirPods"]),
            "qty": random.randint(1, 5),
            "price": round(random.uniform(99.0, 9999.0), 2),
        }
        queue.put(order)
        print(f"  [生产者] 生成订单 {order['order_id']}")
        time.sleep(random.uniform(0.05, 0.15))

    # 放入结束标记（每个消费者一个）
    for _ in range(3):
        queue.put(None)


def order_consumer(queue: Queue, name: str, stats: dict, lock: threading.Lock) -> None:
    """消费者：从队列取订单并处理"""
    while True:
        order = queue.get()  # 阻塞直到有数据
        if order is None:  # 收到结束标记
            queue.task_done()
            break

        # 模拟订单处理
        time.sleep(random.uniform(0.1, 0.2))
        total = order["qty"] * order["price"]

        with lock:
            stats["total_orders"] += 1
            stats["total_amount"] += total

        print(f"  [{name}] 处理订单 {order['order_id']} 金额 {total:.2f}")
        queue.task_done()


def demo_producer_consumer() -> None:
    """演示生产者-消费者模型"""
    print("\n" + "=" * 60)
    print("示例 3：Queue 生产者-消费者模型处理订单")
    print("=" * 60)

    order_queue: Queue = Queue(maxsize=20)
    stats: dict = {"total_orders": 0, "total_amount": 0.0}
    lock = threading.Lock()

    # 1 个生产者 + 3 个消费者
    producer = threading.Thread(
        target=order_producer,
        args=(order_queue, 15),
        name="Producer"
    )
    consumers = [
        threading.Thread(
            target=order_consumer,
            args=(order_queue, f"Consumer-{i}", stats, lock),
            name=f"Consumer-{i}"
        )
        for i in range(1, 4)
    ]

    start = time.perf_counter()
    producer.start()
    for c in consumers:
        c.start()

    # 等待队列中所有任务完成
    order_queue.join()
    producer.join()
    for c in consumers:
        c.join()

    elapsed = time.perf_counter() - start
    print(f"\n订单处理完成：{stats['total_orders']} 单，总金额 {stats['total_amount']:.2f}")
    print(f"耗时 {elapsed:.2f}s")


# ============================================================
# 示例 4：Semaphore 限制并发 - 限制同时抓取数量
# ============================================================

def demo_semaphore() -> None:
    """演示 Semaphore 限制并发数"""
    print("\n" + "=" * 60)
    print("示例 4：Semaphore 限制并发抓取数（最多 3 个同时）")
    print("=" * 60)

    sem = threading.Semaphore(3)
    active = 0
    max_active = 0
    counter_lock = threading.Lock()

    def limited_fetch(idx: int) -> None:
        nonlocal active, max_active
        with sem:
            with counter_lock:
                active += 1
                max_active = max(max_active, active)
            print(f"  [任务 {idx}] 开始抓取，当前并发 {active}")
            time.sleep(0.3)
            with counter_lock:
                active -= 1

    threads = [threading.Thread(target=limited_fetch, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n最大并发数：{max_active}（限制为 3）")


# ============================================================
# 示例 5：Event 事件通知 - 促销开始
# ============================================================

def demo_event() -> None:
    """演示 Event 事件通知"""
    print("\n" + "=" * 60)
    print("示例 5：Event 事件通知（秒杀活动开始）")
    print("=" * 60)

    sale_event = threading.Event()

    def customer(name: str) -> None:
        print(f"  [{name}] 等待秒杀开始...")
        sale_event.wait()  # 阻塞直到 set()
        print(f"  [{name}] 抢购成功！")

    # 3 个顾客等待
    customers = [threading.Thread(target=customer, args=(f"顾客-{i}",)) for i in range(1, 4)]
    for t in customers:
        t.start()

    time.sleep(1)
    print("  [系统] 秒杀活动开始！")
    sale_event.set()  # 触发事件

    for t in customers:
        t.join()


def main() -> None:
    """主函数：依次运行所有演示"""
    demo_thread_basic()
    demo_thread_safe_cart()
    demo_producer_consumer()
    demo_semaphore()
    demo_event()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
