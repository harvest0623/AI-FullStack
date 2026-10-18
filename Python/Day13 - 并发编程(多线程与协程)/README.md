# Day13 - 并发编程（多线程与协程）

并发编程是提升程序性能的关键手段，Python 的 GIL（全局解释器锁）让并发模型选择尤为重要。面对一个需要同时抓取上千个商品价格的爬虫、一个要并行处理大数据集的分析任务、一个要同时处理上万 QPS 的 API 聚合服务，选择合适并发模型会直接决定程序是顺畅运行还是卡死崩溃。本章将系统讲解 Python 三大并发模型——多线程 threading、多进程 multiprocessing、协程 asyncio，以及统一的 concurrent.futures 接口，并结合电商场景给出选型决策。

## 学习目标

完成本章后，你应能：

- 准确区分并发（Concurrency）与并行（Parallelism），理解 IO 密集型与 CPU 密集型任务的差异
- 透彻理解 GIL 的原理、释放时机与对并发模型的影响
- 熟练使用 threading 进行多线程编程，掌握 Lock / RLock / Semaphore / Event / Condition / Queue 等同步原语
- 熟练使用 multiprocessing 进行多进程编程，掌握进程间通信与进程池
- 熟练使用 asyncio 异步编程，掌握 async/await / Task / gather / async with
- 使用 concurrent.futures 统一接口切换线程池与进程池
- 针对不同场景做出正确的并发模型选型

## 理论知识讲解

### 1. 并发 vs 并行

#### 1.1 概念对比

| 维度 | 并发 Concurrency | 并行 Parallelism |
|------|------------------|-----------------|
| 定义 | 多任务交替执行 | 多任务同时执行 |
| 硬件要求 | 单核即可 | 需多核 CPU |
| 核心思想 | 任务调度切换 | 真正同时执行 |
| 比喻 | 一个厨师同时做三道菜（切换） | 三个厨师同时做三道菜 |
| Python 实现 | threading / asyncio | multiprocessing |

**并发**强调"同时处理"多个任务，但任务之间可能只是快速切换；**并行**强调"同时执行"多个任务，需要硬件支持。

#### 1.2 IO 密集型 vs CPU 密集型

| 任务类型 | 特征 | 典型场景 | 推荐模型 |
|---------|------|---------|---------|
| IO 密集型 | 大量时间花在网络/磁盘等待 | 爬虫、API 请求、数据库查询 | 多线程 / asyncio |
| CPU 密集型 | 大量时间花在 CPU 计算 | 图像处理、数值计算、压缩 | 多进程 |

```python
# IO 密集型示例：等待网络响应
import time
def fetch_url(url):
    time.sleep(2)  # 模拟网络等待
    return f"来自 {url} 的数据"

# CPU 密集型示例：大量计算
def cpu_task(n):
    return sum(i * i for i in range(n))
```

### 2. GIL（全局解释器锁）

#### 2.1 什么是 GIL

GIL（Global Interpreter Lock）是 CPython 解释器实现中的一把**互斥锁**，它保证**同一时刻只有一个线程在执行 Python 字节码**。这意味着即使在多核 CPU 上，多线程的 Python 程序也无法真正并行执行 Python 代码。

```
多核 CPU 上 Python 多线程的真实情况：

核心1   ┌───┐   ┌───┐   ┌───┐
        │T1 │   │T1 │   │T1 │  ← GIL 在线程间切换
核心2   └───┘   └───┘   └───┘
        ┌───┐   ┌───┐   ┌───┐
        │T2 │   │T2 │   │T2 │
        └───┘   └───┘   └───┘
        时间 →

实际上任一时刻只有一个线程在执行字节码
```

#### 2.2 为什么有 GIL

GIL 存在的两大原因：

1. **简化引用计数的线程安全**：CPython 用引用计数管理内存，多线程同时修改引用计数需要加锁，GIL 用一把全局锁简化了这个问题
2. **历史原因**：Python 诞生于 1991 年，单核时代，GIL 简化了 C 扩展的编写

#### 2.3 GIL 的影响

| 任务类型 | GIL 影响 | 原因 |
|---------|---------|------|
| CPU 密集型（多线程） | ❌ 无法利用多核 | 同一时刻只有一个线程执行字节码 |
| IO 密集型（多线程） | ✅ 不受影响 | IO 操作会释放 GIL，其他线程可执行 |
| CPU 密集型（多进程） | ✅ 不受影响 | 每个进程有独立的 GIL |

#### 2.4 GIL 的释放时机

