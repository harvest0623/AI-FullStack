# Day12 - RESTful API 设计与实现

> 本篇聚焦后端 API 设计的“通用语言”——**REST**。你将在 Day10/Day11 的 Express 基础上，从“能写出接口”升级到“能设计出规范、可演进、团队协作友好的接口”。我们会讲透 REST 的架构原则、HTTP 方法语义、幂等性、状态码、URI 设计规范与版本化策略，并亲手用 Express 实现一个符合工业惯例的 `/api/v1/articles` 资源，包含统一响应格式、分页、错误处理。这是后续接入数据库、鉴权、AI 接口编排的工程地基。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识讲解](#二理论知识讲解)
  - [2.1 什么是 REST](#21-什么是-rest)
  - [2.2 REST 架构风格核心原则](#22-rest-架构风格核心原则)
  - [2.3 资源（Resource）与 URI 设计](#23-资源resource与-uri-设计)
  - [2.4 HTTP 方法语义](#24-http-方法语义)
  - [2.5 幂等性（Idempotency）详解](#25-幂等性idempotency详解)
  - [2.6 状态码正确使用](#26-状态码正确使用)
  - [2.7 URI 设计规范](#27-uri-设计规范)
  - [2.8 版本化策略](#28-版本化策略)
- [三、RESTful API 设计规范](#三restful-api-设计规范)
  - [3.1 资源 URI 示例表](#31-资源-uri-示例表)
  - [3.2 方法映射 CRUD](#32-方法映射-crud)
  - [3.3 状态码选择决策树](#33-状态码选择决策树)
- [四、请求与响应规范](#四请求与响应规范)
  - [4.1 统一响应格式](#41-统一响应格式)
  - [4.2 分页响应](#42-分页响应)
  - [4.3 错误响应格式](#43-错误响应格式)
  - [4.4 HATEOAS 简述](#44-hateoas-简述)
- [五、实现一个完整 RESTful CRUD](#五实现一个完整-restful-crud)
- [六、常见反模式](#六常见反模式)
- [七、API 文档](#七api-文档)
- [八、关键知识点总结](#八关键知识点总结)
- [九、实战练习](#九实战练习)

---

## 一、学习目标

完成本篇学习后，你应当能够：

1. 准确说出 REST 的五大核心原则，并解释“无状态”与“统一接口”对工程的实际意义。
2. 区分 REST 的“架构风格”与 HTTP 协议的关系——REST 不等于 HTTP，但 HTTP 是承载 REST 最常见的协议。
3. 为任意业务场景设计出符合规范的资源 URI（名词复数、层级清晰、用 query 做过滤分页）。
4. 牢记 GET / POST / PUT / PATCH / DELETE 的语义，并能判断每个方法是否“安全”与“幂等”。
5. 用“幂等性”思维解释为什么 PUT/DELETE 天然防重复提交，而 POST 需要 token 兜底。
6. 为不同场景选择正确的 HTTP 状态码（200/201/204/400/401/403/404/409/422/500）。
7. 设计统一的响应格式（`{code, message, data}`）与分页响应（`{data, total, page, pageSize}`）。
8. 用 Express + `express.Router` 实现一个完整、规范、带分页与错误处理的 `/api/v1/articles` CRUD。
9. 识别并规避常见 REST 反模式（URI 动词、GET 写操作、状态码乱用、响应结构不一致）。
10. 了解 Swagger/OpenAPI 的价值与“用注释生成文档”的思路，为后续 API 文档化 skill 铺垫。

---

## 二、理论知识讲解

### 2.1 什么是 REST

**REST**（Representational State Transfer，表述性状态转移）由 Roy Fielding 在 2000 年的博士论文中提出。它不是协议，也不是框架，而是一种**分布式超媒体系统的架构风格（Architectural Style）**。

拆解这个名字：

- **Representational（表述性）**：资源以某种表现形式（JSON、XML、HTML）在网络上传输。我们传的不是“资源本身”，而是资源的“表述”。
- **State Transfer（状态转移）**：客户端通过操作资源的表述，让资源的状态发生改变（创建、更新、删除）。

一句话定位：

> REST 是一套“用 HTTP 的特性来表达业务操作”的设计约定——把后端能力抽象成一组**资源**，用 **HTTP 方法**表达对资源的动作，用 **状态码**表达结果。

需要澄清一个常见误解：

| 概念 | 关系 |
|------|------|
| REST | 架构风格，与协议无关 |
| HTTP | 实现 REST 最常见的协议，但 REST 也能基于其它协议 |
| RESTful API | “符合 REST 风格的 HTTP API”的口语化说法 |

> 现实中多数团队说的“RESTful”，其实是“**贴近 REST 思想的 HTTP API**”，并不一定 100% 严格遵守 Fielding 论文（尤其是 HATEOAS）。这不影响它的工程价值——抓住“资源 + 方法 + 状态码”三件套，就能写出远胜 RPC 风格接口的 API。

### 2.2 REST 架构风格核心原则

REST 定义了六大约束（constraint），满足这些约束的系统才称得上 RESTful。其中五个是必选项，一个是可选项。

#### ① 客户端-服务端分离（Client-Server Separation）

客户端与服务端各司其职、独立演进。

- 客户端专注“用户界面与交互”，不关心数据怎么存储。
- 服务端专注“数据与业务”，不关心界面怎么渲染。
- 两者通过统一接口通信，解耦后客户端可换（Web/App/小程序），服务端可扩（分库分表）。

**工程意义**：前后端分离的技术基石。前端工程师转全栈，第一件事就是理解“服务端只负责吐数据，不负责渲染页面”。

#### ② 无状态（Stateless）

服务端**不保存客户端的会话状态**。每个请求必须自包含所有必要信息（认证凭据、参数等），服务端处理完即“忘记”。

- ❌ 错误做法：服务端在内存里记着“当前用户在第 3 页”，下次请求自动翻第 4 页。
- ✅ 正确做法：客户端每次都带上 `?page=4`，服务端无脑返回第 4 页。

**工程意义**：

- 可水平扩展：任意一台服务器都能处理任意请求（因为没有“粘性会话”）。
- 可观测性好：单看一个请求就能复现问题，不用还原会话上下文。
- 代价：每次请求要重复传认证信息（如 JWT），略增带宽。

> 注意：“无状态”指**协议层无状态**，不等于“应用无状态”。服务端当然可以读写数据库，只是不在内存里持有客户端的会话状态。登录态通常用 JWT 或 Cookie+Session（Session 存在共享存储如 Redis 中）实现。

#### ③ 统一接口（Uniform Interface）

这是 REST 最核心的约束，它进一步细化为四个子约束：

| 子约束 | 含义 | 落地表现 |
|--------|------|----------|
| **资源标识** | 每个资源有唯一 URI | `/articles/1`、`/users/42` |
| **表述操作** | 客户端通过表述（JSON）操作资源，服务端返回表述 | POST/PUT 带 JSON body，GET 返回 JSON |
| **自描述消息** | 每个消息自带足够信息说明如何处理 | `Content-Type: application/json` 告诉服务端怎么解析 |
| **超媒体驱动（HATEOAS）** | 响应里带可执行的后续链接 | 见 4.4 节 |

**工程意义**：统一接口让客户端无需学习每个服务的“私有协议”，只要懂 HTTP 就能用。这是 REST 能成为“行业通用语言”的根本原因。

#### ④ 分层系统（Layered System）

客户端无法、也无需知道它直接连接的是最终服务器，还是中间的代理、网关、负载均衡。

```
客户端 ──► CDN ──► 负载均衡 ──► API 网关 ──► 业务服务 ──► 数据库
```

每一层只与相邻层交互，可独立替换。比如在网关层加鉴权、限流，业务服务无感知。

**工程意义**：允许架构演进——从单体到微服务，从直连到加网关，客户端代码不用改。

#### ⑤ 可缓存（Cacheable）

响应必须明确标识自己是否可缓存、缓存多久，让客户端和中间代理可以复用响应，减少往返。

- 通过 `Cache-Control`、`ETag`、`Last-Modified` 等响应头控制。
- `GET` 通常是可缓存的，`POST/PUT/DELETE` 默认不可缓存。

**工程意义**：缓存是性能优化的利器。设计 API 时要主动思考“这个响应能不能缓存”。

#### ⑥ 按需代码（Code on Demand，可选）

服务端可临时向客户端下发可执行代码（如 JS），客户端可选择执行。这是**唯一可选**约束，现代 RESTful API 几乎不用，了解即可。

> **小结**：六大约束中，前五个是 REST 的硬性要求。现实中“RESTful”常被宽泛使用，但只要抓住“**资源 + 统一接口 + 无状态**”这三个灵魂，就抓住了 REST 的本质。

### 2.3 资源（Resource）与 URI 设计

REST 的世界观里，万物皆**资源（Resource）**。资源是任何可以被命名的事物：一篇文章、一个用户、一批订单、一张图片。

资源的**标识符**就是 URI（统一资源标识符）。URL 是 URI 的一种（带定位能力），日常口语里常混用。

设计资源 URI 的核心心法：

> **URI 标识“是什么”（名词），HTTP 方法表达“做什么”（动词）。**

对比两种风格：

| 风格 | 示例 | 评价 |
|------|------|------|
| RPC 风格 | `POST /getUser?id=1`、`POST /createUser` | URI 里塞动词，方法只用 POST |
| REST 风格 | `GET /users/1`、`POST /users` | URI 是名词，方法表达动作 |

资源之间的层级关系用路径嵌套表达：

```
/users/42/articles           → 用户 42 的文章集合
/users/42/articles/7         → 用户 42 的 id=7 文章
/articles/7/comments          → 文章 7 的评论集合
```

> 层级不要太深，一般 2-3 层为宜。过深会导致 URI 冗长且难以缓存。如果一个资源有独立身份（如评论本身有 id），可以直接用 `/comments/:id` 而非挂在文章下。

### 2.4 HTTP 方法语义

HTTP 方法（也叫动词）表达对资源的操作。理解它们的**安全（Safe）**与**幂等（Idempotent）**属性是设计 API 的基本功。

| 方法 | 语义 | 安全 | 幂等 | 典型用途 |
|------|------|------|------|----------|
| **GET** | 读取资源 | ✅ 是 | ✅ 是 | 查询列表、详情 |
| **POST** | 创建资源 / 触发动作 | ❌ 否 | ❌ 否 | 新建、提交表单 |
| **PUT** | 全量替换资源 | ❌ 否 | ✅ 是 | 整体更新（需提供全部字段） |
| **PATCH** | 部分修改资源 | ❌ 否 | ❌ 否* | 修改个别字段 |
| **DELETE** | 删除资源 | ❌ 否 | ✅ 是 | 删除 |

\* PATCH 的幂等性存在争议：若 PATCH 操作是“设置为某值”则幂等，若是“字段值 +1”这种相对操作则不幂等。实践中按“不保证幂等”对待更稳妥。

#### 两个关键概念

- **安全（Safe）**：方法不改变服务端状态。GET 必须“只读”，调用 100 次和 0 次对数据的影响一样。
- **幂等（Idempotent）**：方法调用 N 次和调用 1 次的效果相同。与“安全”的区别在于——幂等的方法**可以改变状态**，只是重复执行不再产生新变化。

#### 各方法的细节

**GET**——查询专用：

```bash
GET /articles           # 列表
GET /articles/1         # 详情
GET /articles?author=A  # 过滤
```

- 永远不要用 GET 修改数据（违反“安全”）。
- 参数通过 query string 传递，不通过 body（虽然 HTTP 允许 GET 带 body，但被多数实现拒绝）。

**POST**——创建 / 非幂等动作：

```bash
POST /articles
# body: { "title": "...", "content": "..." }
# 返回 201 + 新资源
```

- 每次 POST 都会创建一个新资源，所以不幂等。
- 也用于“无法用幂等方法表达的动作”，如 `POST /orders/1/cancel`（取消订单是个状态机动作，不是 CRUD）。

**PUT**——全量替换：

```bash
PUT /articles/1
# body: { "title": "新标题", "content": "新内容", "author": "...", "tags": [...] }
# 用 body 整体替换 id=1 的资源
```

- 幂等：用同一份 body 连续 PUT 10 次，结果和 PUT 1 次一样（都是“替换成这份内容”）。
- 客户端必须提供资源的**全部字段**；未提供的字段会被置空/默认值（这是 PUT 与 PATCH 的核心区别）。

**PATCH**——部分更新：

```bash
PATCH /articles/1
# body: { "title": "只改标题" }
# 只修改 title，其它字段保持不变
```

- 设计为“只传要改的字段”，未传的字段不动。
- 实践中 PATCH 最常被滥用成“半个 PUT”。严格规范应约定一种 patch 格式（如 JSON Patch / Merge Patch）。

**DELETE**——删除：

```bash
DELETE /articles/1
# 返回 204 No Content
```

- 幂等：删一次和删十次，资源最终都是“不存在”。
- 第二次删除已不存在的资源，规范上应返回 404 还是 204 存争议——实践中常见做法是第一次返回 204，重复删除返回 404。

### 2.5 幂等性（Idempotency）详解

幂等性是分布式系统的“防重复”利器，理解它能解决一类高频工程问题。

#### 定义

> 一个方法如果**调用一次与调用多次产生的副作用完全相同**，则称它是幂等的。

注意是“副作用”相同，不是“返回值”相同。比如：

- `GET /articles/1` 调用 10 次，返回值都一样（只读，无副作用）→ 安全且幂等。
- `DELETE /articles/1` 第一次返回 204，第二次可能返回 404——但副作用（文章 1 被删除）只发生一次 → 幂等但不安全。
- `POST /articles` 调用 10 次，创建 10 篇相同文章 → 不幂等。

#### 为什么幂等性重要

网络不可靠是分布式第一定律。客户端发出请求后，可能发生：

```
客户端 ──请求──► 服务端   ──► 处理成功
   ▲                  │
   │  超时/丢包        │
   └── 没收到响应 ──────┘
   ──► 客户端重试 ──► ？
```

如果方法**幂等**（PUT/DELETE），客户端可以放心重试，不会造成重复操作。

如果方法**不幂等**（POST），重试会导致重复创建。常见解法：

| 场景 | 幂等方法 | 不幂等方法 |
|------|----------|-----------|
| 网络超时 | 直接重试 | 需要**幂等键**（Idempotency-Key）兜底 |
| 前端按钮连点 | 自然防重 | 需前端禁用按钮 + 后端去重 |

#### 幂等键（Idempotency-Key）示例

对 POST 这种本不幂等的方法，通过客户端传入唯一键让服务端“手动”实现幂等：

```bash
POST /payments
Idempotency-Key: 7c8d2f1a-9b3e-4f6a-8d2c-1e5f7a9b3d12
Content-Type: application/json

{ "amount": 100, "to": "alice" }
```

服务端处理时：

1. 用 `Idempotency-Key` 查缓存/数据库。
2. 若已存在 → 直接返回上次的结果（不重复扣款）。
3. 若不存在 → 执行业务，存结果，返回。

> 支付宝、微信支付、Stripe 都用这套机制保证“点一次和点十次扣款金额一样”。这是前端转全栈后必须建立的分布式认知。

#### 幂等性速查图

```
        ┌─ 不改变状态 ──► 安全
GET  ───┤
        └─ 调用N次=调用1次 ──► 幂等

POST ───► 每次创建新资源 ──► 不安全 + 不幂等

PUT  ───► 全量替换，重复执行结果不变 ──► 不安全 + 幂等

DELETE──► 删除，重复执行结果不变 ──► 不安全 + 幂等

PATCH ───► 视实现而定，默认按“不幂等”处理
```

### 2.6 状态码正确使用

HTTP 状态码是服务端向客户端表达处理结果的“标准语言”。用对状态码，客户端就能用统一逻辑处理响应；用错，前端要写一堆 `if` 特判。

状态码按首位数字分五类：

| 分类 | 含义 | 典型 |
|------|------|------|
| 1xx | 信息性 | 100 Continue（少用） |
| 2xx | 成功 | 200、201、204 |
| 3xx | 重定向 | 301、302、304 |
| 4xx | 客户端错误 | 400、401、403、404、409、422 |
| 5xx | 服务端错误 | 500、502、503 |

#### 本篇重点掌握的状态码

| 码 | 名称 | 何时用 | 示例 |
|----|------|--------|------|
| **200** | OK | 请求成功，返回数据 | `GET /articles` 返回列表 |
| **201** | Created | 资源创建成功 | `POST /articles` 创建后返回新资源 |
| **204** | No Content | 成功但无内容返回 | `DELETE /articles/1` 删除后 |
| **400** | Bad Request | 请求语法/格式错误 | JSON 格式错、缺必填 query |
| **401** | Unauthorized | 未认证（没登录） | 缺少或无效的 token |
| **403** | Forbidden | 已认证但无权限 | 普通用户访问管理员接口 |
| **404** | Not Found | 资源不存在 | `GET /articles/999` |
| **409** | Conflict | 资源冲突 | 注册已存在的用户名 |
| **422** | Unprocessable Entity | 格式对但语义错 | 字段类型对但值非法（校验失败） |
| **500** | Internal Server Error | 服务端内部错误 | 代码异常、数据库挂了 |

#### 401 vs 403 的区别（高频面试题）

- **401**：你是“谁”都不清楚（没登录 / token 失效）→ “请先证明你的身份”。
- **403**：我知道你是“谁”，但你没权限做这件事（已登录但角色不够）→ “你不行”。

#### 400 vs 422 的区别

- **400**：请求“语法/格式”层面就错了——JSON 解析失败、必填字段缺失。
- **422**：请求格式没问题，但“业务语义”通不过——`age: -5`（类型对、值非法）、邮箱格式对但已被占用。

> 有些团队把所有“客户端错误”统一用 400，把细节放进响应体的 `message`。这能简化前端处理，但牺牲了 HTTP 语义。本篇教学示例区分使用，工程中可按团队约定取舍。

#### 状态码使用原则

1. **优先用标准码，不要自创**。HTTP 状态码是协议层约定，自定义 460/470 会让客户端困惑。
2. **2xx 只在真的成功时用**。逻辑失败（如校验不通过）别返回 200 + `{"error": "..."}`，这会让前端无法靠状态码分流。
3. **4xx 是客户端的锅，5xx 是服务端的锅**。让前端能根据码判断“要不要重试”“要不要提示用户”。
4. **不要把所有错误都塞进 500**。500 意味着“服务端出 bug 了”，会触发告警；参数校验失败用 422 更合适。

### 2.7 URI 设计规范

规范的 URI 是 RESTful 的第一观感。以下是从实践中提炼的规则。

#### 规则一：用名词复数

| ❌ 反例 | ✅ 正例 |
|---------|---------|
| `/getUser` | `/users` |
| `/article/1` | `/articles/1` |
| `/listOrders` | `/orders` |

- 统一用复数，避免“单数表详情、复数表列表”的混乱。
- 一个 URI `GET /articles/1` 拿单条，`GET /articles` 拿列表，靠路径区分，不靠单复数。

#### 规则二：层级表达从属关系

```
/users/42/articles        # 用户 42 的文章
/articles/7/comments      # 文章 7 的评论
```

- 层级反映资源间的包含/从属关系。
- 但别过度嵌套，2-3 层即可。

#### 规则三：用 query 做过滤、分页、排序

URI 路径定位“资源”，query 表达“怎么筛”。

```
GET /articles?author=Alice              # 过滤
GET /articles?page=2&pageSize=10        # 分页
GET /articles?sort=createdAt:desc       # 排序
GET /articles?keyword=REST&tag=node     # 多条件组合
```

不要把过滤塞进路径：

| ❌ 反例 | ✅ 正例 |
|---------|---------|
| `/articles/byAuthor/Alice` | `/articles?author=Alice` |
| `/articles/page/2` | `/articles?page=2` |

#### 规则四：避免动词

动作由 HTTP 方法承担，URI 不该再带动词。

| ❌ 反例 | ✅ 正例 |
|---------|---------|
| `POST /createArticle` | `POST /articles` |
| `POST /deleteArticle/1` | `DELETE /articles/1` |
| `GET /searchArticles?kw=x` | `GET /articles?keyword=x` |

**例外**：有些操作无法用 CRUD 动词表达（如“取消订单”“发布文章”），可用“动词子资源”：

```
POST /orders/1/cancel      # 取消订单（动作）
POST /articles/1/publish   # 发布文章（动作）
```

这是一种务实的妥协，优于强行套用 PUT/DELETE。

#### 规则五：用连字符分词，全小写

| ❌ 反例 | ✅ 正例 |
|---------|---------|
| `/userProfiles` | `/user-profiles` |
| `/User_Profiles` | `/user-profiles` |

- URI 路径全小写，用 `-`（连字符）分词。
- 不要用下划线 `_`，不要用驼峰。

#### 规则六：资源 id 与 slug

```
GET /articles/1                # 用数字 id
GET /articles/how-to-use-rest  # 用 slug（人类可读）
```

两者皆可，数字 id 更稳定，slug 更友好。可二选一或都支持。

### 2.8 版本化策略

API 一旦上线就会演进：加字段、改行为、删接口。版本化让“老客户端继续用旧版，新客户端用新版”成为可能。常见三种策略：

#### ① URI 版本（最常用）

```
/api/v1/articles
/api/v2/articles
```

- **优点**：直观，一眼看出版本；浏览器、curl 直接能测；缓存友好（URI 不同）。
- **缺点**：URI 里掺入了“版本”这个非资源信息，理论上不纯粹。
- **现状**：工业界绝大多数项目用这种，GitHub、Twitter、Stripe 都如此。

#### ② Header 版本

```
GET /articles
Accept: application/vnd.myapi.v2+json
```

- **优点**：URI 保持纯净，只有资源本身。
- **缺点**：不直观，调试困难（要设 header）；浏览器难直接访问。
- **适合**：对“URI 纯洁性”有洁癖的团队，或内部 API。

#### ③ 查询参数版本

```
GET /articles?version=2
```

- **优点**：简单，不改 URI 结构。
- **缺点**：版本信息混进业务参数；容易被缓存忽略。
- **现状**：用得较少，少数老系统在用。

#### 三者对比

| 策略 | 示例 | 直观性 | 纯粹性 | 采用率 |
|------|------|--------|--------|--------|
| URI 版本 | `/api/v1/articles` | ⭐⭐⭐ | ⭐⭐ | 极高 |
| Header 版本 | `Accept: ...v2+json` | ⭐ | ⭐⭐⭐ | 中 |
| 查询参数 | `?version=2` | ⭐⭐ | ⭐ | 低 |

> 本篇采用 **URI 版本**（`/api/v1/articles`），这是最务实、团队协作最友好的选择。版本号从 `v1` 开始，做了不兼容改动才升 `v2`，兼容性改动（加字段）不必升版本。

---

## 三、RESTful API 设计规范

### 3.1 资源 URI 示例表

以“文章系统”为例，展示一组规范的资源 URI：

| 资源 | URI | 说明 |
|------|-----|------|
| 文章集合 | `/api/v1/articles` | 所有文章 |
| 单篇文章 | `/api/v1/articles/1` | id=1 的文章 |
| 文章评论 | `/api/v1/articles/1/comments` | 文章 1 的评论 |
| 单条评论 | `/api/v1/articles/1/comments/5` | 文章 1 的 id=5 评论 |
| 作者信息 | `/api/v1/users/42` | id=42 的作者 |
| 当前用户 | `/api/v1/users/me` | “me”是约定俗成的别名 |
| 文章标签 | `/api/v1/articles/1/tags` | 文章 1 的标签集合 |

### 3.2 方法映射 CRUD

CRUD（Create / Read / Update / Delete）与 HTTP 方法的映射是 REST 的核心约定：

| CRUD 操作 | HTTP 方法 | URI | 请求体 | 成功状态码 | 幂等 |
|-----------|-----------|-----|--------|-----------|------|
| Create（创建） | POST | `/articles` | ✅ 资源数据 | 201 | 否 |
| Read 列表（查询） | GET | `/articles` | ❌ | 200 | 是 |
| Read 详情（查询） | GET | `/articles/:id` | ❌ | 200 | 是 |
| Update 全量（更新） | PUT | `/articles/:id` | ✅ 全部字段 | 200 | 是 |
| Update 部分（更新） | PATCH | `/articles/:id` | ✅ 部分字段 | 200 | 否 |
| Delete（删除） | DELETE | `/articles/:id` | ❌ | 204 | 是 |

记忆口诀：

> **POST 建新家，GET 看一看，PUT 整个换，PATCH 补一补，DELETE 送走它。**

### 3.3 状态码选择决策树

面对一个请求，按以下决策树选择状态码：

```
请求处理完毕了吗？
│
├─ 否，服务端代码崩了 ───────────────────► 500
│
├─ 否，服务暂时不可用 ───────────────────► 503
│
└─ 是，处理完成了
    │
    ├─ 操作类型是创建？
    │   ├─ 是，创建成功 ──────────────► 201
    │   └─ 否
    │
    ├─ 操作类型是删除？
    │   ├─ 是，删除成功（无内容返回）──► 204
    │   └─ 否
    │
    ├─ 请求有数据返回？
    │   ├─ 是 ──────────────────────► 200
    │   └─ 否（如 PUT 后无需返回）────► 204
    │
    └─ 请求失败？
        │
        ├─ 没登录 / token 无效 ──────► 401
        ├─ 登录了但没权限 ──────────► 403
        ├─ 资源不存在 ──────────────► 404
        ├─ 资源冲突（重复创建）──────► 409
        ├─ 请求格式错误（JSON 坏了）──► 400
        ├─ 字段校验失败（值非法）────► 422
        └─ 其它客户端错误 ──────────► 400
```

---

## 四、请求与响应规范

### 4.1 统一响应格式

工业界普遍采用“统一响应壳”，让所有接口返回结构一致，前端只需写一套解析逻辑：

```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "id": 1,
    "title": "RESTful API 设计"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 业务状态码。`0` 表示成功，非 `0` 表示业务错误（可与 HTTP 状态码配合） |
| `message` | string | 人类可读的提示信息，成功时给“操作成功”，失败时给具体原因 |
| `data` | any | 业务数据。列表、对象、null 皆可 |

> 为什么 HTTP 状态码 + 业务 code 双重存在？HTTP 状态码表达“传输/协议层”结果，业务 code 表达“业务层”结果。比如 `HTTP 200` 但 `code: 1001` 表示“请求到了，但业务规则不通过”。也有团队只用 HTTP 状态码，把业务错误映射到 4xx——两种流派都合理，关键是**全项目统一**。

本篇示例约定：HTTP 状态码与业务 code 同时使用，成功时 `code: 0`，失败时 `code` 取一个四位业务错误码（如 `4040` 表示资源不存在）。

### 4.2 分页响应

列表接口几乎都要分页。统一分页结构让前端能复用分页组件：

```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "list": [ { "id": 1 }, { "id": 2 } ],
    "total": 27,
    "page": 1,
    "pageSize": 10,
    "totalPages": 3
  }
}
```

| 字段 | 说明 |
|------|------|
| `list` | 当前页的数据数组 |
| `total` | 符合条件的总记录数 |
| `page` | 当前页码（从 1 开始） |
| `pageSize` | 每页条数 |
| `totalPages` | 总页数（由 `total / pageSize` 向上取整） |

请求侧的分页参数约定：

```
GET /api/v1/articles?page=2&pageSize=10
```

边界处理要点：

- `page` 最小为 1，非法值（0、负数、非数字）回退到 1。
- `pageSize` 给一个上限（如 100），防止客户端传 `pageSize=100000` 拖垮服务。
- `page` 超出总页数时，返回空 `list` 而非报错。

### 4.3 错误响应格式

错误也要统一结构，前端靠 `code` 和 `message` 渲染提示：

```json
{
  "code": 4040,
  "message": "文章 id=999 不存在",
  "data": null
}
```

进阶做法可附加 `errors` 字段，给出字段级校验错误（适合表单提交场景）：

```json
{
  "code": 4220,
  "message": "参数校验失败",
  "data": null,
  "errors": [
    { "field": "title", "message": "title 不能为空" },
    { "field": "email", "message": "email 格式不正确" }
  ]
}
```

> 本篇示例为简洁起见使用三字段结构，`errors` 字段可在实战练习中扩展。

### 4.4 HATEOAS 简述

**HATEOAS**（Hypermedia As The Engine Of Application State，超媒体作为应用状态的引擎）是 REST“统一接口”约束的最后一个子约束，也是现实中**最常被省略**的一个。

它的思想是：响应里不仅返回数据，还返回**客户端接下来可以执行的操作链接**，让客户端“跟着链接走”，而不必硬编码 URL。

示例——查询文章后，响应里带相关链接：

```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "id": 1,
    "title": "RESTful API 设计",
    "_links": {
      "self":   { "href": "/api/v1/articles/1", "method": "GET" },
      "update": { "href": "/api/v1/articles/1", "method": "PUT" },
      "delete": { "href": "/api/v1/articles/1", "method": "DELETE" },
      "comments": { "href": "/api/v1/articles/1/comments", "method": "GET" }
    }
  }
}
```

- **优点**：客户端与服务端解耦——服务端改了 URL，客户端跟着链接走，不用改代码。这是 REST“理想形态”。
- **现实**：实现成本高，前端要写“链接解析器”，收益在多数业务场景不明显。因此 99% 的“RESTful API”其实不实现 HATEOAS，属于“REST 风格但不纯粹”。
- **价值**：理解 HATEOAS 能帮你领会 REST 的“自描述”哲学。在开放 API、需要动态发现能力的场景（如某些 BaaS 平台）值得采用。

> 本篇示例不强制实现 HATEOAS，但你在设计 API 时可以思考：如果加上 `_links`，客户端会更自由吗？这种思维训练比实现本身更重要。

---

## 五、实现一个完整 RESTful CRUD

> 本节对应 `Code/` 目录下的可运行代码。进入该目录执行 `npm install` 后 `npm start` 即可。

我们用 Express + 内存数组实现 `/api/v1/articles` 资源的完整 CRUD，综合运用前面所有理论。

### 5.1 文件结构

```
Code/
├── package.json          # 依赖声明（express）
├── response-helper.js    # 统一响应封装（success/error/paginate）
├── async-handler.js      # 异步错误包装器
├── pagination-demo.js    # 分页逻辑单独演示
├── articles-router.js    # 文章资源 CRUD（express.Router）
└── server.js             # 应用入口，挂载路由 + 错误处理中间件
```

### 5.2 统一响应封装（response-helper.js）

把“成功/失败/分页”三种响应收敛到三个工具函数，保证全项目响应结构一致：

```js
// 成功：{ code: 0, message, data }
function success(res, data, message = '操作成功', statusCode = 200) {
  if (statusCode === 204) return res.status(204).end(); // 204 无内容
  return res.status(statusCode).json({ code: 0, message, data });
}

// 失败：{ code, message, data: null }
function error(res, message = '操作失败', statusCode = 400, code = 1) {
  return res.status(statusCode).json({ code, message, data: null });
}

// 分页：{ code: 0, message, data: { list, total, page, pageSize, totalPages } }
function paginate(res, { list, total, page, pageSize }, message = '查询成功') {
  return res.status(200).json({
    code: 0,
    message,
    data: { list, total, page, pageSize, totalPages: Math.max(1, Math.ceil(total / pageSize)) },
  });
}
```

### 5.3 异步错误包装器（async-handler.js）

Express 4 不会自动捕获 `async/await` 抛出的 rejection，需要包装器把错误转发给错误处理中间件：

```js
function asyncHandler(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}
```

路由里这样用，就无需每个 handler 写 `try/catch`：

```js
router.get('/', asyncHandler(async (req, res) => {
  // 这里抛错会被自动转给错误处理中间件
  const data = await someAsyncOp();
  success(res, data);
}));
```

### 5.4 文章 CRUD（articles-router.js）

资源定义与路由映射：

| 方法 | 路由 | 功能 | 成功码 | 失败码 |
|------|------|------|--------|--------|
| GET | `/` | 列表（分页/过滤/排序） | 200 | — |
| GET | `/:id` | 详情 | 200 | 404 |
| POST | `/` | 创建 | 201 | 422 |
| PUT | `/:id` | 全量更新 | 200 | 404 / 422 |
| PATCH | `/:id` | 部分更新 | 200 | 404 / 422 |
| DELETE | `/:id` | 删除 | 204 | 404 |

核心设计要点：

1. **内存数组存储**：用模块级 `let articles = [...]` 模拟数据库，重启即重置。
2. **自增 id**：`let nextId = 4`，每次创建 `id: nextId++`。
3. **分页参数解析**：`page` 默认 1、`pageSize` 默认 10 且上限 100，非法值回退默认。
4. **过滤与排序**：支持 `?author=`、`?keyword=`、`?sort=field:desc`。
5. **校验**：POST/PUT 校验必填字段，失败返回 422。
6. **PATCH 白名单**：只允许更新 `title/content/author/tags`，防止客户端篡改 `id`、`createdAt`。
7. **时间戳**：创建时写 `createdAt`，更新时写 `updatedAt`。

### 5.5 应用入口与错误处理（server.js）

```js
app.use(express.json());                         // 解析 JSON body
app.use((req, res, next) => { /* 日志 */ });     // 请求日志
app.use('/api/v1/articles', articlesRouter);     // 挂载文章路由

app.get('/health', ...);                         // 健康检查
app.use((req, res) => { /* 404 */ });            // 兜底 404
app.use((err, req, res, next) => { /* 错误处理 */ }); // 错误中间件
```

错误处理中间件覆盖三类异常：

- **JSON 解析失败**（`entity.parse.failed`）→ 400
- **请求体过大**（`entity.too.large`）→ 413
- **其它未捕获错误** → 500

### 5.6 运行与测试

```bash
cd "Code"
npm install
npm start
# Server running at http://localhost:3000
```

`server.js` 注释里给出了覆盖所有方法的完整 curl 命令，包括正常流程与各类错误流程。也可用 `node pagination-demo.js` 单独观察分页逻辑。

---

## 六、常见反模式

识别反模式比记忆正模式更能加深理解。以下是 RESTful API 设计的高频坑。

### 反模式一：URI 中带动词

```
❌ POST /api/createArticle
❌ GET  /api/getArticleById/1
❌ POST /api/deleteArticle/1

✅ POST   /api/v1/articles       # 创建
✅ GET    /api/v1/articles/1     # 查询
✅ DELETE /api/v1/articles/1     # 删除
```

**问题**：动词挤进 URI，意味着你只在用 POST 一种方法，丢失了 HTTP 方法语义，客户端无法靠方法判断意图。

### 反模式二：用 GET 修改数据

```
❌ GET /api/articles/delete/1     # 用 GET 删除
❌ GET /api/articles/1?status=published  # 用 GET 改状态
```

**问题**：GET 必须是“安全”的。用 GET 改数据会导致：

- 搜索引擎爬虫/预加载无意中触发修改。
- 浏览器历史、缓存重放引发误操作。
- 违反 HTTP 语义，CDN/网关可能错误缓存。

### 反模式三：状态码乱用

| ❌ 反例 | 问题 | ✅ 正解 |
|---------|------|---------|
| 创建成功返回 `200` | 应返回 `201` 表示“已创建” | `201 Created` |
| 校验失败返回 `200 {error}` | 前端无法靠状态码分流 | `422` |
| 资源不存在返回 `500` | 这是客户端的错，不是服务端崩了 | `404` |
| 所有错误都 `500` | 触发误告警，前端无法区分 | 按场景用 4xx |
| 删除成功返回 `200 {ok:true}` | 无内容返回应用 204 | `204 No Content` |

### 反模式四：响应结构不一致

```
❌ 列表返回：{ articles: [...] }
❌ 详情返回：{ data: {...} }
❌ 错误返回：{ error: "msg" }
❌ 另一个错误：{ msg: "xxx", success: false }
```

**问题**：前端要为每个接口写专门的解析逻辑，维护成本爆炸。

**正解**：全项目统一 `{ code, message, data }`，列表的分页数据统一放 `data: { list, total, page, pageSize }`。

### 反模式五：URI 大小写混用、用下划线

```
❌ /api/v1/UserProfiles
❌ /api/v1/user_profiles
✅ /api/v1/user-profiles
```

**问题**：URI 路径区分大小写（RFC 3986），混用会导致“看起来一样但 404”的诡异问题。

### 反模式六：把动作塞进查询参数

```
❌ GET /api/articles?action=delete&id=1   # 又是 GET 改数据，又是 action 参数
✅ DELETE /api/articles/1
```

**问题**：把 RPC 风格的 `action` 参数套进 REST，两头不讨好。

---

## 七、API 文档

API 设计得好，还得文档跟得上，否则前端/外部调用方无从下手。

### 7.1 为什么需要文档

- **契约**：文档是前后端的“契约”，定义了接口的路径、方法、参数、响应。
- **自助**：好的文档让调用方无需问后端就能上手。
- **演进**：版本化文档记录 API 的变迁，便于追溯。

### 7.2 Swagger / OpenAPI 简述

**OpenAPI Specification（OAS）** 是描述 RESTful API 的工业标准（前身叫 Swagger Specification）。它用一份 JSON/YAML 文件完整描述一个 API：

- 有哪些接口（path + method）
- 每个接口的请求参数、请求体、响应结构
- 数据模型（schema）定义
- 认证方式

**Swagger** 则是围绕 OpenAPI 的一套工具生态：

| 工具 | 作用 |
|------|------|
| Swagger Editor | 在线编写/预览 OpenAPI 文件 |
| Swagger UI | 把 OpenAPI 文件渲染成可交互的文档页面（可在线试调用） |
| Swagger Codegen | 根据 OpenAPI 生成客户端 SDK / 服务端桩代码 |

一份 OpenAPI 文件长这样（YAML 片段）：

```yaml
openapi: 3.0.0
info:
  title: Articles API
  version: 1.0.0
paths:
  /api/v1/articles:
    get:
      summary: 获取文章列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedArticles'
    post:
      summary: 创建文章
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ArticleInput'
      responses:
        '201':
          description: 创建成功
```

### 7.3 用注释生成文档的思路

手写 OpenAPI 文件维护成本高，更工程化的做法是**从代码注释自动生成**。Node.js 生态常用 `swagger-jsdoc`：

1. 在路由代码里用 JSDoc 风格注释写 OpenAPI 片段。
2. `swagger-jsdoc` 扫描代码，把注释汇总成一份完整的 OpenAPI 文件。
3. `swagger-ui-express` 把这份文件挂到 `/api-docs` 路径，提供可交互文档页。

示意（不必现在运行，仅为铺垫）：

```js
/**
 * @openapi
 * /api/v1/articles:
 *   get:
 *     summary: 获取文章列表
 *     parameters:
 *       - name: page
 *         in: query
 *         schema:
 *           type: integer
 *     responses:
 *       200:
 *         description: 成功
 */
router.get('/', handler);
```

> 这种“注释即文档”的思路会在后续的 **API 文档化 skill** 中专门展开。本篇你只需建立认知：**好 API = 好设计 + 好文档**，而 OpenAPI 是连接两者的标准。

---

## 八、关键知识点总结

1. **REST 是架构风格，不是协议**。它依赖 HTTP 但不等于 HTTP；抓住“资源 + 统一接口 + 无状态”三大灵魂。
2. **六大约束**：客户端-服务端分离、无状态、统一接口、分层系统、可缓存（必选）+ 按需代码（可选）。其中统一接口是核心。
3. **URI 标识资源（名词复数），HTTP 方法表达动作**。这是 REST 与 RPC 风格的根本区别。
4. **HTTP 方法语义**：GET 安全且幂等；POST 不安全不幂等；PUT 不安全但幂等（全量替换）；PATCH 部分更新（默认不幂等）；DELETE 不安全但幂等。
5. **幂等性**：重复执行副作用不变。PUT/DELETE 天然防重复；POST 需用 Idempotency-Key 兜底——这是分布式防重的基础认知。
6. **状态码**：2xx 成功（200/201/204）、4xx 客户端错（400/401/403/404/409/422）、5xx 服务端错（500）。401 是“没登录”，403 是“没权限”；400 是“格式错”，422 是“语义错”。
7. **URI 设计**：名词复数、层级从属、query 过滤分页排序、避免动词、连字符分词全小写。
8. **版本化**：URI 版本（`/api/v1`）最主流、最直观；Header 版本最纯粹但难调试；查询参数版本用得少。不兼容改动才升版本。
9. **统一响应格式**：`{ code, message, data }` 是工业惯例；分页用 `data: { list, total, page, pageSize, totalPages }`；错误也要同构。
10. **HATEOAS** 是 REST 的理想形态（响应带可执行链接），现实中常被省略，但理解它能领会 REST 的“自描述”哲学。
11. **反模式要避坑**：URI 带动词、GET 改数据、状态码乱用、响应结构不一致——这四类是最高频的 API 设计烂味。
12. **API 文档**：OpenAPI 是描述 REST API 的工业标准，Swagger 是其工具生态；“注释生成文档”是工程化方向，后续 skill 会深入。

---

## 九、实战练习

> 以下练习在 `Code/` 目录基础上扩展，建议独立完成后再对照本篇结论自查。

### 练习一：为文章接口增加标签过滤与字段筛选

**目标**：扩展 `GET /api/v1/articles` 的 query 能力，练习 URI 设计规范中的“用 query 过滤”。

**要求**：

1. 支持 `?tag=node` 过滤包含某标签的文章（`tags` 是数组，需匹配数组元素）。
2. 支持 `?fields=id,title` 只返回指定字段（字段投影），减少网络传输。
3. 思考：`fields` 是放在 query 还是 header？为什么？

**考察点**：query 参数设计、数组过滤、字段投影的实现与权衡。

### 练习二：实现评论子资源 CRUD 并体会层级 URI

**目标**：新增 `/api/v1/articles/:articleId/comments` 资源，练习层级 URI 与从属资源管理。

**要求**：

1. 数据结构：`{ id, articleId, content, author, createdAt }`，存在内存数组中。
2. 实现 `GET /api/v1/articles/:articleId/comments`（某文章的评论列表）。
3. 实现 `POST /api/v1/articles/:articleId/comments`（为某文章新增评论）——若 `articleId` 不存在返回 404。
4. 实现 `DELETE /api/v1/articles/:articleId/comments/:commentId`（删除评论）。
5. 思考：评论是否也需要支持 `GET /api/v1/comments/:commentId` 这种“脱离父资源”的访问？什么情况下值得？

**考察点**：层级 URI 设计、从属资源校验、404 与父资源存在性的关系。

### 练习三：用 Idempotency-Key 给 POST 加幂等保护

**目标**：为 `POST /api/v1/articles` 实现幂等键机制，亲手把“不幂等”变“幂等”。

**要求**：

1. 读取请求头 `Idempotency-Key`，若不存在则正常创建（不强制）。
2. 若存在该头，用该 key 作为缓存键：
   - 首次请求：执行创建，把响应结果存入内存 Map（`key → response`）。
   - 重复请求（同 key）：直接返回缓存的结果，**不再创建新文章**。
3. 验证：用同一个 `Idempotency-Key` 连续 POST 3 次，数据库里只多 1 篇文章，3 次返回完全相同。
4. 思考：缓存的响应要不要连同状态码一起存？缓存该设过期时间吗？

**考察点**：幂等键的工程实现、Map 作为简易缓存、对“网络重试”场景的建模——这是支付类业务的核心机制。

---

> 完成本篇后，你已具备设计规范 RESTful API 的系统认知与实现能力。下一篇将在此基础上引入**数据库集成（从内存数组到持久化存储）**、**鉴权（JWT）**、**CORS 与跨域**等主题，让 API 从“能跑”走向“能上线”。
