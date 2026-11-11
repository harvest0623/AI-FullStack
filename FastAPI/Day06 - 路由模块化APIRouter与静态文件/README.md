# Day06 - 路由模块化 APIRouter 与静态文件

> 接口一多，单文件就难以维护。FastAPI 提供 **`APIRouter`**：可以把接口按业务拆成
> 若干子路由（模块），再统一挂到主应用上——就像给应用装了几个功能模块。
> 本讲还用 `StaticFiles` 挂一个静态目录，服务图片/网页等资源。

## 本讲目标

1. 创建多个 `APIRouter`（如 user、order、admin），各自定义接口。
2. 用 `app.include_router(...)` 把它们挂到主应用，**前缀 + 子路由**合成完整路径。
3. 挂载一个静态文件目录。
4. 用 TestClient 验证各模块的接口是否都能访问。

## 核心概念

| 概念 | 说明 |
|------|------|
| `APIRouter()` | 一个子路由容器，可独立定义接口、前缀、标签 |
| `include_router` | 把子路由挂到主应用 |
| `prefix` | 统一路径前缀，如 `/users` |
| `tags` | 给接口分组，Swagger 文档里更好看 |
| `StaticFiles` | 挂载静态文件目录 |

## 代码结构（单文件版便于运行）

```python
from fastapi import APIRouter, FastAPI

# 用户模块
user_router = APIRouter(prefix="/users", tags=["用户"])

@user_router.get("/{uid}")          # -> 实际路径 /users/{uid}
def get_user(uid: int):
    return {"uid": uid}

# 订单模块
order_router = APIRouter(prefix="/orders", tags=["订单"])

@order_router.get("")
def list_orders():                   # -> /orders
    return [{"id": 1}]

# 主应用挂载
app = FastAPI()
app.include_router(user_router)
app.include_router(order_router)
```

## 运行

```bash
python "Code/06-routers-static.py"
```

## 你要体会的

- 项目大了就该**一个业务一个 router 文件**，主应用只负责 `include_router` 汇总。
- `prefix` 让每个模块内部不用重复写前缀，改前缀只改一处。
- 静态文件与 API 并存：`/` 外的资源用 `StaticFiles` 挂目录即可。