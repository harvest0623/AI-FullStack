# Day01 - 认识 FastAPI 与第一个接口

> 从零上手 FastAPI。你要先理解三件事：**路由、接口装饰器、JSON 响应**，
> 然后用 TestClient 让它真正跑起来。

## 本讲目标

1. 搭建一个最小的 FastAPI 应用，定义 `GET /` 和 `GET /hello/{name}`。
2. 认识路径路由（`@app.get`）与自动 JSON 序列化。
3. 用一个脚本结束前：起一个 FastAPI 应用实例，并用 `TestClient` 发起真实 HTTP 请求验证 `status_code` 与 JSON 内容。
4. 知道脚本里那条"启动服务器"的注释如何在真实项目里用。

## 核心概念

| 概念 | 说明 |
|------|------|
| `FastAPI()` | 应用实例，构造所有路由的容器 |
| `@app.get("/path")` | 路由装饰器：声明一个 HTTP GET 接口 |
| `def` 函数 | 接口处理函数，返回值会被 FastAPI 自动转成 JSON |
| `TestClient(app)` | Starlette 提供的测试客户端，本地发请求、不占端口 |
| `response.status_code` / `.json()` | 读取响应状态码与解析后的 JSON 体 |

## 最小代码

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
def hello(name: str):
    return {"name": name, "msg": f"你好, {name}!"}
```

## 运行

```bash
python "Code/01-first-endpoint.py"
```

> 若想以真实服务器方式运行：`uvicorn 文件名:app --reload`，
> 浏览器打开 `http://127.0.0.1:8000/docs` 就能看到自动生成的 Swagger 文档。

## 你要体会的

- 一个 `return 字典` 就完成了一次 JSON API——这才是 FastAPI 的"极简"。
- 处理函数里写 `emoji 中文` 都没关系，返回的就是原样 UTF-8 字符串。
- TestClient 是学习期最顺手的"遥控器"，本模块后面的每一讲都会靠它验证。