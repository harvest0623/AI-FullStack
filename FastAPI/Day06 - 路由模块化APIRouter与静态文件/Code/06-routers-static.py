"""
Day06 练习：APIRouter 模块化 + 静态文件
=====================================
把用户/订单两个业务拆成独立 router, 挂载静态目录, 最后用 TestClient 验证。

运行:
  python "Code/06-routers-static.py"
"""
import os
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

# ---------- 用户模块 ----------
user_router = APIRouter(prefix="/users", tags=["用户"])

@user_router.get("/{uid}")
def get_user(uid: int):
    """ -> /users/{uid} """
    return {"uid": uid, "name": f"用户{uid}"}

@user_router.get("")
def list_users():
    """ -> /users """
    return [{"uid": 1}, {"uid": 2}]


# ---------- 订单模块 ----------
order_router = APIRouter(prefix="/orders", tags=["订单"])

@order_router.get("/{order_id}")
def get_order(order_id: int):
    """ -> /orders/{order_id} """
    return {"order_id": order_id, "amount": 99.0}


# ---------- 主应用 ----------
app = FastAPI(title="模块化 API")
app.include_router(user_router)
app.include_router(order_router)

# 挂载静态目录(本脚本目录下的 static/, 不存在就先创建)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
# 放一个欢迎页
welcome = os.path.join(static_dir, "hello.txt")
if not os.path.exists(welcome):
    with open(welcome, "w", encoding="utf-8") as f:
        f.write("这是静态文件里的问候。")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


client = TestClient(app)

print("1) 用户模块: GET /users/7")
r = client.get("/users/7")
assert r.status_code == 200 and r.json()["uid"] == 7
print(f"   status={r.status_code} body={r.json()}")

print("2) 用户模块: GET /users")
r = client.get("/users")
assert len(r.json()) == 2
print(f"   status={r.status_code} body={r.json()}")

print("3) 订单模块: GET /orders/42")
r = client.get("/orders/42")
assert r.status_code == 200 and r.json()["order_id"] == 42
print(f"   status={r.status_code} body={r.json()}")

print("4) 静态文件: GET /static/hello.txt")
r = client.get("/static/hello.txt")
print(f"   status={r.status_code} content={r.text!r}")
assert r.status_code == 200 and "问候" in r.text

print("5) 路由总览(带前缀后)")
for route in app.routes:
    methods = getattr(route, "methods", None)
    if methods:
        print(f"   {sorted(methods)} {route.path}")

print("\n全部通过 ✓  一个业务一个 router, 主应用只管汇总挂载")