- **IO 操作**：文件读写、网络请求、`time.sleep()` 等会主动释放 GIL
- **定时检查**：默认每 5ms 检查一次是否切换线程，可用 `sys.setswitchinterval()` 调整
- **C 扩展**：C 扩展可以主动释放 GIL（如 NumPy 的底层计算）

```python
import sys
# 查看当前切换间隔（秒）
print(sys.getswitchinterval())  # 默认 0.005（5ms）
# 设置切换间隔
sys.setswitchinterval(0.001)
```

#### 2.5 绕过 GIL 的方法

| 方法 | 适用场景 | 代价 |
|------|---------|------|
| multiprocessing | CPU 密集型 | 进程开销大、内存独立需 IPC |
| C 扩展（如 NumPy） | 数值计算 | 需要编写 C 代码或使用现成库 |
| Jython / PyPy | 替代解释器 | 生态不如 CPython 完整 |
| Python 3.13+ 实验性无 GIL | 未来方案 | 兼容性需验证 |

### 3. 多线程 threading

#### 3.1 Thread 类基础

```python
import threading
import time

def worker(name, count):
    for i in range(count):
        print(f"[{name}] 第 {i} 次")
        time.sleep(0.1)

# 方式一：传入 target 和 args
t = threading.Thread(target=worker, args=("A", 3))
t.start()   # 启动线程
t.join()    # 等待线程结束
print(t.is_alive())  # False
```

#### 3.2 继承 Thread 重写 run()

```python
class MyThread(threading.Thread):
    def __init__(self, name, count):
        super().__init__()
        self.name = name
        self.count = count

    def run(self):  # 重写 run 方法
        for i in range(self.count):
            print(f"[{self.name}] 第 {i} 次")

t = MyThread("B", 3)
t.start()
t.join()
```

#### 3.3 常用线程 API

| API | 用途 |
|-----|------|
| `threading.active_count()` | 当前活跃线程数 |
| `threading.current_thread()` | 当前线程对象 |
| `threading.enumerate()` | 所有活跃线程列表 |
| `t.start()` | 启动线程 |
| `t.join(timeout)` | 等待线程结束 |
| `t.is_alive()` | 线程是否存活 |
| `t.daemon = True` | 守护线程（主线程退出即结束） |

#### 3.4 线程同步原语

##### 3.4.1 Lock（互斥锁）

```python
import threading

lock = threading.Lock()
shared_counter = 0

def increment():
    global shared_counter
    for _ in range(100000):
        # 方式一：手动 acquire/release
        # lock.acquire()
        # shared_counter += 1
        # lock.release()

        # 方式二：with 上下文（推荐）
        with lock:
            shared_counter += 1

threads = [threading.Thread(target=increment) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()
print(shared_counter)  # 500000（无锁则远小于此值）
```

##### 3.4.2 RLock（可重入锁）

同一线程可以多次 acquire，避免自己锁死自己（常用于递归调用）。

```python
lock = threading.RLock()

def recursive_func(n):
    with lock:
        if n > 0:
            print(f"递归层 {n}")
            recursive_func(n - 1)  # 再次获取同一把锁
```

##### 3.4.3 Semaphore（信号量）

限制同时访问某资源的线程数量。

```python
sem = threading.Semaphore(3)  # 最多 3 个线程同时访问

def fetch_with_limit(url):
    with sem:
        print(f"开始抓取 {url}")
        time.sleep(1)
```

##### 3.4.4 Event（事件通知）

```python
event = threading.Event()

def waiter():
    print("等待事件...")
    event.wait()       # 阻塞直到 set()
    print("事件已触发")

def setter():
    time.sleep(2)
    event.set()        # 触发事件

threading.Thread(target=waiter).start()
threading.Thread(target=setter).start()
```

##### 3.4.5 Condition（条件变量）

```python
cond = threading.Condition()
queue = []

def producer():
    with cond:
        queue.append("商品")
        cond.notify()  # 通知一个等待者

def consumer():
    with cond:
        while not queue:
            cond.wait()  # 释放锁并等待通知
        item = queue.pop(0)
```

#### 3.5 Queue 线程安全队列

| 类型 | 说明 |
|------|------|
| `queue.Queue` | 先进先出 FIFO |
| `queue.LifoQueue` | 后进先出 LIFO |
| `queue.PriorityQueue` | 优先级队列 |

```python
from queue import Queue

q = Queue(maxsize=10)
q.put("item")          # 入队
item = q.get()         # 出队
q.task_done()          # 标记任务完成
q.join()               # 等待所有任务完成
```

