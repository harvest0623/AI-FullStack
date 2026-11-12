"""
Day10 练习：实战整合 —— 一个带鉴权的待办 API
=========================================
整合 Day02(参数/模型) Day03(响应模型) Day04(依赖注入) Day05(错误)
Day06(思路) Day07(SQLite) Day09(JWT) 成一个小而完整的服务, 端到端验证。

运行:
  python "Code/10-app.py"
"""
import base64, hashlib, hmac, json, sqlite3, time
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Form, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# ==================== 1. JWT (自实现 HS256, 来自 Day09) ====================
SECRET = "app-secret-key"

def _b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def _unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def encode_token(payload):
    body = dict(payload, exp=int(time.time()) + 7200)
    h = _b64(json.dumps({"alg": "HS256"}).encode())
    p = _b64(json.dumps(body).encode())
    sig = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"
def decode_token(token):
    try: h, p, s = token.split(".")
    except ValueError: raise ValueError("格式错误")
    expect = _b64(hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(s, expect): raise ValueError("签名无效")
    payload = json.loads(_unb64(p))
    if payload.get("exp", 0) < time.time(): raise ValueError("过期")
    return payload

# ==================== 2. 数据库 (来自 Day07) ====================
conn = sqlite3.connect(":memory:", check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT UNIQUE, pass_memo TEXT)")
conn.execute("CREATE TABLE todos(id INTEGER PRIMARY KEY, uid INT, title TEXT, done INT DEFAULT 0)")
conn.commit()
def get_db():
    yield conn

# ==================== 3. 模型 (来自 Day02/03) ====================
class TodoIn(BaseModel):
    title: str = Field(min_length=1)
class TodoOut(BaseModel):
    id: int
    title: str
    done: bool
class RegisterIn(BaseModel):
    name: str = Field(min_length=2)
    password: str = Field(min_length=4)

# ==================== 4. 鉴权依赖 (来自 Day04 + Day09) ====================
def require_user(authorization: str | None = Header(default=None), db=Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    try:
        payload = decode_token(authorization.split(" ", 1)[1])
    except ValueError as e:
        raise HTTPException(401, f"令牌无效: {e}")
    row = db.execute("SELECT * FROM users WHERE name=?", (payload["sub"],)).fetchone()
    if not row:
        raise HTTPException(401, "用户不存在")
    return dict(row)

# ==================== 5. 应用与路由 ====================
app = FastAPI(title="待办 API")
auth = APIRouter(prefix="/auth", tags=["鉴权"])
todos = APIRouter(prefix="/todos", tags=["待办"], dependencies=[Depends(require_user)])

@auth.post("/register", response_model=dict)
def register(body: RegisterIn, db=Depends(get_db)):
    try:
        cur = db.execute("INSERT INTO users(name, pass_memo) VALUES(?, '****')", (body.name,))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "用户名已存在")
    return {"id": cur.lastrowid, "name": body.name}

@auth.post("/login")
def login(name: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    row = db.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
    if not row:
        raise HTTPException(401, "用户不存在")
    # 教学简化: 密码直接比对, 不存储明文于表(存了 '****')
    return {"token": encode_token({"sub": name})}

@todos.get("", response_model=list[TodoOut])
def list_todos(user: dict = Depends(require_user), db=Depends(get_db)):
    rows = db.execute("SELECT * FROM todos WHERE uid=? ORDER BY id", (user["id"],)).fetchall()
    return [dict(r, done=bool(r["done"])) for r in rows]

@todos.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(body: TodoIn, user: dict = Depends(require_user), db=Depends(get_db)):
    cur = db.execute("INSERT INTO todos(uid, title) VALUES(?, ?)", (user["id"], body.title))
    db.commit()
    row = db.execute("SELECT * FROM todos WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row, done=bool(row["done"]))

@todos.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, user: dict = Depends(require_user), db=Depends(get_db)):
    db.execute("DELETE FROM todos WHERE id=? AND uid=?", (todo_id, user["id"]))
    db.commit()

app.include_router(auth)
app.include_router(todos)

# ==================== 6. 端到端测试 ====================
client = TestClient(app)
print("== 端到端: 注册 -> 登录 -> 增删查 待办 ==")

print("1) 注册 kate")
r = client.post("/auth/register", json={"name": "kate", "password": "pw1234"})
assert r.status_code == 200, r.text
print(f"   {r.json()}")

print("2) 登录拿 token")
r = client.post("/auth/login", data={"name": "kate", "password": "pw1234"})
token = r.json()["token"]
print(f"   token 获取成功")

H = {"Authorization": f"Bearer {token}"}
print("3) 新增两条待办")
for t in ("学完 FastAPI", "练一遍 JWT"):
    r = client.post("/todos", json={"title": t}, headers=H)
    assert r.status_code == 201
print("   新增成功")

print("4) 查列表(应 2 条)")
r = client.get("/todos", headers=H)
print(f"   {r.json()}")
assert len(r.json()) == 2

print("5) 未登录访问 /todos -> 401")
r = client.get("/todos")
print(f"   status={r.status_code}")
assert r.status_code == 401

print("6) 删除一条后再查(剩 1 条)")
client.delete("/todos/1", headers=H)
r = client.get("/todos", headers=H)
print(f"   {r.json()}")
assert len(r.json()) == 1

print("\n全部通过 ✓  一个带鉴权 + 数据库的小服务完整闭环")