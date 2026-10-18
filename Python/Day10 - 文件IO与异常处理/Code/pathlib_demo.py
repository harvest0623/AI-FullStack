# 文件用途：pathlib 路径操作练习
# 演示 Path 创建/拼接/exists/is_file/mkdir/glob/rglob/read_text/write_text
# 电商场景：遍历数据目录、查找所有 JSON 文件
# 运行方式：python pathlib_demo.py

from pathlib import Path
from datetime import datetime


def demo_path_creation() -> None:
    """路径创建与拼接"""
    print('=== 路径创建 ===')
    # 用 / 运算符拼接（推荐，跨平台）
    p1 = Path('data') / 'products' / 'list.json'
    print(f'/ 拼接: {p1}')

    # 也可直接传完整字符串
    p2 = Path('data/orders/2026.csv')
    print(f'完整字符串: {p2}')

    # 特殊路径
    print(f'当前目录: {Path.cwd()}')
    print(f'主目录: {Path.home()}')

    # 路径属性
    p = Path('data') / 'products' / 'list.json'
    print(f'\n路径属性 ({p}):')
    print(f'  name   = {p.name}')        # list.json
    print(f'  stem   = {p.stem}')        # list
    print(f'  suffix = {p.suffix}')      # .json
    print(f'  parent = {p.parent}')      # data/products
    print(f'  parts  = {p.parts}')       # ('data', 'products', 'list.json')


def demo_exists_check() -> None:
    """存在性判断"""
    print('=== 存在性判断 ===')
    p = Path('data') / 'demo.txt'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('test', encoding='utf-8')

    print(f'{p} exists  = {p.exists()}')
    print(f'{p} is_file = {p.is_file()}')
    print(f'{p} is_dir  = {p.is_dir()}')

    dir_p = Path('data')
    print(f'{dir_p} is_dir = {dir_p.is_dir()}')

    # 不存在的路径
    no = Path('not_exist.txt')
    print(f'{no} exists = {no.exists()}')


def demo_mkdir() -> None:
    """创建目录"""
    print('=== 创建目录 ===')
    # parents=True 递归创建，exist_ok=True 已存在不报错
    deep = Path('data') / 'eshop' / '2026' / '07'
    deep.mkdir(parents=True, exist_ok=True)
    print(f'创建多层目录: {deep} exists={deep.exists()}')

    # 写一个文件进去
    f = deep / 'summary.txt'
    f.write_text(f'生成于 {datetime.now()}', encoding='utf-8')
    print(f'写入文件: {f}')


def demo_read_write() -> None:
    """pathlib 文件读写"""
    print('=== pathlib 读写 ===')
    p = Path('data') / 'config.txt'
    p.parent.mkdir(parents=True, exist_ok=True)

    # 一次写完
    p.write_text('eshop 配置\n版本=1.0\n', encoding='utf-8')
    # 一次读完
    text = p.read_text(encoding='utf-8')
    print(f'读回: {text!r}')

    # 二进制
    p2 = Path('data') / 'bin.dat'
    p2.write_bytes(b'\x01\x02\x03')
    print(f'二进制: {p2.read_bytes()!r}')

    # 文件信息
    print(f'文件大小: {p.stat().st_size} 字节')
    # 修改时间（时间戳转可读）
    import datetime as dt
    mtime = dt.datetime.fromtimestamp(p.stat().st_mtime)
    print(f'修改时间: {mtime}')


def demo_glob() -> None:
    """glob 模式匹配"""
    print('=== glob 模式匹配 ===')
    # 先造一些测试文件
    base = Path('data') / 'glob_demo'
    base.mkdir(parents=True, exist_ok=True)
    for name in ['a.json', 'b.json', 'c.csv', 'd.txt']:
        (base / name).write_text(name, encoding='utf-8')
    # 子目录造一个 json
    sub = base / 'sub'
    sub.mkdir(exist_ok=True)
    (sub / 'deep.json').write_text('deep', encoding='utf-8')

    # glob 只匹配当前目录
    print('glob("*.json") 当前目录:')
    for p in sorted(base.glob('*.json')):
        print(f'  {p.name}')

    # rglob 递归匹配所有子目录
    print('rglob("*.json") 递归:')
    for p in sorted(base.rglob('*.json')):
        print(f'  {p.relative_to(base)}')   # 相对路径显示

    # glob 所有文件
    print('glob("*") 所有条目:')
    for p in sorted(base.glob('*')):
        kind = '目录' if p.is_dir() else '文件'
        print(f'  [{kind}] {p.name}')


def demo_eshop_scan() -> None:
    """电商场景：遍历数据目录，统计所有 JSON 文件"""
    print('=== 电商场景：扫描数据目录 ===')
    data_dir = Path('data') / 'eshop_data'
    data_dir.mkdir(parents=True, exist_ok=True)

    # 模拟生成电商数据文件
    (data_dir / 'products.json').write_text('{"items": []}', encoding='utf-8')
    (data_dir / 'orders.json').write_text('{"orders": []}', encoding='utf-8')
    (data_dir / 'customers.csv').write_text('id,name\n1,张三\n', encoding='utf-8')
    sub = data_dir / 'backup'
    sub.mkdir(exist_ok=True)
    (sub / 'products_backup.json').write_text('{"backup": true}', encoding='utf-8')

    # 扫描所有 JSON 文件
    print(f'扫描 {data_dir} 下所有 JSON 文件:')
    json_files = list(data_dir.rglob('*.json'))
    total_size = 0
    for f in json_files:
        size = f.stat().st_size
        total_size += size
        print(f'  {f.relative_to(data_dir)} ({size} bytes)')
    print(f'共 {len(json_files)} 个 JSON 文件，总 {total_size} bytes')

    # 按扩展名分类统计
    from collections import Counter
    ext_counter = Counter(p.suffix for p in data_dir.rglob('*') if p.is_file())
    print(f'扩展名分布: {dict(ext_counter)}')


def demo_path_operations() -> None:
    """路径运算：resolve / relative_to / with_suffix / with_name"""
    print('=== 路径运算 ===')
    p = Path('data') / 'products.json'

    # resolve 转绝对路径
    print(f'resolve: {p.resolve()}')

    # relative_to 求相对路径
    base = Path('data')
    print(f'relative_to(data): {p.relative_to(base)}')

    # with_suffix 改扩展名
    print(f'with_suffix(.csv): {p.with_suffix(".csv")}')

    # with_name 改文件名
    print(f'with_name(items.json): {p.with_name("items.json")}')

    # joinpath 也可拼接
    print(f'joinpath: {Path("data").joinpath("a", "b", "c.txt")}')


def main() -> None:
    demos = [
        demo_path_creation,
        demo_exists_check,
        demo_mkdir,
        demo_read_write,
        demo_glob,
        demo_eshop_scan,
        demo_path_operations,
    ]
    for demo in demos:
        demo()
        print()


if __name__ == '__main__':
    main()
