"""
Day04 练习：依赖注入 Depends
=========================
演示: 分页参数依赖、token 解析依赖、以及带 yield 的资源生命周期依赖。

运行:
  python "Code/04-dependency.py"
"""
from fastapi import FastAPI, Depends, Header
from fastapi.testclient import TestClient

app = FastAPI(title="依赖注入演示")


# ---------- 1. 分页参数依赖 ----------
def pagination(skip: int = 0, limit: int = 10):
    """把 skip/limit 两个查询参数打包成 dict, 注入给接口。"""
    return {"skip": skip, "limit": limit}


# ---------- 2. token 解析依赖 ----------
def require_user(authorization: str | None = Header(default=None)):
    """简化的 token 识别: 从 Authorization 头取出用户名。"""
    if authorization and authorization.startswith("Bearer "):
        return {"user": authorization.split(" ", 1)[1], "scopes": ["read"]}
    return {"user": "anonymous", "scopes": []}


# ---------- 3. 带 yield 的资源生命周期依赖 ----------
def opened_conn():
    """模拟"开一把数据库连接", 用完自动关。"""
    conn = {"id": hash("conn")}
    print("   [依赖] 打开连接:", conn)
    yield conn                                   # 请求处理期间注入的是 yield 的这个值
    print("   [依赖] 关闭连接:", conn)


# ---------- 接口 ----------
@app.get("/items")
def list_items(page: dict = Depends(pagination)):
    """使用分页依赖。"""
    return {"data": f"第 {page['skip']+1}-{page['skip']+page['limit']} 条", "page": page}

@app.get("/me")
def who_am_i(u: dict = Depends(require_user)):
    """使用 token 解析依赖。"""
    return u

@app.get("/report")
def make_report(conn: dict = Depends(opened_conn)):
    """使用生命周期依赖。"""
    # 处理期间可以放心用 conn, 请求结束自动 close
    return {"using": conn, "ok": True}


client = TestClient(app)

print("1) 不带分页参数 -> 用默认 skip=0,limit=10")
r = client.get("/items")
print(f"   {r.json()}")
assert r.json()["page"] == {"skip": 0, "limit": 10}

print("2) 带分页参数 ?skip=5&limit=3 -> 注入不同值")
r = client.get("/items?skip=5&limit=3")
print(f"   {r.json()}")
assert r.json()["page"] == {"skip": 5, "limit": 3}

print("3) 无 token -> 匿名")
r = client.get("/me")
print(f"   {r.json()}")
assert r.json()["user"] == "anonymous"

print("4) 带 token -> 识别出用户")
r = client.get("/me", headers={"Authorization": "Bearer kate"})
print(f"   {r.json()}")
assert r.json()["user"] == "kate"

print("5) 生命周期依赖(看打印顺序)")
r = client.get("/report")
print(f"   {r.json()}")

print("\n全部通过 ✓  依赖即复用: 公共逻辑抽出来, 接口只声明需要什么")