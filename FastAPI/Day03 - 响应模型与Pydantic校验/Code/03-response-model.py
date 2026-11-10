"""
Day03 练习：响应模型与 Pydantic 输出过滤
=====================================
用 response_model 声明输出契约, 观察多余字段(如 password)被自动过滤,
并演示嵌套模型与 List[模型] 的返回。

运行:
  python "Code/03-response-model.py"
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI(title="响应模型演示")

# ---------- 输入/输出模型 ----------
class UserIn(BaseModel):
    username: str
    password: str
    age: int = Field(ge=0, le=130)      # 0~130 岁

class UserOut(BaseModel):
    username: str
    age: int
    # 故意没有 password/email —— 输出时被过滤

class Friend(BaseModel):
    name: str

class UserWithFriends(BaseModel):
    username: str
    age: int
    friends: list[Friend]                # 嵌套模型 + 列表


# ---------- 接口 ----------
@app.post("/user", response_model=UserOut, status_code=201)
def create_user(u: UserIn):
    """返回里故意带了 password, 但 response_model 会过滤掉它。"""
    return {"username": u.username, "password": u.password, "age": u.age}

@app.get("/users/{username}", response_model=UserWithFriends)
def get_user_with_friends(username: str):
    """返回嵌套模型 + 列表字段。"""
    return {
        "username": username,
        "age": 25,
        "friends": [Friend(name="甲"), Friend(name="乙")],
        # response_model 里没有该字段, 会自动丢弃
        "secret_internal": "不该暴露",
    }


client = TestClient(app)

print("1) 响应模型过滤: POST /user")
payload = {"username": "kate", "password": "顶秘密", "age": 21}
r = client.post("/user", json=payload)
print(f"   status={r.status_code}  body={r.json()}")
assert r.status_code == 201
assert "password" not in r.json(), "password 应被过滤"
print("   => password 已被过滤, 只暴露 username/age")

print("2) 校验年龄: age=200 -> 422")
r = client.post("/user", json={"username": "x", "password": "p", "age": 200})
print(f"   status={r.status_code}")
assert r.status_code == 422

print("3) 嵌套模型 + 多余字段过滤: GET /users/kate")
r = client.get("/users/kate")
print(f"   status={r.status_code}  body={r.json()}")
assert "secret_internal" not in r.json()
assert r.json()["friends"][0]["name"] == "甲"

print("\n全部通过 ✓  要点: response_model 既格式化输出, 又防止泄露多余字段")