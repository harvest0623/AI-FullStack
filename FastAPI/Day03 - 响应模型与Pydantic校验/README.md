# Day03 - 响应模型与 Pydantic 校验

> 输入用 Pydantic 校验（Day02），输出同样可以用 Pydantic 约束。本讲引入
> **响应模型 `response_model`**：它决定了"返回给客户端的数据长什么样"——
> 多传了什么会被过滤，字段类型不对会校验失败。

## 本讲目标

1. 用 `response_model=UserOut` 声明接口的**输出契约**。
2. 体验响应过滤：内部返回的字典里多余的字段（如密码）会被剔除。
3. 用字段校验器/嵌套模型保证数据合法。
4. 理解 422 何时作用于输出、何时作用于输入。

## 核心概念

| 概念 | 说明 |
|------|------|
| `response_model` | 接口返回值的类型约束，自动过滤多余字段 |
| `BaseModel` | 定义响应结构 |
| status_code | 决定成功返回的状态码 |
| 嵌套模型 | 模型里字段是另一个模型，构建层级 JSON |

## 响应过滤机制

```python
from pydantic import BaseModel

class UserIn(BaseModel):      # 输入模型 —— 数据来源
    username: str
    password: str

class UserOut(BaseModel):     # 输出模型 —— 只暴露这两项
    username: str
    phone: str

@app.post("/user", response_model=UserOut)
def create_user(u: UserIn):
    # 返回里故意带上 password, 但 response_model 会自动把它过滤掉
    return {"username": u.username, "password": u.password, "phone": "138-0000-1234"}
```

上面接口虽然内部返回了 `password`，但因为 `response_model=UserOut`，客户端不会收到密码字段。

## 运行

```bash
python "Code/03-response-model.py"
```

## 你要体会的

- 响应模型 = **安全与契约**：对外只暴露该暴露的字段，绝不把密码/内部 id 泄出去。
- 校验双向：输入是"增"，输出是"减"——输入过滤不是不要数据，而是筛掉非法；输出筛掉的是"多余"。
- 后端改内部实现（多算点东西），只要响应模型不变，前端零感知。