#### 3.6 ThreadPoolExecutor 线程池

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    # 方式一：submit 返回 Future
    future = executor.submit(func, arg1)
    result = future.result()

    # 方式二：map 批量提交
    results = executor.map(func, [1, 2, 3])

    # 方式三：as_completed 按完成顺序
    futures = [executor.submit(func, i) for i in range(5)]
    for f in as_completed(futures):
        print(f.result())
```

### 4. 多进程 multiprocessing

#### 4.1 Process 类

```python
from multiprocessing import Process

def worker(name):
    print(f"进程 {name} 运行中，PID: {os.getpid()}")

p = Process(target=worker, args=("A",))
p.start()
p.join()
```

#### 4.2 进程间通信

| 方式 | 说明 |
|------|------|
| `multiprocessing.Queue` | 进程安全队列 |
| `multiprocessing.Pipe` | 双向管道 |
| `multiprocessing.Value` | 共享单个值 |
| `multiprocessing.Array` | 共享数组 |
| `multiprocessing.Manager` | 共享 Python 对象（list/dict 等） |

```python
from multiprocessing import Process, Queue, Value

# Queue 通信
q = Queue()
def producer(q):
    q.put("来自子进程")
def consumer(q):
    print(q.get())

p1 = Process(target=producer, args=(q,))
p2 = Process(target=consumer, args=(q,))
```

#### 4.3 进程池

```python
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(cpu_task, range(10))
```

#### 4.4 进程 vs 线程对比

| 维度 | 多线程 threading | 多进程 multiprocessing |
|------|-----------------|----------------------|
| 内存空间 | 共享 | 独立 |
| 启动开销 | 小 | 大 |
| GIL 影响 | 受限 | 不受限 |
| 通信成本 | 直接共享变量 | 需 IPC（Queue/Pipe） |
| 适用场景 | IO 密集型 | CPU 密集型 |
| 稳定性 | 一个线程崩溃影响整个进程 | 进程独立崩溃 |

### 5. asyncio 异步编程

#### 5.1 async/await 语法

```python
import asyncio

async def hello():
    print("Hello")
    await asyncio.sleep(1)  # 非阻塞 sleep
    print("World")

asyncio.run(hello())
```

#### 5.2 协程与事件循环

- **协程 coroutine**：用 `async def` 定义的函数，调用它返回协程对象而非立即执行
- **事件循环 Event Loop**：调度协程执行的引擎，`asyncio.run()` 创建并运行事件循环

#### 5.3 Task 任务调度

```python
import asyncio

async def fetch(name, delay):
    await asyncio.sleep(delay)
    return f"{name} 完成"

async def main():
    # 方式一：create_task
    t1 = asyncio.create_task(fetch("A", 1))
    t2 = asyncio.create_task(fetch("B", 2))
    r1, r2 = await asyncio.gather(t1, t2)  # 并发等待全部完成

    # 方式二：wait（返回两个集合）
    done, pending = await asyncio.wait([t1, t2])

asyncio.run(main())
```

#### 5.4 asyncio.sleep vs time.sleep

| 函数 | 阻塞 | 适用 |
|------|------|------|
| `time.sleep(n)` | 阻塞整个线程 | 同步代码 |
| `await asyncio.sleep(n)` | 不阻塞事件循环 | 异步代码 |

```python
# 错误：在协程里调用 time.sleep 会阻塞事件循环！
async def bad():
    time.sleep(2)  # ❌ 阻塞所有协程

# 正确：使用 asyncio.sleep
async def good():
    await asyncio.sleep(2)  # ✅ 让出控制权
```

#### 5.5 异步 IO 库

| 库 | 用途 |
|----|------|
| aiohttp | 异步 HTTP 客户端/服务端 |
| httpx | 同步/异步两用 HTTP 客户端 |
| asyncio.Queue | 异步队列 |
| aiofiles | 异步文件 IO |

#### 5.6 async with / async for

```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
        data = await resp.json()

async for item in async_generator():
    process(item)
```

#### 5.7 并发 vs 串行性能对比

```python
import asyncio
import time

async def task(n):
    await asyncio.sleep(1)
    return n

# 串行：3 秒
async def serial():
    await task(1)
    await task(2)
    await task(3)

# 并发：约 1 秒
async def concurrent():
    await asyncio.gather(task(1), task(2), task(3))
