# 文件用途：contextlib 练习
# 演示 @contextmanager、closing/suppress/redirect_stdout/ExitStack
# 电商场景：用 @contextmanager 实现计时器和临时目录、用 suppress 忽略文件不存在错误
# 运行方式：python contextlib_demo.py

import io
import os
import time
import shutil
import tempfile
from pathlib import Path
from contextlib import contextmanager, closing, suppress, redirect_stdout, ExitStack


# ====== @contextmanager 实现 ======
@contextmanager
def timer(name: str = '代码块'):
    """计时器上下文（生成器实现版）

    yield 之前 = __enter__，yield 之后 = __exit__。
    yield 出去的值就是 as 变量拿到的值。
    """
    start = time.perf_counter()
    print(f'  [{name}] 开始...')
    try:
        yield {'start': start}     # with 块内拿到这个字典
    finally:
        elapsed = time.perf_counter() - start
        print(f'  [{name}] 结束，耗时 {elapsed*1000:.2f} ms')


@contextmanager
def temporary_dir(prefix: str = 'eshop_'):
    """临时目录上下文：进入时创建，退出时自动删除

    用 tempfile 创建临时目录，离开 with 自动清理。
    """
    path = Path(tempfile.mkdtemp(prefix=prefix))
    print(f'  [tmpdir] 创建临时目录: {path}')
    try:
        yield path      # with 块内拿到目录路径
    finally:
        # 无论是否异常都清理
        shutil.rmtree(path, ignore_errors=True)
        print(f'  [tmpdir] 已删除: {path}')


@contextmanager
def db_transaction(dsn: str):
    """电商场景：数据库事务上下文（@contextmanager 版）

    对比 context_manager.py 里的类实现，生成器版更简洁。
    """
    print(f'  [DB] 连接 {dsn}，开启事务')
    try:
        yield dsn       # with 块内拿到 dsn
        print(f'  [DB] 提交事务（COMMIT）')
    except Exception as e:
        print(f'  [DB] 回滚事务（ROLLBACK）: {type(e).__name__}: {e}')
        raise           # 重新抛出，让上层感知


@contextmanager
def change_cwd(path: Path):
    """切换工作目录上下文：退出时恢复原目录"""
    original = Path.cwd()
    os.chdir(path)
    print(f'  [cwd] 切换到 {path}')
    try:
        yield path
    finally:
        os.chdir(original)
        print(f'  [cwd] 恢复到 {original}')


# ====== 演示函数 ======
def demo_contextmanager_timer() -> None:
    """@contextmanager 实现计时器"""
    print('=== @contextmanager 计时器 ===')
    with timer('数据处理') as info:
        time.sleep(0.02)
        total = sum(i * i for i in range(50000))
        print(f'  计算结果: {total}')
    print(f'  （yield 出去的值: {info}）')


def demo_temporary_dir() -> None:
    """临时目录上下文"""
    print('=== 临时目录 temporary_dir ===')
    with temporary_dir() as tmp:
        # 在临时目录里写文件
        f = tmp / 'products.json'
        f.write_text('{"items": []}', encoding='utf-8')
        print(f'  写入文件: {f} (exists={f.exists()})')
        # 列出目录内容
        print(f'  目录内容: {list(tmp.iterdir())}')
    # 离开后目录已被删除
    print(f'  退出后目录是否还在: {tmp.exists()}')


def demo_db_transaction() -> None:
    """电商场景：数据库事务（生成器版）"""
    print('=== 电商场景：数据库事务（@contextmanager） ===')

    # 正常场景
    print('  [正常] 下单:')
    with db_transaction('eshop://db'):
        print('  执行 INSERT order')
        print('  执行 UPDATE stock')
    print()

    # 异常场景
    print('  [异常] 下单:')
    try:
        with db_transaction('eshop://db'):
            print('  执行 INSERT order')
            raise ValueError('库存不足')
    except ValueError:
        print('  （异常已传播）')


def demo_closing() -> None:
    """closing：自动调用 close()"""
    print('=== closing 自动关闭 ===')

    # closing 包装任何有 close() 方法的对象
    class Resource:
        def __init__(self, name):
            self.name = name
            print(f'  [Resource] 打开 {name}')

        def work(self):
            print(f'  [Resource] {self.name} 工作中')

        def close(self):
            print(f'  [Resource] 关闭 {self.name}')

    with closing(Resource('连接A')) as r:
        r.work()
    # 离开 with 自动调 r.close()


