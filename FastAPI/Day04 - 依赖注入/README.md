# Day04 - 依赖注入 Dependency

> 多个接口常需要**相同的公共逻辑**：查数据库、取当前用户、验证 token、分页参数……
> FastAPI 用 **依赖注入（`Depends`）** 把这类横切逻辑抽出来复用，接口只声明"我需要的组件"，
> FastAPI 自动解析并注入。

## 本讲目标

1. 写一个普通函数当依赖，用 `Depends()` 注入到接口函数。
2. 依赖可以返回数据，接口直接使用；依赖里也能做校验/分支。
3. 用带 `yield` 的依赖演示 **资源生命周期**（如开/关连接）。
4. 观察依赖如何被自动调用、参数如何传递。

## 核心概念

| 概念 | 说明 |
|------|------|
| `Depends(func)` | 声明依赖：调用 func 得到返回值注入接口 |
| 依赖函数 | 任意可调用对象，本身也可有参数（构成依赖树） |
| `yield` 依赖 | 在请求前执行 yield 前代码，请求结束执行之后的清理 |
| 复用 | 同一依赖被多个接口使用时只写一次 |

## 最简单的注入

```python
from fastapi import Depends

def pagination(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/items")
def list_items(p: dict = Depends(pagination)):   # p 自动 = pagination() 的结果
    return {"param": p}
```

## 依赖里做校验

```python
def require_token(authorization: str | None = None):
    if not authorization or not authorization.startswith("Bearer "):
        return {"user": "anonymous"}          # 简化: 缺 token 给个匿名
    return {"user": authorization.split(" ")[1]}

@app.get("/me")
def who_am_i(u: dict = Depends(require_token)):
    return u
```

## 运行

```bash
python "Code/04-dependency.py"
```

## 你要体会的

- 依赖就是普通函数，参数仍靠 FastAPI 自动从请求里解析——**依赖也能层层套娃**。
- 把"公共的、跨接口的"搬到依赖里，接口函数变干净、可测试。
- `yield` 依赖非常适合"用完即关"的资源（数据库连接、文件句柄）。