"""
Day05 练习：错误处理与状态码
=========================
用 HTTPException 主动抛错, 用 status 常量写语义化状态码, 验证 404/400/200。

运行:
  python "Code/05-errors-status.py"
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI(title="错误处理演示")

# 一个假的商品库
DB = {
    1: {"name": "机械键盘", "price": 299.5},
    2: {"name": "无线鼠标", "price": 89.9},
}

class OrderIn(BaseModel):
    item_id: int
    qty: int = Field(ge=1)                       # 数量至少 1


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商品 {item_id} 不存在",
        )
    return DB[item_id]


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderIn):
    if order.item_id not in DB:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="不能下单: 商品不存在")
    if DB[order.item_id]["price"] * order.qty > 1000:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail="超出额度, 请联系客服拆分订单")
    return {"ok": True, "amount": DB[order.item_id]["price"] * order.qty}


client = TestClient(app)

print("1) 存在商品: GET /items/1")
r = client.get("/items/1")
assert r.status_code == 200
print(f"   status={r.status_code} body={r.json()}")

print("2) 不存在商品: GET /items/99 -> 404 且带 detail")
r = client.get("/items/99")
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 404
assert r.json()["detail"] == "商品 99 不存在"

print("3) 正常下单: POST /orders")
r = client.post("/orders", json={"item_id": 1, "qty": 2})
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 201

print("4) 下单商品不存在: POST /orders -> 404")
r = client.post("/orders", json={"item_id": 999, "qty": 1})
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 404

print("5) 超额下单: POST /orders -> 402")
r = client.post("/orders", json={"item_id": 1, "qty": 9})   # 299.5*9=2695.5 > 1000
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 402

print("6) 数量非法(qty=0): -> 422(校验层拦截)")
r = client.post("/orders", json={"item_id": 1, "qty": 0})
print(f"   status={r.status_code}")
assert r.status_code == 422

print("\n全部通过 ✓  HTTPException + status 常量 = 语义清晰的错误返回")