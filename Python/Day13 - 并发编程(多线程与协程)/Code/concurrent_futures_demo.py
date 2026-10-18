# 文件用途：concurrent.futures 统一接口演示
# 演示内容：ThreadPoolExecutor/ProcessPoolExecutor、submit/map/as_completed、Future 回调
# 电商场景：线程池批量处理订单、进程池并行计算
# Python 3.10+ 可运行

import time
import random
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    as_completed,
    Future,
)


# ============================================================
# 示例 1：ThreadPoolExecutor - 线程池批量处理订单
# ============================================================

def process_order(order_id: int) -> dict:
    """模拟处理一个订单（IO 密集型）"""
    time.sleep(random.uniform(0.05, 0.2))  # 模拟数据库写入
    return {
        "order_id": order_id,
        "status": "completed",
        "amount": round(random.uniform(10.0, 999.9), 2),
    }


def demo_thread_pool_submit() -> None:
    """演示 ThreadPoolExecutor 的 submit + as_completed"""
    print("=" * 60)
    print("示例 1：ThreadPoolExecutor 批量处理订单（submit + as_completed）")
    print("=" * 60)

    order_ids = list(range(1, 11))

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        # submit 返回 Future
        futures = {
            executor.submit(process_order, oid): oid
            for oid in order_ids
        }

        # as_completed 按完成顺序获取结果
        for future in as_completed(futures):
            oid = futures[future]
            try:
                result = future.result()
                print(f"  订单 {oid} 处理完成：{result['status']} 金额 {result['amount']}")
            except Exception as e:
                print(f"  订单 {oid} 处理失败：{e}")

    elapsed = time.perf_counter() - start
    print(f"\n共处理 {len(order_ids)} 个订单，耗时 {elapsed:.2f}s")


# ============================================================
# 示例 2：map 方法 - 批量提交保持顺序
# ============================================================

def demo_thread_pool_map() -> None:
    """演示 ThreadPoolExecutor 的 map 方法"""
    print("\n" + "=" * 60)
    print("示例 2：ThreadPoolExecutor map 批量处理（保持顺序）")
    print("=" * 60)

    order_ids = list(range(1, 11))

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        # map 会按输入顺序返回结果
        results = executor.map(process_order, order_ids)

        for oid, result in zip(order_ids, results):
            print(f"  订单 {oid}：{result}")

    elapsed = time.perf_counter() - start
    print(f"\n共处理 {len(order_ids)} 个订单，耗时 {elapsed:.2f}s")
    print("注意：map 保证返回顺序与输入顺序一致")


# ============================================================
# 示例 3：Future 回调 - add_done_callback
# ============================================================

def order_callback(future: Future) -> None:
    """订单完成回调"""
    try:
        result = future.result()
        print(f"  [回调] 订单 {result['order_id']} 已通知客户，金额 {result['amount']}")
    except Exception as e:
        print(f"  [回调] 订单处理失败：{e}")


def demo_future_callback() -> None:
    """演示 Future 的 add_done_callback"""
    print("\n" + "=" * 60)
    print("示例 3：Future 回调 add_done_callback")
    print("=" * 60)

    order_ids = list(range(1, 6))

    with ThreadPoolExecutor(max_workers=3) as executor:
        for oid in order_ids:
            future = executor.submit(process_order, oid)
            future.add_done_callback(order_callback)
            print(f"  提交订单 {oid} 处理中...")

    print("  所有订单处理完毕")


# ============================================================
# 示例 4：ProcessPoolExecutor - 进程池并行计算
# ============================================================

def compute_stats(data_chunk: list[float]) -> dict:
    """CPU 密集型：计算统计指标"""
    time.sleep(0.1)  # 模拟额外计算开销
    return {
        "count": len(data_chunk),
        "sum": sum(data_chunk),
        "avg": sum(data_chunk) / len(data_chunk) if data_chunk else 0,
        "max": max(data_chunk),
        "min": min(data_chunk),
    }


def demo_process_pool_executor() -> None:
    """演示 ProcessPoolExecutor 并行计算"""
    print("\n" + "=" * 60)
    print("示例 4：ProcessPoolExecutor 进程池并行计算")
    print("=" * 60)

    # 生成 4 份数据
    chunks = [
        [random.uniform(0, 100) for _ in range(1000)]
        for _ in range(4)
    ]

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(compute_stats, chunk) for chunk in chunks]

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            print(f"  分块 {i}: count={result['count']} avg={result['avg']:.2f}")

    elapsed = time.perf_counter() - start
    print(f"\n并行计算 4 份数据，耗时 {elapsed:.2f}s")


# ============================================================
# 示例 5：线程池 vs 进程池 - 选型对比
# ============================================================

def io_task(n: int) -> int:
    """IO 密集型任务"""
    time.sleep(0.2)
    return n * 2


def cpu_task(n: int) -> int:
    """CPU 密集型任务"""
    return sum(i * i for i in range(n))


def demo_pool_comparison() -> None:
    """对比线程池与进程池在 IO/CPU 任务上的表现"""
    print("\n" + "=" * 60)
    print("示例 5：ThreadPoolExecutor vs ProcessPoolExecutor 对比")
    print("=" * 60)

    # IO 密集型任务
    print("\n--- IO 密集型任务（每个 sleep 0.2s）---")
    tasks = list(range(10))

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(io_task, tasks))
    thread_io_time = time.perf_counter() - start
    print(f"  线程池：{thread_io_time:.2f}s")

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=5) as ex:
        list(ex.map(io_task, tasks))
    process_io_time = time.perf_counter() - start
    print(f"  进程池：{process_io_time:.2f}s")
    print("  结论：IO 密集型线程池更优（进程启动开销大）")

    # CPU 密集型任务
    print("\n--- CPU 密集型任务（计算 50000 以内平方和）---")
    cpu_tasks = [50000] * 4

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(cpu_task, cpu_tasks))
    thread_cpu_time = time.perf_counter() - start
    print(f"  线程池：{thread_cpu_time:.2f}s（受 GIL 限制）")

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as ex:
        list(ex.map(cpu_task, cpu_tasks))
    process_cpu_time = time.perf_counter() - start
    print(f"  进程池：{process_cpu_time:.2f}s（真正并行）")
    print(f"  结论：CPU 密集型进程池更优（线程池受 GIL 限制无法加速）")


# ============================================================
# 示例 6：统一接口切换 - 线程池与进程池无缝切换
# ============================================================

def demo_unified_interface() -> None:
    """演示 ThreadPoolExecutor 与 ProcessPoolExecutor 接口一致"""
    print("\n" + "=" * 60)
    print("示例 6：统一接口 - 线程池与进程池代码几乎一致")
    print("=" * 60)

    def run_with_executor(executor_class, task_name: str):
        with executor_class(max_workers=4) as executor:
            # 三种用法完全相同
            # 1. submit
            f = executor.submit(io_task, 1)
            print(f"  [{task_name}] submit 结果：{f.result()}")

            # 2. map
            results = list(executor.map(io_task, [1, 2, 3]))
            print(f"  [{task_name}] map 结果：{results}")

    print("使用 ThreadPoolExecutor:")
    run_with_executor(ThreadPoolExecutor, "线程池")

    print("\n使用 ProcessPoolExecutor:")
    run_with_executor(ProcessPoolExecutor, "进程池")

    print("\n结论：两类执行器 API 完全一致，只需改一行即可切换")


def main() -> None:
    """主函数"""
    demo_thread_pool_submit()
    demo_thread_pool_map()
    demo_future_callback()
    demo_process_pool_executor()
    demo_pool_comparison()
    demo_unified_interface()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
