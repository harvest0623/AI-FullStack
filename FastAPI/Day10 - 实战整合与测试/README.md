# Day10 - 实战整合 + 测试

> 收官之讲！把前九讲学的零件全部拼成一个**小而完整的"待办 API 服务"**：
> 注册登录(JWT)、增删改查(SQLite)、响应模型、依赖注入、错误处理、TestClient 端到端验证。
> 一个能跑通的整体，才是真正的"我能用 FastAPI 做东西"。

## 本讲整合了哪些 Day

| 用到 | 来自 |
|------|------|
| 路径/查询参数、请求体 | Day02 |
| Pydantic 响应模型与校验 | Day03 |
| 依赖注入(验签/连接) | Day04 |
| 错误处理与状态码 | Day05 |
| APIRouter 模块化(论点) | Day06 |
| SQLite 持久化 | Day07 |
| JWT 鉴权(自实现 HS256) | Day09 |

## 应用结构

```
app = FastAPI()
├─ POST /auth/register   注册(存用户, 密码打码)
├─ POST /auth/login      登录 -> 返回 JWT
├─ GET  /todos           受保护, 查当前用户的待办
├─ POST /todos           受保护, 增一条
├─ PUT  /todos/{id}      受保护, 改一条
└─ DELETE /todos/{id}    受保护, 删一条(JWT 鉴权保护)
```

**鉴权流程**：注册→登录得 token→带 `Authorization: Bearer <token>` 操作自己的待办。
`require_user` 依赖负责验签（Day04 + Day09），SQLite 依赖负责连接（Day04 + Day07）。

## 运行

```bash
python "Code/10-app.py"     # 端到端演示 + 断言
```

设 `ALLOW_EXP`=0 之类可实时看过期…… 这里直接跑即演示成功路径 + 未登录 401 路径。

## 你要体会的

- FastAPI 项目 = **规格(模型) + 逻辑(接口) + 依赖(复用) + 数据(库)** 的拼装。
- 一个端到端脚本 10 秒跑通，比十篇文档都更有说服力。
- 从这里出发，接上 ORM(SQLAlchemy)、超时/限流、CORS、部署(uvicorn/gunicorn)就能上生产。
- 这也是你从"单点知识"走向"完整 Web 服务"的临门一脚。