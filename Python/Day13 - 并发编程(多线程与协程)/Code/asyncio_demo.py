# 文件用途：asyncio 异步编程演示
# 演示内容：async/await、create_task/gather、asyncio.sleep 对比 time.sleep、并发 vs 串行
# 电商场景：异步批量请求商品 API、并发下载多个资源
# Python 3.10+ 可运行

import asyncio
import time
import random


# ============================================================
# 示例 1：async/await 基础
# ============================================================

async def fetch_product(product_id: int) -> dict:
    """模拟异步获取商品信息"""
    await asyncio.sleep(random.uniform(0.1, 0.3))  # 非阻塞等待
    return {
        "id": product_id,
        "name": f"商品-{product_id}",
        "price": round(random.uniform(10.0, 999.9), 2),
        "stock": random.randint(0, 100),
    }


async def demo_async_basic() -> None:
    """演示 async/await 基本语法"""
    print("=" * 60)
    print("示例 1：async/await 基础")
    print("=" * 60)

    print("开始获取商品 1...")
    product = await fetch_product(1)
    print(f"获取到：{product}")

    print("\n获取多个商品（串行）...")
    start = time.perf_counter()
    products = []
    for i in range(1, 6):
        p = await fetch_product(i)
        products.append(p)
    elapsed = time.perf_counter() - start
    print(f"串行获取 5 个商品耗时 {elapsed:.2f}s")


# ============================================================
# 示例 2：create_task + gather 并发
# ============================================================

async def demo_concurrent_fetch() -> None:
    """演示 asyncio.gather 并发获取多个商品"""
    print("\n" + "=" * 60)
    print("示例 2：asyncio.gather 并发获取商品")
    print("=" * 60)

    # 串行对比
    print("串行方式...")
    start = time.perf_counter()
    serial = []
    for i in range(1, 11):
        serial.append(await fetch_product(i))
    serial_time = time.perf_counter() - start
    print(f"  串行 10 个商品：{serial_time:.2f}s")

    # 并发对比
    print("并发方式...")
    start = time.perf_counter()
    tasks = [fetch_product(i) for i in range(1, 11)]
    concurrent = await asyncio.gather(*tasks)
    concurrent_time = time.perf_counter() - start
    print(f"  并发 10 个商品：{concurrent_time:.2f}s")

    print(f"\n加速比：{serial_time / concurrent_time:.2f}x")


# ============================================================
# 示例 3：asyncio.sleep vs time.sleep
# ============================================================

async def demo_sleep_compare() -> None:
    """对比 asyncio.sleep 与 time.sleep"""
    print("\n" + "=" * 60)
    print("示例 3：asyncio.sleep vs time.sleep")
    print("=" * 60)

    # 正确用法：asyncio.sleep
    async def good_task(name: str) -> None:
        await asyncio.sleep(0.5)
        print(f"  [{name}] 完成（asyncio.sleep）")

    start = time.perf_counter()
    await asyncio.gather(good_task("A"), good_task("B"), good_task("C"))
    good_time = time.perf_counter() - start
    print(f"asyncio.sleep 并发 3 任务：{good_time:.2f}s（应约 0.5s）")

    # 错误用法：time.sleep 会阻塞事件循环
    async def bad_task(name: str) -> None:
        time.sleep(0.5)  # ❌ 阻塞整个事件循环
        print(f"  [{name}] 完成（time.sleep 阻塞）")

    start = time.perf_counter()
    await asyncio.gather(bad_task("A"), bad_task("B"), bad_task("C"))
    bad_time = time.perf_counter() - start
    print(f"time.sleep 阻塞 3 任务：{bad_time:.2f}s（应约 1.5s）")

    print("\n结论：在协程中必须使用 asyncio.sleep 而非 time.sleep")


# ============================================================
# 示例 4：Semaphore 并发限流 - 批量请求商品 API
# ============================================================

async def fetch_with_limit(product_id: int, sem: asyncio.Semaphore) -> dict:
    """使用 Semaphore 限制并发数"""
    async with sem:  # 获取信号量
        await asyncio.sleep(random.uniform(0.05, 0.2))
        return {"id": product_id, "price": round(random.uniform(10, 999), 2)}


