# Day07 - 数据库集成(SQLite)

> 前面的数据都在内存/字典里，重启就没了。常规 API 都要**接数据库**。
> 本讲用标准库自带的 **SQLite**（零安装、单文件、适合学习与轻量应用）做一套完整的
> CRUD，并把数据库访问封装成依赖，让接口真正"持久化"。

## 本讲目标

1. 用 `sqlite3` 建立一张表 + 连接管理的依赖（沿用 Day04 的 `yield` 依赖）。
2. 实现增(Create)、查(Read 单个/列表)、改(Update)、删(Delete) 四类接口。
3. 用 Pydantic 模型定义输入/输出。
4. 用 TestClient 走一遍完整 CRUD 并断言结果。

## 核心概念

| 概念 | 说明 |
|------|------|
| `sqlite3` | Python 内置的 SQLite 驱动 |
| 内存库 | `":memory:"` 连接，跑完即弃，适合演示 |
| `yield` 依赖 | 每个请求一个连接，用完自动 `close` |
| CRUD | Create / Read / Update / Delete |
| `INSERT` / `SELECT` / `UPDATE` / `DELETE` | 最基础的 SQL 语句 |

## 连接管理依赖

```python
import sqlite3

def get_db():
    conn = sqlite3.connect(":memory:")   # 内存库
    conn.row_factory = sqlite3.Row       # 让查询结果能像 dict 一样访问
    yield conn
    conn.close()

def run_in_db(conn, sql, params=()):
    """执行 SQL 并返回最后插入的 rowid。"""
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.lastrowid
```

## 一个接口示例

```python
@app.post("/items", response_model=ItemOut, status_code=201)
def create_item(item: ItemIn, db=Depends(get_db)):
    rid = run_in_db(db, "INSERT INTO items(name, price) VALUES(?, ?)",
                    (item.name, item.price))
    row = db.execute("SELECT * FROM items WHERE id=?", (rid,)).fetchone()
    return dict(row)
```

## 运行

```bash
python "Code/07-sqlite-crud.py"
```

> 本讲用内存库跑完即弃，不会在磁盘留下数据库文件。真实项目改用文件路径即可持久化。

## 你要体会的

- 数据库访问放进 `yield` 依赖，接口函数只需 `db=Depends(get_db)`，干净可测。
- SQL 是操作数据的地基；尽量用 `?` 占位符防 SQL 注入。
- CRUD 对应 GET/POST 的 create/read + PUT/PATCH 的 update + DELETE 的 delete，一一对应。
- FastAPI 本身不绑定 ORM，你可以平滑升级到 SQLAlchemy/Prisma/Alembic 等。