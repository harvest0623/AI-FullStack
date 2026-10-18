# 文件用途：自定义上下文管理器练习
# 类实现 __enter__/__exit__，演示上下文管理器协议
# 电商场景：数据库连接管理器、文件锁、计时器上下文
# 运行方式：python context_manager.py

import time
from pathlib import Path


# ====== 上下文管理器：文件管理 ======
class FileManager:
    """文件管理上下文管理器：自动关闭文件"""

    def __init__(self, filename, mode: str = 'r', encoding: str = 'utf-8'):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.file = None

    def __enter__(self):
        # 进入 with 时调用，返回值赋给 as 变量
        self.file = open(self.filename, self.mode, encoding=self.encoding)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 离开 with 时调用（无论是否异常）
        if self.file and not self.file.closed:
            self.file.close()
        # 返回 False 表示不抑制异常（异常继续传播）
        return False


# ====== 上下文管理器：计时器 ======
class Timer:
    """计时器上下文管理器：测量代码块耗时"""

    def __init__(self, name: str = '代码块'):
        self.name = name
        self.start = 0
        self.elapsed = 0

    def __enter__(self):
        self.start = time.perf_counter()
        print(f'  [{self.name}] 开始计时...')
        return self    # 返回自身，方便 with ... as t 后取 t.elapsed

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start
        if exc_type is None:
            print(f'  [{self.name}] 正常结束，耗时 {self.elapsed*1000:.2f} ms')
        else:
            print(f'  [{self.name}] 异常结束（{exc_type.__name__}），'
                  f'耗时 {self.elapsed*1000:.2f} ms')
        return False    # 不抑制异常


# ====== 上下文管理器：模拟数据库连接 ======
class DBConnection:
    """模拟数据库连接上下文管理器

    电商场景：自动管理事务，无异常提交，有异常回滚。
    """

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.connected = False

    def __enter__(self):
        # 模拟连接数据库
        print(f'  [DB] 连接 {self.dsn} ...')
        self.connected = True
        print(f'  [DB] 已连接，开启事务')
        return self    # 返回连接对象，可执行查询

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 无异常：提交事务
            print(f'  [DB] 提交事务（COMMIT）')
        else:
            # 有异常：回滚事务
            print(f'  [DB] 回滚事务（ROLLBACK），原因: {exc_type.__name__}: {exc_val}')
        # 关闭连接
        self.connected = False
        print(f'  [DB] 关闭连接')
        return False    # 不抑制异常，让上层感知

    def query(self, sql: str):
        """模拟执行 SQL"""
        if not self.connected:
            raise RuntimeError('数据库未连接')
        print(f'  [DB] 执行: {sql}')
        return f'结果({sql})'


# ====== 上下文管理器：文件锁 ======
class FileLock:
    """文件锁上下文管理器：简单的互斥锁

    通过创建锁文件实现互斥，离开 with 时释放。
    """

    def __init__(self, lock_path: str):
        self.lock_path = Path(lock_path)
        self.acquired = False

    def __enter__(self):
        if self.lock_path.exists():
            raise RuntimeError(f'锁文件已存在，资源被占用: {self.lock_path}')
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.write_text('locked', encoding='utf-8')
        self.acquired = True
        print(f'  [Lock] 获取锁: {self.lock_path}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired and self.lock_path.exists():
            self.lock_path.unlink()
            print(f'  [Lock] 释放锁: {self.lock_path}')
        return False


# ====== 演示函数 ======
def demo_file_manager() -> None:
    """文件管理上下文管理器"""
    print('=== FileManager 上下文管理器 ===')
    path = Path('data') / 'cm_test.txt'
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写文件
    with FileManager(path, 'w') as f:
        f.write('第一行\n')
        f.write('第二行\n')
    print(f'  写入完成，文件已自动关闭')

    # 读文件
    with FileManager(path, 'r') as f:
        content = f.read()
    print(f'  读回: {content!r}')

    # 异常时也会关闭
    print('  模拟异常时是否关闭:')
    try:
        with FileManager(path, 'r') as f:
            raise ValueError('故意出错')
    except ValueError:
        pass
    # 验证文件已关闭（FileManager 对象已销毁，但逻辑上 __exit__ 已执行）
    print(f'  异常后文件已关闭（__exit__ 被调用）')


def demo_timer() -> None:
    """计时器上下文管理器"""
    print('=== Timer 计时器 ===')
    with Timer('数据处理') as t:
        time.sleep(0.05)
        total = sum(i * i for i in range(100000))
        print(f'  计算结果: {total}')
    # 离开 with 后可取 t.elapsed
    print(f'  事后取耗时: {t.elapsed*1000:.2f} ms')

    # 异常场景
    print('  异常场景计时:')
    try:
        with Timer('可能出错的任务'):
            time.sleep(0.01)
            raise RuntimeError('任务失败')
    except RuntimeError:
        print('  （异常已向上传播）')


def demo_db_connection() -> None:
    """电商场景：数据库连接与事务管理"""
    print('=== 电商场景：数据库事务 ===')

    # 场景1：正常流程，自动提交
    print('  [场景1] 正常下单:')
    with DBConnection('eshop://localhost') as db:
        db.query('INSERT INTO orders VALUES (1001, ...)')
        db.query('UPDATE products SET stock = stock - 1 WHERE id = 1')
    print()

    # 场景2：异常流程，自动回滚
    print('  [场景2] 下单失败:')
    try:
        with DBConnection('eshop://localhost') as db:
            db.query('INSERT INTO orders VALUES (1002, ...)')
            db.query('UPDATE products SET stock = stock - 1 WHERE id = 999')
            # 模拟业务异常
            raise ValueError('商品 999 不存在')
    except ValueError:
        print('  （事务已回滚，异常已传播）')


def demo_file_lock() -> None:
    """文件锁上下文管理器"""
    print('=== 文件锁 FileLock ===')
    lock_path = Path('data') / 'eshop.lock'

    # 正常获取和释放
    with FileLock(lock_path):
        print('  执行需要互斥的操作...')
        time.sleep(0.01)
    # 锁已释放

    # 模拟锁冲突
    print('  模拟锁冲突:')
    # 先手动创建锁文件
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text('locked-by-other', encoding='utf-8')
    try:
        with FileLock(lock_path):
            print('  这行不会执行')
    except RuntimeError as e:
        print(f'  锁冲突: {e}')
    # 清理测试锁
    if lock_path.exists():
        lock_path.unlink()


def demo_exit_return_value() -> None:
    """演示 __exit__ 返回值：True 抑制异常"""
    print('=== __exit__ 返回 True 抑制异常 ===')

    class SuppressAll:
        def __enter__(self):
            print('  进入')
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                print(f'  捕获并抑制异常: {exc_type.__name__}: {exc_val}')
            print('  退出')
            return True    # 返回 True → 异常被抑制，不向外传播

    with SuppressAll():
        raise ValueError('这个异常会被吞掉')
    print('  with 块结束后继续执行（异常被抑制了）')


def main() -> None:
    demos = [
        demo_file_manager,
        demo_timer,
        demo_db_connection,
        demo_file_lock,
        demo_exit_return_value,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
