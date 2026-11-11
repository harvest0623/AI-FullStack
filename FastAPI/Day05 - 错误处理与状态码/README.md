# Day05 - 错误处理与状态码

> 一个可靠的 API 不仅要"成功时返回 200"，还得在**出问题时返回正确的状态码和错误信息**。
> 本讲学习 FastAPI 的两大武器：`HTTPException`（主动抛错）和 `status` 常量（语义化状态码）。

## 本讲目标

1. 用 `HTTPException(status_code, detail)` 主动抛出业务错误（如 404 找不到、400 参数错）。
2. 用 FastAPI 提供的 `status` 常量代替魔法数字（更读得懂）。
3. 了解自定义返回值状态码（`status_code=...`）。
4. 用 TestClient 验证各类错误响应。

## 核心概念

| 概念 | 说明 |
|------|------|
| `HTTPException` | 主动抛出的 HTTP 错误，含状态码 + 说明 |
| `status` 模块 | 状态码常量，如 `status.HTTP_404_NOT_FOUND` |
| `detail` | 错误描述，返回在响应体 `{"detail": "..."}` |
| `status_code=` | 声明接口成功时返回的默认状态码 |

## 主动抛错

```python
from fastapi import HTTPException, status

fake_db = {1: {"name": "键盘"}}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return fake_db[order_id]
```

此时访问不存在的订单，会得到：

```json
{"detail": "订单不存在"}
```

同时状态码是 404。

## 运行

```bash
python "Code/05-errors-status.py"
```

## 你要体会的

- `HTTPException` 让业务错误"显式发生"，而不是让接口静默返回空数据。
- 用 `status` 常量比手写 404/422 更不易出错、更可读。
- 状态码三个层级各司其职：2xx 成功、4xx 客户端错、5xx 服务端错。