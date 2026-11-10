"""
Day01 练习：认识 FastAPI 并搭出第一个接口
=======================================
用 TestClient 发起真实 HTTP 请求, 验证接口返回的状态码与 JSON 内容。

运行:
  python "Code/01-first-endpoint.py"
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------- 1. 创建应用 + 定义接口 ----------
app = FastAPI(title="我的第一个 FastAPI")

@app.get("/")
def root():
    """根路径: 返回问候。"""
    return {"message": "Hello World"}

@app.get("/hello/{name}")
def hello(name: str):
    """路径参数: /hello/小明  -> 针对某人返回问候。"""
    return {"name": name, "msg": f"你好, {name}!"}


# ---------- 2. 用 TestClient 请求并验证 ----------
client = TestClient(app)

print("=" * 50)
print("1) GET /")
r = client.get("/")
print(f"   status_code: {r.status_code}")
print(f"   body       : {r.json()}")
assert r.status_code == 200
assert r.json() == {"message": "Hello World"}
print("   => 通过\n")

print("=" * 50)
print("2) GET /hello/小明")
r = client.get("/hello/小明")
print(f"   status_code: {r.status_code}")
print(f"   body       : {r.json()}")
assert r.json()["msg"] == "你好, 小明!"
print("   => 通过\n")

print("=" * 50)
print("3) 不存在的路径 -> 应该 404")
r = client.get("/no-such-page")
print(f"   status_code: {r.status_code}  (期待 404)")
assert r.status_code == 404
print("   => 通过\n")

# ---------- 3. 打印自动生成的路由表 ----------
print("=" * 50)
print("当前应用注册的接口:")
for route in app.routes:
    methods = getattr(route, "methods", None)
    if methods:
        print(f"   {list(methods)} {route.path}")

print("\n真机运行方式:  uvicorn 文件名:app --reload  (然后打开 /docs)")