```

### 6. concurrent.futures 统一接口

#### 6.1 两类执行器

| 执行器 | 模块 | 适用 |
|-------|------|------|
| `ThreadPoolExecutor` | 线程池 | IO 密集型 |
| `ProcessPoolExecutor` | 进程池 | CPU 密集型 |

两者 API 完全一致，方便切换。

#### 6.2 三种提交方式

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=4) as executor:
    # 1. submit：返回 Future
    future = executor.submit(func, arg)
    future.add_done_callback(callback)
    result = future.result()

    # 2. map：批量提交，保持顺序
    results = list(executor.map(func, [1, 2, 3]))

    # 3. as_completed：按完成顺序
    futures = {executor.submit(func, i): i for i in range(3)}
    for f in as_completed(futures):
        print(f.result())
```

#### 6.3 Future 对象

| 方法 | 用途 |
|------|------|
| `future.result(timeout)` | 获取结果（阻塞） |
| `future.done()` | 是否完成 |
| `future.cancel()` | 取消（未开始才有效） |
| `future.add_done_callback(fn)` | 完成回调 |
| `future.exception()` | 获取异常 |

### 7. 并发模型选型

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 网络爬虫、API 聚合（高并发 IO） | asyncio | 单线程高并发、低开销 |
| 少量并发 IO（< 100） | threading | 简单直接 |
| CPU 密集型计算 | multiprocessing | 真正并行、绕过 GIL |
| 混合型任务 | concurrent.futures | 统一接口、灵活切换 |
| Web 服务（大量连接） | asyncio（FastAPI/aiohttp） | 高并发优势 |

## 关键知识点总结

### GIL 原理图

```
┌────────────────────────────────────────────────┐
│              CPython 解释器进程                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Thread A │  │ Thread B │  │ Thread C │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │              │              │           │
│       └──────┬───────┴───────┬──────┘          │
│              │   GIL 锁       │                 │
│              ▼               ▼                 │
│       ┌──────────────────────────────┐         │
│       │  同一时刻只允许一个线程       │         │
│       │  执行 Python 字节码           │         │
│       └──────────────────────────────┘         │
└────────────────────────────────────────────────┘
```

### 线程同步工具速查表

| 工具 | 用途 | 典型场景 |
|------|------|---------|
| Lock | 互斥访问共享资源 | 计数器累加 |
| RLock | 可重入互斥锁 | 递归函数加锁 |
| Semaphore | 限制并发数 | 连接池 |
| Event | 事件通知 | 启动信号 |
| Condition | 条件等待/通知 | 生产者-消费者 |
| Queue | 线程安全队列 | 任务分发 |

### 并发模型选型决策表

```
任务特征?
│
├─ IO 密集型?
│   ├─ 并发量大（> 1000）→ asyncio
│   ├─ 并发量小（< 100） → threading
│   └─ 混合场景          → ThreadPoolExecutor
│
├─ CPU 密集型?
│   ├─ 简单并行          → ProcessPoolExecutor
│   └─ 复杂任务分发      → multiprocessing.Pool
│
└─ 混合型?
    └─ asyncio + ProcessPool（run_in_executor）
```

### asyncio 核心 API 速查

| API | 用途 |
|-----|------|
| `asyncio.run(coro)` | 运行顶层协程 |
| `asyncio.create_task(coro)` | 创建 Task |
| `asyncio.gather(*tasks)` | 并发等待全部 |
| `asyncio.wait(tasks)` | 返回 (done, pending) |
| `asyncio.sleep(n)` | 非阻塞 sleep |
| `asyncio.Queue` | 异步队列 |
| `asyncio.Lock` | 异步锁 |
| `asyncio.Semaphore` | 异步信号量 |
| `loop.run_in_executor(pool, fn)` | 在线程/进程池中运行同步函数 |

## 实战练习

### 练习 1：多线程电商价格爬虫

用 `threading` + `Queue` 实现一个生产者-消费者模型：
- 生产者向队列放入 100 个商品 URL
- 5 个消费者线程从队列取出 URL，模拟抓取价格（`time.sleep` 模拟网络延迟）
- 使用 `Lock` 保护一个全局字典，统计每个商品类目的平均价格
- 使用 `Queue.join()` 等待全部完成

### 练习 2：asyncio 批量 API 聚合

用 `asyncio` + `asyncio.gather` 并发请求 50 个商品详情 API（可用本地 aiohttp 服务或 `asyncio.sleep` 模拟）：
- 实现并发限流（`asyncio.Semaphore` 限制最多 10 个并发）
- 对比串行与并发的耗时
- 处理单个请求失败的容错（try/except 不影响其他请求）

### 练习 3：CPU 密集型任务对比

实现一个 CPU 密集型任务（如计算 1000 万以内所有质数之和）：
- 分别用单线程、多线程（5 线程）、多进程（5 进程）实现
- 用 `time.perf_counter()` 计时
- 观察并解释三种方式的速度差异，验证 GIL 的影响
