# 文件用途：多进程编程演示
# 演示内容：Process 创建、Pool 进程池、Queue 进程间通信
# 电商场景：多进程并行处理大数据集、CPU 密集型任务对比线程和进程的性能差异
# Python 3.10+ 可运行

import os
import time
import threading
import multiprocessing
from multiprocessing import Process, Pool, Queue, Value, Array
from concurrent.futures import ProcessPoolExecutor


# ============================================================
# 示例 1：Process 基础 - 多进程并行处理大数据集
# ============================================================

def process_chunk(chunk: list[int], process_id: int, result_queue: Queue) -> None:
    """处理一个数据分块（CPU 密集型任务）"""
    print(f"  [进程 {process_id}] PID={os.getpid()} 处理 {len(chunk)} 条数据")
    # 模拟 CPU 密集型计算：求平方和
    total = sum(x * x for x in chunk)
    result_queue.put((process_id, total))


def demo_process_basic() -> None:
    """演示 Process 创建与 Queue 进程间通信"""
    print("=" * 60)
    print("示例 1：多进程并行处理大数据集")
    print("=" * 60)

    # 生成 100 万个数据，分成 4 份
    data = list(range(1, 1_000_001))
    chunk_size = len(data) // 4
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    result_queue: Queue = Queue()
    processes = []

    start = time.perf_counter()
    for i, chunk in enumerate(chunks):
        p = Process(
            target=process_chunk,
            args=(chunk, i, result_queue),
            name=f"Worker-{i}"
        )
        processes.append(p)
        p.start()

    # 等待所有进程完成
    for p in processes:
        p.join()

    # 收集结果
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    elapsed = time.perf_counter() - start
    print(f"\n处理完成：{len(data)} 条数据，分 {len(chunks)} 进程")
    print(f"各进程结果：{results}")
    print(f"总和：{sum(r for _, r in results)}")
    print(f"耗时 {elapsed:.2f}s")


# ============================================================
# 示例 2：Pool 进程池 - 批量并行任务
# ============================================================

def cpu_intensive_task(n: int) -> int:
    """CPU 密集型任务：计算 n 以内所有质数之和"""
    def is_prime(x: int) -> bool:
        if x < 2:
            return False
        for i in range(2, int(x ** 0.5) + 1):
            if x % i == 0:
                return False
        return True

    return sum(x for x in range(2, n) if is_prime(x))


def demo_process_pool() -> None:
    """演示 Pool 进程池的 map 用法"""
    print("\n" + "=" * 60)
    print("示例 2：Pool 进程池批量并行计算质数之和")
    print("=" * 60)

    tasks = [50000, 50000, 50000, 50000]

    start = time.perf_counter()
    with Pool(processes=4) as pool:
        results = pool.map(cpu_intensive_task, tasks)
    elapsed = time.perf_counter() - start

    print(f"\n各任务结果：{results}")
    print(f"耗时 {elapsed:.2f}s（4 进程并行）")


# ============================================================
# 示例 3：共享内存 - Value 与 Array
# ============================================================

def increment_counter(counter: Value, lock: multiprocessing.Lock, times: int) -> None:
    """使用 Value 共享计数器"""
    for _ in range(times):
        with lock:
            counter.value += 1


def demo_shared_memory() -> None:
    """演示 Value 共享内存"""
    print("\n" + "=" * 60)
    print("示例 3：Value 共享内存（多进程计数器）")
    print("=" * 60)

    counter = Value("i", 0)  # 'i' 表示整型
    lock = multiprocessing.Lock()

    processes = [
        Process(target=increment_counter, args=(counter, lock, 10000))
        for _ in range(4)
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    print(f"\n期望结果：{4 * 10000}")
    print(f"实际结果：{counter.value}")


# ============================================================
# 示例 4：CPU 密集型任务 - 线程 vs 进程性能对比
# ============================================================

def demo_thread_vs_process() -> None:
    """对比多线程与多进程在 CPU 密集型任务上的性能差异"""
    print("\n" + "=" * 60)
    print("示例 4：CPU 密集型任务 - 多线程 vs 多进程")
    print("=" * 60)

    n = 80_000  # 每个任务计算 8 万以内质数之和
    num_workers = 4

    # 1. 单线程基准
    start = time.perf_counter()
    single_results = [cpu_intensive_task(n) for _ in range(num_workers)]
    single_time = time.perf_counter() - start
    print(f"\n单线程串行：{single_time:.2f}s（结果 {single_results[0]}）")

    # 2. 多线程
    start = time.perf_counter()
    threads = [threading.Thread(target=cpu_intensive_task, args=(n,)) for _ in range(num_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    thread_time = time.perf_counter() - start
    print(f"多线程（{num_workers}）：{thread_time:.2f}s")

    # 3. 多进程
    start = time.perf_counter()
    with Pool(processes=num_workers) as pool:
        pool.map(cpu_intensive_task, [n] * num_workers)
    process_time = time.perf_counter() - start
    print(f"多进程（{num_workers}）：{process_time:.2f}s")

    # 对比结论
    print("\n--- 性能对比结论 ---")
    print(f"多线程 vs 单线程：{thread_time / single_time:.2f}x（受 GIL 限制，几乎无加速）")
    print(f"多进程 vs 单线程：{single_time / process_time:.2f}x（真正并行加速）")


# ============================================================
# 示例 5：ProcessPoolExecutor - 统一接口
# ============================================================

def demo_process_pool_executor() -> None:
    """演示 ProcessPoolExecutor 统一接口"""
    print("\n" + "=" * 60)
    print("示例 5：ProcessPoolExecutor 统一接口")
    print("=" * 60)

    tasks = [30000, 40000, 50000, 60000]

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        # map 方式：按顺序返回结果
        results = list(executor.map(cpu_intensive_task, tasks))
    elapsed = time.perf_counter() - start

    print(f"\n任务输入：{tasks}")
    print(f"计算结果：{results}")
    print(f"耗时 {elapsed:.2f}s")


def main() -> None:
    """主函数"""
    # Windows 下 multiprocessing 必须有此保护
    demo_process_basic()
    demo_process_pool()
    demo_shared_memory()
    demo_thread_vs_process()
    demo_process_pool_executor()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
