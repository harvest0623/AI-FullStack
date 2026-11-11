"""
Day07 练习：SQLite 数据库集成 —— 完整 CRUD
=====================================
用内存 SQLite + yield 依赖, 实现商品的增删改查, 用 TestClient 走完整流程。

运行:
  python "Code/07-sqlite-crud.py"
"""
import sqlite3
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI(title="SQLite CRUD")

# ---------- 模型 ----------
class ItemIn(BaseModel):
    name: str
    price: float

class ItemOut(ItemIn):
    id: int


# ---------- 建库 + 连接管理 ----------
def setUp_conn():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row                 # 结果可按列名访问
    conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 " name TEXT, price REAL)")
    conn.commit()
    return conn

_db = setUp_conn()

def get_db():
    """每个请求给一个连接, 用完自动 close(这里共用一个内存库实例)。"""
    yield _db

def run(db, sql, params=()):
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid

def fetch_one(db, sql, params=()):
    row = db.execute(sql, params).fetchone()
    return dict(row) if row else None


# ---------- CRUD 接口 ----------
@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemIn, db=Depends(get_db)):
    rid = run(db, "INSERT INTO items(name, price) VALUES(?, ?)", (item.name, item.price))
    return fetch_one(db, "SELECT * FROM items WHERE id=?", (rid,))

@app.get("/items/{item_id}", response_model=ItemOut)
def read_item(item_id: int, db=Depends(get_db)):
    row = fetch_one(db, "SELECT * FROM items WHERE id=?", (item_id,))
    if not row:
        raise HTTPException(status_code=404, detail="商品不存在")
    return row

@app.get("/items", response_model=list[ItemOut])
def list_items(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM items ORDER BY id").fetchall()
    return [dict(r) for r in rows]

@app.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, item: ItemIn, db=Depends(get_db)):
    run(db, "UPDATE items SET name=?, price=? WHERE id=?",
        (item.name, item.price, item_id))
    row = fetch_one(db, "SELECT * FROM items WHERE id=?", (item_id,))
    if not row:
        raise HTTPException(status_code=404, detail="商品不存在")
    return row

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db=Depends(get_db)):
    run(db, "DELETE FROM items WHERE id=?", (item_id,))


client = TestClient(app)

print("== 完整 CRUD 流程 ==")
print("  [创建]")
rid = client.post("/items", json={"name": "键盘", "price": 299}).json()["id"]
print(f"    创建成功 id={rid}")
rid2 = client.post("/items", json={"name": "鼠标", "price": 89}).json()["id"]

print("  [读取列表]")
r = client.get("/items")
print(f"    共 {len(r.json())} 条 -> {r.json()}")

print("  [读取单个]")
r = client.get(f"/items/{rid}")
assert r.json()["name"] == "键盘"
print(f"    GET /items/{rid} -> {r.json()}")

print("  [更新]")
r = client.put(f"/items/{rid}", json={"name": "机械键盘Pro", "price": 399})
assert r.json()["price"] == 399 and r.json()["name"] == "机械键盘Pro"
print(f"    PUT -> {r.json()}")

print("  [删除]")
r = client.delete(f"/items/{rid2}")
assert r.status_code == 204
print(f"    DELETE /items/{rid2} -> {r.status_code}")

print("  [读取已删除 -> 404]")
r = client.get(f"/items/{rid2}")
assert r.status_code == 404
print(f"    GET /items/{rid2} -> {r.status_code}")

print("  [最终列表]")
print(f"    {client.get('/items').json()}")

print("\n全部通过 ✓  数据已持久化到 SQLite, CRUD 四件事闭环 Database")