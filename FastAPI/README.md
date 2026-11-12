# FastAPI 模块 —— 从第一个接口到完整 Web 服务

> 本模块用 **10 天**，从零到一掌握 FastAPI。FastAPI 是当下最受欢迎的 Python Web
> 框架之一：**极简、高性能、自带类型校验、自动生成 OpenAPI 文档**，是现代 AI
> 项目（作为模型服务、后端 API）的标配。

## 为什么学 FastAPI

- **快**：基于 Starlette + Pydantic，异步高性能，自动类型校验。
- **自动文档**：写好接口就有 Swagger /docs，联调省心。
- **类型即契约**：用 Python 类型注解定义请求体/响应模型，前后端天然对齐。
- **和 Pydantic/AI 无缝**：上一模块学的 Pydantic 就是 FastAPI 的校验核心。

## 环境说明

本模块脚本依赖 `fastapi`、`uvicorn`、`pydantic`、`httpx`（已安装，版本见下）。
不再像前面模块用模拟框架，而是**真实运行 FastAPI**，并使用 `TestClient`
（内部走 httpx）发起请求验证，无需单独起服务。

```bash
fastapi==0.136.3   uvicorn==0.30.6   pydantic==2.13.5   httpx==0.27.2
```

每个 Day 的目录结构：

```
DayXX - 主题/
  README.md       讲解与要点
  Code/
    01-xxx.py     可直接运行的脚本 (TestClient 自动请求验证)
    ...           辅助文件(数据库/路由模块等)
```

## 10 天路线

| 天 | 主题 | 你会做出来 |
|----|------|-----------|
| 01 | 认识 FastAPI 与第一个接口 | `GET /` / `GET /hello` 返回 JSON |
| 02 | 路径/查询参数与请求体 | 支持动态路径、查询串、POST JSON |
| 03 | 响应模型与 Pydantic 校验 | 输出模型、字段校验、422 错误 |
| 04 | 依赖注入 Dependency | 复用逻辑、公共参数、`Depends` |
| 05 | 错误处理与状态码 | HTTPException、自定义响应、状态码测试 |
| 06 | 路由模块化 APIRouter | 把接口拆成分组模块 + 静态文件 |
| 07 | 数据库集成 SQLite | CRUD 全流程、ORM 风格访问 |
| 08 | 文件上传与表单 | UploadFile、Multipart、表单 |
| 09 | 鉴权安全 JWT | 登录发令牌、受保护接口 |
| 10 | 实战整合 + 测试 | 把前九讲拼成一个完整小应用 |

## 怎么开始

```bash
# 推荐从 Day01 逐个阅读, 再看对应脚本并运行
python "Day01 - 认识 FastAPI 与第一个接口/Code/01-first-endpoint.py"
```

## 速查

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/items/{item_id}")          # 路径参数
def read_item(item_id: int, q: str | None = None):   # 查询参数
    return {"item_id": item_id, "q": q}

@app.post("/items", status_code=201)  # 返回 201
def create_item(item: Item):
    return {"name": item.name, "price": item.price}
```

启动开发服务器：`uvicorn 文件名:app --reload`，打开 `http://127.0.0.1:8000/docs`。