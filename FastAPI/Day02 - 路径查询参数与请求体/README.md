# Day02 - 路径参数、查询参数与请求体

> 接口的数据从哪来？三个主要入口：**路径里**、**查询串里(?key=val)**、**请求体里**。
> 本讲用一个小而全的示例把三类参数都试一遍，并看 FastAPI 如何做类型校验。

## 本讲目标

1. 路径参数：`/items/{item_id}`，声明类型后 FastAPI 自动校验（如 `int`）。
2. 查询参数：`?q=xxx&skip=0&limit=10`，带默认值的可选参数。
3. 请求体：`POST` 时发 JSON，用 Pydantic 模型接收。
4. 用 TestClient 分别发起 GET/POST 并验证响应；同时演示**类型不正确时返回 422**。

## 核心概念

| 概念 | 说明 | 例子 |
|------|------|------|
| 路径参数 | 写在 URL 路径里，`{}` 占位 | `/items/42` |
| 查询参数 | 写在 `?` 后面，键值对 | `?q=手机&limit=5` |
| 请求体 | 需要随请求发送的数据 | POST `{"name":"键盘"}` |
| `BaseModel` | Pydantic 模型，定义请求体的字段与类型 | `class Item(BaseModel)` |
| 422 | 校验失败时 FastAPI 返回的状态码 | 传了错误类型 |

## 请求体模型

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float           # 必须是数值
    in_stock: bool = True   # 带默认值, 可不传
```

## 关键代码

```python
@app.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = None, skip: int = 0):
    # item_id 来自路径, q/skip 来自查询
    return {"item_id": item_id, "q": q, "skip": skip}

@app.post("/items", status_code=201)
def create_item(item: Item):      # item 来自请求体
    return item
```

## 运行

```bash
python "Code/02-params.py"
```

## 你要体会的

- **类型即校验**：声明 `item_id: int`，传 "abc" 直接 422，不用手写 if。
- **参数来源由写法决定**：函数里直接命名的简单类型默认是路径/查询参数；`BaseModel` 类型默认来自请求体。
- FastAPI 靠"函数签名"自动路由数据——同样是参数，位置不同来源不同。