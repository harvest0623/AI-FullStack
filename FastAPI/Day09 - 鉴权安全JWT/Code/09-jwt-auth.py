"""
Day09 练习：JWT 鉴权(自实现 HS256, 零第三方依赖)
=============================================
1) 用标准库自实现 JWT 签发/验签
2) POST /login 返回 token
3) GET /me 要求 Bearer token, 验签通过才返回用户

运行:
  python "Code/09-jwt-auth.py"
"""
import base64, hashlib, hmac, json, time
from fastapi import FastAPI, HTTPException, Header, Form, Depends
from fastapi.testclient import TestClient

# ---------- 1. 自实现 JWT(HS256) ----------
SECRET = "qwerty-secret-for-learning"     # 生产环境从环境变量读取!

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def encode_token(payload: dict, ttl: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload, exp=int(time.time()) + ttl)
    h, p = _b64(json.dumps(header).encode()), _b64(json.dumps(body).encode())
    sig = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"

def decode_token(token: str) -> dict:
    try:
        h, p, s = token.split(".")
    except ValueError:
        raise ValueError("格式错误")
    expect = _b64(hmac.new(SECRET.encode(), f"{h}.{p}".encode(),
                           hashlib.sha256).digest())
    if not hmac.compare_digest(s, expect):
        raise ValueError("签名无效")
    payload = json.loads(_unb64(p))
    if payload.get("exp", float("inf")) < time.time():
        raise ValueError("令牌已过期")
    return payload


# ---------- 2. 应用 ----------
app = FastAPI(title="JWT 鉴权")

USERS = {"kate": "pw123", "admin": "admin888"}   # 简化: 明文, 教学用

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """校验用户名密码, 成功签发 token。"""
    if USERS.get(username) == password:
        return {"token": encode_token({"sub": username}), "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="用户名或密码错误")


def require_user(authorization: str | None = Header(default=None)):
    """验签依赖: 把当前用户提取出来, 方便受保护接口直接用。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权: 缺少令牌")
    try:
        payload = decode_token(authorization.split(" ", 1)[1])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"未授权: {e}")
    return payload["sub"]


@app.get("/me")
def me(user: str = Depends(require_user)):
    """受保护接口: 只有带有效 token 才能访问。"""
    return {"user": user, "msg": "欢迎回来, 你已通过身份验证"}


client = TestClient(app)

print("1) 登录成功 -> 拿到 token")
r = client.post("/login", data={"username": "kate", "password": "pw123"})
print(f"   status={r.status_code}")
token = r.json()["token"]
print(f"   token = {token}")   # 三段的 header.payload.signature
assert "token" in r.json()

print("2) 携带有效 token 访问 /me")
r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 200 and r.json()["user"] == "kate"

print("3) 无 token -> 401")
r = client.get("/me")
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 401

print("4) 伪造 token -> 401(签名校验拦截)")
r = client.get("/me", headers={"Authorization": "Bearer fake.token.value"})
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 401

print("5) 篡改 payload -> 401(签名不一致)")
h, p, s = token.split(".")
tampered = f"{h}.{_b64(b'{\"sub\":\"admin\",\"exp\":' + b'9999999999}')}.{s}"
r = client.get("/me", headers={"Authorization": f"Bearer {tampered}"})
print(f"   status={r.status_code} body={r.json()}")
assert r.status_code == 401

print("6) 登录失败 -> 401")
r = client.post("/login", data={"username": "kate", "password": "wrong"})
print(f"   status={r.status_code}")
assert r.status_code == 401

print("\n全部通过 ✓  只要密钥不被泄露, 伪造/篡改令牌都会在验签一步被拦下")