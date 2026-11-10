"""
Day02 练习：路径参数 / 查询参数 / 请求体
=====================================
一个极简"商品接口", 演示三类参数, 并观察 FastAPI 的类型校验。

运行:
  python "Code/02-params.py"
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI(title="商品接口")

class Item(BaseModel):
    name: str
    price: float                 # 必须数值
    in_stock: bool = True        # 默认在库


# ---------- 路径参数 + 查询参数 ----------
@app.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = None, skip: int = 0, limit: int = 10):
    """取单个商品; query 提供可选过滤与分页。"""
    return {"item_id": item_id, "q": q, "skip": skip, "limit": limit}


# ---------- 请求体 ----------
@app.post("/items", status_code=201)
def create_item(item: Item):
    """新建商品(请求体为 JSON)。"""
    return {"created": item.model_dump()}


client = TestClient(app)

print("1) 路径参数: GET /items/42?q=键盘")
r = client.get("/items/42?q=键盘")
print(f"   status={r.status_code} body={r.json()}")
assert r.json()["item_id"] == 42 and r.json()["q"] == "键盘"

print("2) 路径参数类型错误: GET /items/abc  -> 期待 422")
r = client.get("/items/abc")
print(f"   status={r.status_code}")
assert r.status_code == 422

print("3) 请求体: POST /items 发送 JSON")
payload = {"name": "机械键盘", "price": 299.5}
r = client.post("/items", json=payload)
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 201
assert r.json()["created"]["name"] == "机械键盘"

print("4) 请求体缺 price: 期待 422(字段校验失败)")
r = client.post("/items", json={"name": "无价商品"})
print(f"   status={r.status_code}")
assert r.status_code == 422

print("5) 请求体 price 类型错误: 期待 422")
r = client.post("/items", json={"name": "坏数据", "price": "很贵"})
print(f"   status={r.status_code}")
assert r.status_code == 422

print("\n全部通过 ✓  关键点: 类型即校验, 一个 int/float 声明就挡住了非法输入")