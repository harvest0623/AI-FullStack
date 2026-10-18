# Day13 代码文件说明

本目录包含 Day13 并发编程的 4 个 Python 演示脚本，所有代码围绕电商场景 `eshop` 展开。

## 文件清单

| 文件 | 内容 | 主要 API |
|------|------|---------|
| `threading_demo.py` | 多线程编程 | Thread / Lock / RLock / Semaphore / Event / Queue |
| `multiprocessing_demo.py` | 多进程编程 | Process / Pool / Queue / Value / ProcessPoolExecutor |
| `asyncio_demo.py` | asyncio 异步编程 | async/await / create_task / gather / Semaphore / async with |
| `concurrent_futures_demo.py` | concurrent.futures 统一接口 | ThreadPoolExecutor / ProcessPoolExecutor / Future |

## 运行方式

```bash
# 运行单个示例
python threading_demo.py
python multiprocessing_demo.py
python asyncio_demo.py
python concurrent_futures_demo.py
```

## 各文件演示内容

### threading_demo.py

- 示例 1：多线程批量抓取商品价格（Thread + Lock）
- 示例 2：线程安全的购物车操作（RLock 可重入锁）
- 示例 3：Queue 生产者-消费者模型处理订单
- 示例 4：Semaphore 限制并发抓取数
- 示例 5：Event 事件通知（秒杀活动开始）

### multiprocessing_demo.py

- 示例 1：多进程并行处理大数据集（Process + Queue）
- 示例 2：Pool 进程池批量并行计算
- 示例 3：Value 共享内存（多进程计数器）
- 示例 4：CPU 密集型任务线程 vs 进程性能对比
- 示例 5：ProcessPoolExecutor 统一接口

### asyncio_demo.py

- 示例 1：async/await 基础语法
- 示例 2：asyncio.gather 并发获取商品
- 示例 3：asyncio.sleep vs time.sleep 对比
- 示例 4：Semaphore 并发限流批量请求
- 示例 5：异步下载多个资源 + 容错处理
- 示例 6：asyncio.wait 与超时控制
- 示例 7：async with 异步上下文管理

### concurrent_futures_demo.py

- 示例 1：ThreadPoolExecutor submit + as_completed 处理订单
- 示例 2：ThreadPoolExecutor map 批量处理
- 示例 3：Future add_done_callback 回调
- 示例 4：ProcessPoolExecutor 进程池并行计算
- 示例 5：线程池 vs 进程池性能对比
- 示例 6：统一接口切换演示

## 环境要求

- Python 3.10+
- 仅使用标准库，无需额外安装依赖

## 注意事项

1. **multiprocessing 在 Windows 下**：必须将启动代码放在 `if __name__ == "__main__":` 保护块中
2. **asyncio 在 Windows 下**：Python 3.8+ 默认使用 ProactorEventLoop，无需特殊处理
3. **性能对比结果**：实际加速比取决于 CPU 核心数和任务特性
