# Day09 - 鉴权安全(JWT)

> 上回学文件上传，这次让接口"认人"。最常见的方案是 **JWT(JSON Web Token)**：
> 登录后服务器签发一个带签名的令牌，客户端每次请求带上，服务器验签即确认"你是谁"。
> 本讲用**标准库自实现**一个极简 HS256 JWT，既讲清原理，又离线可跑。

## 本讲目标

1. 用 `hmac` + `hashlib` + `base64` 自实现 JWT 的**签发**与**验签**（理解那一刻到底在做什么）。
2. 做一个 `POST /login`：校验用户名密码，成功返回 token。
3. 做一个受保护的 `/me`：要求带 token，验签通过才返回用户信息。
4. 用 TestClient 演示"无 token -> 401、坏 token -> 401、好 token -> 200"。

## JWT 长什么样

JWT 是 `Header.Payload.Signature` 三段，每段 base64：

```
Header:    {"alg":"HS256","typ":"JWT"}
Payload:   {"sub":"kate","exp":<时间戳>}
Signature: HMAC-SHA256(header + "." + payload, 密钥)
```

验签时重算签名比对，一致则令牌真实、未被篡改；同时检查过期时间。

## 自实现核心

```python
import base64, hashlib, hmac, json, time

SECRET = "超级秘密字符串"

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def encode_token(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64(json.dumps(header).encode())
    p = _b64(json.dumps(payload).encode())
    sig = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64(sig)}"

def decode_token(token: str) -> dict:
    h, p, s = token.split(".")
    expect = _b64(hmac.new(SECRET.encode(), f"{h}.{p}".encode(),
                           hashlib.sha256).digest())
    if not hmac.compare_digest(s, expect):
        raise ValueError("签名无效")                 # 被篡改/密钥不对
    payload = json.loads(base64.urlsafe_b64decode(p + "=="))
    if payload.get("exp", float("inf")) < time.time():
        raise ValueError("令牌已过期")
    return payload
```

## 受保护接口

```python
import jwt_lib   # 上面自实现的模块

@app.get("/me")
def me(authorization: str = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权: 缺少令牌")
    try:
        token = authorization.split(" ", 1)[1]
        payload = jwt_lib.decode_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"未授权: {e}")
    return {"user": payload["sub"]}
```

## 运行

```bash
python "Code/09-jwt-auth.py"
```

## 你要体会的

- JWT 的"安全"来自**签名**：只有持有密钥的服务端能签发和验证。
- 客户端不存会话、服务端无状态，审校只在"验签 + 查过期"两步。
- 把验签封装成依赖（Day04），就能一键保护任意接口——Day10 会真的这么做。
- 真实生产建议用 `python-jose` / `PyJWT` + OAuth2；这里自实现是为了让你看清黑盒。