async def demo_semaphore_limit() -> None:
    """演示 Semaphore 限制并发"""
    print("\n" + "=" * 60)
    print("示例 4：Semaphore 限制并发（最多 5 个同时）")
    print("=" * 60)

    sem = asyncio.Semaphore(5)
    product_ids = list(range(1, 21))  # 20 个商品

    start = time.perf_counter()
    tasks = [fetch_with_limit(pid, sem) for pid in product_ids]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    print(f"\n并发请求 {len(results)} 个商品，限流 5")
    print(f"耗时 {elapsed:.2f}s")
    print(f"前 3 个结果：{results[:3]}")


# ============================================================
# 示例 5：异步下载多个资源 + 容错处理
# ============================================================

async def download_resource(url: str, idx: int) -> str | None:
    """模拟异步下载资源，可能失败"""
    await asyncio.sleep(random.uniform(0.1, 0.5))
    if random.random() < 0.2:  # 20% 概率失败
        raise RuntimeError(f"下载 {idx} 失败")
    return f"resource-{idx}.bin ({len(url)} bytes)"


async def demo_download_with_error_handling() -> None:
    """演示并发下载并处理错误"""
    print("\n" + "=" * 60)
    print("示例 5：异步下载多个资源 + 容错处理")
    print("=" * 60)

    urls = [f"https://api.eshop.com/resource/{i}" for i in range(1, 11)]

    async def safe_download(url: str, idx: int) -> str | None:
        try:
            return await download_resource(url, idx)
        except RuntimeError as e:
            print(f"  ❌ {e}")
            return None

    start = time.perf_counter()
    tasks = [safe_download(url, i) for i, url in enumerate(urls, 1)]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    success = [r for r in results if r]
    failed = len(results) - len(success)
    print(f"\n下载完成：成功 {len(success)} / 失败 {failed}")
    print(f"耗时 {elapsed:.2f}s")


# ============================================================
# 示例 6：asyncio.wait 与超时控制
# ============================================================

async def demo_wait_with_timeout() -> None:
    """演示 asyncio.wait 与超时控制"""
    print("\n" + "=" * 60)
    print("示例 6：asyncio.wait 与超时控制")
    print("=" * 60)

    async def slow_task(name: str, delay: float) -> str:
        await asyncio.sleep(delay)
        return f"{name} 完成（{delay}s）"

    # 创建任务
    tasks = [
        asyncio.create_task(slow_task("快", 0.3), name="快任务"),
        asyncio.create_task(slow_task("中", 0.6), name="中任务"),
        asyncio.create_task(slow_task("慢", 1.5), name="慢任务"),
    ]

    # 等待最先完成的 2 个
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print(f"\n最先完成：{[t.get_name() for t in done]}")

    # 取消未完成的
    for t in pending:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

    # 超时控制
    print("\n超时控制演示：")
    try:
        result = await asyncio.wait_for(slow_task("超时测试", 2.0), timeout=0.5)
        print(f"  {result}")
    except asyncio.TimeoutError:
        print("  任务超时被取消（0.5s 超时限制）")


# ============================================================
# 示例 7：async with 异步上下文管理
# ============================================================

class AsyncDBConnection:
    """模拟异步数据库连接"""

    async def __aenter__(self):
        print("  打开数据库连接...")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("  关闭数据库连接...")
        await asyncio.sleep(0.05)

    async def query(self, sql: str) -> list:
        await asyncio.sleep(0.1)
        return [{"id": 1, "name": "商品A"}, {"id": 2, "name": "商品B"}]


async def demo_async_with() -> None:
    """演示 async with 异步上下文管理"""
    print("\n" + "=" * 60)
    print("示例 7：async with 异步上下文管理")
    print("=" * 60)

    async with AsyncDBConnection() as db:
        results = await db.query("SELECT * FROM products")
        print(f"  查询结果：{results}")


async def amain() -> None:
    """异步主函数"""
    await demo_async_basic()
    await demo_concurrent_fetch()
    await demo_sleep_compare()
    await demo_semaphore_limit()
    await demo_download_with_error_handling()
    await demo_wait_with_timeout()
    await demo_async_with()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("=" * 60)


def main() -> None:
    """入口：用 asyncio.run 启动事件循环"""
    asyncio.run(amain())


if __name__ == "__main__":
    main()