def demo_suppress() -> None:
    """suppress：忽略指定异常"""
    print('=== suppress 忽略异常 ===')

    # 不用 suppress 的写法
    print('  传统写法:')
    try:
        os.remove('不存在的文件.txt')
    except FileNotFoundError:
        print('    文件不存在，忽略')

    # 用 suppress 更简洁
    print('  suppress 写法:')
    with suppress(FileNotFoundError):
        os.remove('不存在的文件.txt')
        print('    删除成功')
    print('    （文件不存在被自动忽略）')

    # 电商场景：清理临时文件，不存在不报错
    print('  电商场景：清理临时数据文件')
    tmp_files = ['data/tmp1.json', 'data/tmp2.json', 'data/tmp3.json']
    Path('data').mkdir(exist_ok=True)
    # 只创建 tmp1
    Path('data/tmp1.json').write_text('{}', encoding='utf-8')
    for f in tmp_files:
        with suppress(FileNotFoundError):
            Path(f).unlink()
            print(f'    已删除 {f}')
    print('    清理完成（不存在的被忽略）')


def demo_redirect_stdout() -> None:
    """redirect_stdout：重定向标准输出"""
    print('=== redirect_stdout 重定向输出 ===')

    # 捕获 print 的输出
    buf = io.StringIO()
    with redirect_stdout(buf):
        print('这行被重定向到 buf')
        print('这行也是')
        print('中文测试')

    captured = buf.getvalue()
    print(f'  捕获到的内容: {captured!r}')

    # 电商场景：测试时捕获日志输出
    print('  电商场景：捕获生成报告的输出')
    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        print('商品汇总: 25 件')
        print('订单汇总: 100 笔')
        print('营收汇总: ¥50,000')
    report = buf2.getvalue()
    print(f'  报告内容:\n{report}')


def demo_exit_stack() -> None:
    """ExitStack：管理多个动态上下文"""
    print('=== ExitStack 管理多个上下文 ===')

    # 静态多个 with：嵌套
    print('  传统嵌套 with:')
    with open('data/a.txt', 'w', encoding='utf-8') as f1:
        with open('data/b.txt', 'w', encoding='utf-8') as f2:
            f1.write('A')
            f2.write('B')
    print('    两个文件写入完成')

    # ExitStack：动态管理多个上下文，避免深层嵌套
    print('  ExitStack 动态管理:')
    Path('data').mkdir(exist_ok=True)
    files = []
    with ExitStack() as stack:
        for name in ['x.txt', 'y.txt', 'z.txt']:
            f = stack.enter_context(open(f'data/{name}', 'w', encoding='utf-8'))
            files.append(f)
            f.write(name)
        # 退出时按进入相反顺序关闭
    print(f'    写入 {len(files)} 个文件，全部已自动关闭')

    # 结合 @contextmanager 和 ExitStack
    print('  ExitStack + 计时器:')
    with ExitStack() as stack:
        stack.enter_context(timer('阶段1'))
        time.sleep(0.01)
        stack.enter_context(timer('阶段2'))
        time.sleep(0.01)
        print('    两阶段任务完成')


def demo_eshop_batch_process() -> None:
    """电商场景：批量处理（组合多个上下文）"""
    print('=== 电商场景：批量数据处理 ===')
    # 场景：在临时目录里处理数据，用计时器测耗时，
    #       用 suppress 忽略清理时的错误

    with timer('批量处理'), temporary_dir('batch_'):
        # 在临时目录里模拟批量处理
        pass

    print('  清理残留文件:')
    # suppress 忽略清理时的各种错误
    for pattern in ['*.tmp', '*.bak']:
        with suppress(FileNotFoundError, PermissionError):
            for f in Path('.').glob(pattern):
                f.unlink()
                print(f'    删除 {f}')
    print('  完成')


def main() -> None:
    demos = [
        demo_contextmanager_timer,
        demo_temporary_dir,
        demo_db_transaction,
        demo_closing,
        demo_suppress,
        demo_redirect_stdout,
        demo_exit_stack,
        demo_eshop_batch_process,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
