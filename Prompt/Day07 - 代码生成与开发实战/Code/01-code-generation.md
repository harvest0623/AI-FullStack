# 代码生成模板合集

> 本文件包含 6 个代码生成 Prompt 模板，覆盖函数、类、API、SQL、正则、配置六大场景。所有模板均可直接复制到主流 LLM 使用。

---

## 模板 1：函数生成 - 电商折扣计算函数

### 模板说明
- 用途：根据用户等级和订单金额生成电商折扣计算函数
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{user_levels}}`、`{{discount_rules}}`、`{{language_version}}`

### 完整模板

```text
你是一名资深 Python 后端工程师，请用 {{language_version}} 编写一个电商折扣计算函数。

需求：
- 功能：根据用户等级和订单金额计算最终折扣价
- 输入：user_level(str)、order_amount(float，单位元)
- 输出：final_price(float，保留两位小数)

用户等级与折扣规则：
{{user_levels}}
{{discount_rules}}

约束：
- 严格遵循 PEP 8 规范，类型注解齐全
- 必须包含 docstring（Google Style）
- 输入非法时抛出 ValueError，并附带明确的错误信息
- 不使用 eval / exec
- 不引入第三方依赖
- 时间复杂度 O(1)

输出格式：
1. 完整函数代码（含 docstring）
2. 3 个调用示例
3. 边界条件说明（列出至少 5 种边界情况）
```

### 使用示例

#### 输入
```text
你是一名资深 Python 后端工程师，请用 Python 3.12 编写一个电商折扣计算函数。

需求：
- 功能：根据用户等级和订单金额计算最终折扣价
- 输入：user_level(str)、order_amount(float，单位元)
- 输出：final_price(float，保留两位小数)

用户等级与折扣规则：
- bronze：满 200 减 20，否则不打折
- silver：9 折
- gold：满 500 减 80 + 8.5 折

约束：
- 严格遵循 PEP 8 规范，类型注解齐全
- 必须包含 docstring（Google Style）
- 输入非法时抛出 ValueError，并附带明确的错误信息
- 不使用 eval / exec
- 不引入第三方依赖
- 时间复杂度 O(1)

输出格式：
1. 完整函数代码（含 docstring）
2. 3 个调用示例
3. 边界条件说明（列出至少 5 种边界情况）
```

#### 预期输出
```python
def calculate_discount(user_level: str, order_amount: float) -> float:
    """根据用户等级和订单金额计算最终折扣价。

    Args:
        user_level: 用户等级，取值 bronze/silver/gold。
        order_amount: 订单金额（元），必须为正数。

    Returns:
        折扣后价格，保留两位小数。

    Raises:
        ValueError: 当 user_level 非法或 order_amount <= 0 时。

    Examples:
        >>> calculate_discount("bronze", 250)
        230.0
        >>> calculate_discount("silver", 100)
        90.0
        >>> calculate_discount("gold", 600)
        442.0
    """
    valid_levels = {"bronze", "silver", "gold"}
    if user_level not in valid_levels:
        raise ValueError(
            f"非法用户等级: {user_level}，可选值: {valid_levels}"
        )
    if order_amount <= 0:
        raise ValueError(f"订单金额必须为正数，当前: {order_amount}")

    if user_level == "bronze":
        final_price = order_amount - 20 if order_amount >= 200 else order_amount
    elif user_level == "silver":
        final_price = order_amount * 0.9
    else:  # gold
        if order_amount >= 500:
            final_price = (order_amount - 80) * 0.85
        else:
            final_price = order_amount * 0.85

    return round(final_price, 2)


# 调用示例
print(calculate_discount("bronze", 250))   # 230.0
print(calculate_discount("silver", 100))   # 90.0
print(calculate_discount("gold", 600))     # 442.0
```

边界条件说明：
1. order_amount 刚好等于 200（bronze 满减临界）
2. order_amount 刚好等于 500（gold 满减临界）
3. order_amount 为极小浮点数（如 0.01）
4. user_level 为大写（如 "GOLD"）—— 当前实现区分大小写，可按需扩展
5. order_amount 为整数 0 —— 应抛出 ValueError

### 调优建议
- 温度：0.0（代码生成需确定性）
- 若需支持优惠券叠加，可在 Prompt 中追加"优惠券规则"小节
- 若 LLM 输出多余解释，在 Prompt 末尾追加"只输出代码块和边界说明，不要其他解释"

---

## 模板 2：类生成 - Product 数据类

### 模板说明
- 用途：生成电商商品数据类，含字段校验、序列化、魔术方法
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{class_name}}`、`{{fields}}`、`{{methods}}`

### 完整模板

```text
请用 Python 3.12 设计一个 {{class_name}} 数据类，遵循 PEP 8 与 dataclass 最佳实践。

字段定义：
{{fields}}

需要实现的方法：
{{methods}}

约束：
1. 使用 @dataclass 装饰器
2. 字段校验：非法值抛出 ValueError
3. 实现类型注解
4. 不引入第三方依赖（仅标准库）
5. 包含完整 docstring

输出：
1. 完整类定义
2. 使用示例（创建、序列化、反序列化、比较）
```

### 使用示例

#### 输入
```text
请用 Python 3.12 设计一个 Product 数据类，遵循 PEP 8 与 dataclass 最佳实践。

字段定义：
- product_id: str
- name: str
- price: float（必须 > 0）
- stock: int（必须 >= 0）
- category: str

需要实现的方法：
- to_dict() -> dict：序列化为字典
- from_dict(cls, data: dict) -> Product：类方法反序列化
- apply_discount(self, rate: float) -> None：应用折扣（rate 取值 0-1）
- __repr__、__eq__

约束：
1. 使用 @dataclass 装饰器
2. 字段校验：非法值抛出 ValueError
3. 实现类型注解
4. 不引入第三方依赖（仅标准库）
5. 包含完整 docstring

输出：
1. 完整类定义
2. 使用示例（创建、序列化、反序列化、比较）
```

#### 预期输出
```python
from dataclasses import dataclass, asdict
from typing import ClassVar


@dataclass
class Product:
    """电商商品数据类。

    Attributes:
        product_id: 商品唯一标识。
        name: 商品名称。
        price: 商品单价（元），必须大于 0。
        stock: 库存数量，必须大于等于 0。
        category: 商品类别。
    """

    product_id: str
    name: str
    price: float
    stock: int
    category: str

    _VALID_CATEGORIES: ClassVar[set] = {
        "electronics", "books", "clothing", "food", "other"
    }

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError(f"price 必须大于 0，当前: {self.price}")
        if self.stock < 0:
            raise ValueError(f"stock 必须大于等于 0，当前: {self.stock}")
        if not self.product_id or not self.name:
            raise ValueError("product_id 和 name 不能为空")

    def to_dict(self) -> dict:
        """序列化为字典。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """从字典反序列化。"""
        return cls(
            product_id=data["product_id"],
            name=data["name"],
            price=float(data["price"]),
            stock=int(data["stock"]),
            category=data["category"],
        )

    def apply_discount(self, rate: float) -> None:
        """应用折扣。

        Args:
            rate: 折扣率，取值 0-1（如 0.85 表示 8.5 折）。

        Raises:
            ValueError: 当 rate 不在 [0, 1] 区间时。
        """
        if not 0 <= rate <= 1:
            raise ValueError(f"rate 必须在 [0, 1] 区间，当前: {rate}")
        self.price = round(self.price * rate, 2)

    def __repr__(self) -> str:
        return (
            f"Product(product_id={self.product_id!r}, "
            f"name={self.name!r}, price={self.price}, "
            f"stock={self.stock}, category={self.category!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.product_id == other.product_id


# 使用示例
p1 = Product("P001", "无线耳机", 299.0, 100, "electronics")
print(p1.to_dict())
p1.apply_discount(0.9)
print(p1.price)  # 269.1

p2 = Product.from_dict({
    "product_id": "P001", "name": "无线耳机",
    "price": 299.0, "stock": 100, "category": "electronics"
})
print(p1 == p2)  # True（按 product_id 比较）
```

### 调优建议
- 温度：0.0
- 若需 ORM 集成，可在 Prompt 中追加"使用 SQLAlchemy 2.x 映射"
- 若字段较多，可让 LLM 分组生成（基础信息 / 价格信息 / 库存信息）

---

## 模板 3：API 设计 - RESTful 商品 CRUD 接口

### 模板说明
- 用途：生成符合 RESTful 规范的商品 CRUD API
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{resource}}`、`{{tech_stack}}`、`{{error_format}}`

### 完整模板

```text
请设计一组 RESTful API 接口，技术栈：{{tech_stack}}。

资源路径：{{resource}}

要求：
1. 实现完整 CRUD 接口：
   - GET    {{resource}}          列表查询（支持分页 page/page_size、筛选 keyword）
   - GET    {{resource}}/{id}     详情查询
   - POST   {{resource}}          创建资源
   - PUT    {{resource}}/{id}     全量更新
   - DELETE {{resource}}/{id}     删除资源

2. 为每个接口定义请求模型和响应模型（Pydantic v2）

3. 错误响应统一格式：
{{error_format}}

4. 状态码使用规范：200 / 201 / 204 / 400 / 404 / 422 / 500

5. 包含输入校验、异常处理、日志记录

输出：
1. 完整路由代码（含 Pydantic 模型）
2. 全局异常处理中间件
3. curl 调用示例（每个接口一个）
```

### 使用示例

#### 输入
```text
请设计一组 RESTful API 接口，技术栈：FastAPI 0.110 + Pydantic v2 + Python 3.12。

资源路径：/api/v1/products

要求：
1. 实现完整 CRUD 接口：
   - GET    /api/v1/products          列表查询（支持分页 page/page_size、筛选 keyword）
   - GET    /api/v1/products/{id}     详情查询
   - POST   /api/v1/products          创建资源
   - PUT    /api/v1/products/{id}     全量更新
   - DELETE /api/v1/products/{id}     删除资源

2. 为每个接口定义请求模型和响应模型（Pydantic v2）

3. 错误响应统一格式：
   {"code": "ERROR_CODE", "message": "描述", "details": {}}

4. 状态码使用规范：200 / 201 / 204 / 400 / 404 / 422 / 500

5. 包含输入校验、异常处理、日志记录

输出：
1. 完整路由代码（含 Pydantic 模型）
2. 全局异常处理中间件
3. curl 调用示例（每个接口一个）
```

#### 预期输出
```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="商品服务", version="1.0.0")


# ---------- Pydantic 模型 ----------
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = {}


# ---------- 模拟存储 ----------
_products: dict[int, dict] = {}
_next_id = 1


# ---------- 接口 ----------
@app.get("/api/v1/products", response_model=ProductListResponse)
def list_products(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
):
    items = list(_products.values())
    if keyword:
        items = [p for p in items if keyword in p["name"]]
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return ProductListResponse(
        total=total, page=page, page_size=page_size,
        items=[ProductResponse(**p) for p in items[start:end]],
    )


@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    if product_id not in _products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PRODUCT_NOT_FOUND",
                    "message": f"商品 {product_id} 不存在", "details": {}},
        )
    return ProductResponse(**_products[product_id])


@app.post(
    "/api/v1/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(payload: ProductCreate):
    global _next_id
    product = {"id": _next_id, **payload.model_dump()}
    _products[_next_id] = product
    logger.info("创建商品 id=%s", _next_id)
    _next_id += 1
    return ProductResponse(**product)


@app.put("/api/v1/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductUpdate):
    if product_id not in _products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PRODUCT_NOT_FOUND",
                    "message": f"商品 {product_id} 不存在", "details": {}},
        )
    _products[product_id].update(payload.model_dump())
    return ProductResponse(**_products[product_id])


@app.delete("/api/v1/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    if product_id not in _products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PRODUCT_NOT_FOUND",
                    "message": f"商品 {product_id} 不存在", "details": {}},
        )
    del _products[product_id]
```

curl 示例：
```bash
# 创建
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name":"耳机","price":299,"stock":100,"category":"electronics"}'

# 列表
curl "http://localhost:8000/api/v1/products?page=1&page_size=20&keyword=耳"

# 详情
curl http://localhost:8000/api/v1/products/1

# 更新
curl -X PUT http://localhost:8000/api/v1/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"蓝牙耳机","price":259,"stock":80,"category":"electronics"}'

# 删除
curl -X DELETE http://localhost:8000/api/v1/products/1
```

### 调优建议
- 温度：0.0
- 若需数据库版本，追加"使用 SQLAlchemy 2.x + AsyncSession"
- 若需鉴权，追加"使用 JWT Bearer 鉴权，依赖 OAuth2PasswordBearer"

---

## 模板 4：SQL 生成 - 订单统计复杂查询

### 模板说明
- 用途：生成订单统计的复杂 SQL 查询，含表结构与索引建议
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{db_version}}`、`{{tables}}`、`{{query_requirement}}`

### 完整模板

```text
数据库：{{db_version}}

请根据以下需求生成 SQL：

【表结构设计】
{{tables}}

要求：
1. 合理设置主键、外键、索引
2. 字段类型与约束符合电商场景
3. 包含 created_at 和 updated_at 时间戳
4. 使用合适的字符集与引擎

【复杂查询】
{{query_requirement}}

输出：
1. DDL 建表语句（含索引）
2. DQL 查询语句
3. 索引优化建议（说明每个索引的用途）
4. 潜在性能问题与优化思路
```

### 使用示例

#### 输入
```text
数据库：MySQL 8.0

请根据以下需求生成 SQL：

【表结构设计】
- users: id, username, email, level(枚举 bronze/silver/gold), created_at, updated_at
- products: id, name, price, stock, category, created_at, updated_at
- orders: id, user_id, total_amount, status(枚举 pending/paid/shipped/delivered/cancelled), created_at, updated_at
- order_items: id, order_id, product_id, quantity, unit_price

要求：
1. 合理设置主键、外键、索引
2. 字段类型与约束符合电商场景
3. 包含 created_at 和 updated_at 时间戳
4. 使用合适的字符集与引擎

【复杂查询】
查询 2025 年 Q4（10-12 月）每个用户的：
- 订单总数
- 总消费金额
- 最常购买的商品类别
- 客单价（总消费 / 订单数）
只统计 status != 'cancelled' 的订单，按总消费金额降序，取 TOP 10。

输出：
1. DDL 建表语句（含索引）
2. DQL 查询语句
3. 索引优化建议（说明每个索引的用途）
4. 潜在性能问题与优化思路
```

#### 预期输出
```sql
-- ========== DDL ==========
CREATE TABLE users (
    id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) NOT NULL,
    level       ENUM('bronze','silver','gold') NOT NULL DEFAULT 'bronze',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_email (email),
    KEY idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE products (
    id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    price       DECIMAL(10,2) NOT NULL,
    stock       INT UNSIGNED NOT NULL DEFAULT 0,
    category    VARCHAR(50)  NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_category (category),
    KEY idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE orders (
    id           BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    user_id      BIGINT UNSIGNED NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    status       ENUM('pending','paid','shipped','delivered','cancelled')
                 NOT NULL DEFAULT 'pending',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_user_created (user_id, created_at),
    KEY idx_status_created (status, created_at),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE order_items (
    id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    order_id    BIGINT UNSIGNED NOT NULL,
    product_id  BIGINT UNSIGNED NOT NULL,
    quantity    INT UNSIGNED NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,
    KEY idx_order (order_id),
    KEY idx_product (product_id),
    CONSTRAINT fk_oi_order   FOREIGN KEY (order_id)   REFERENCES orders(id),
    CONSTRAINT fk_oi_product FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== DQL ==========
SELECT
    u.id                AS user_id,
    u.username,
    COUNT(DISTINCT o.id) AS order_count,
    SUM(o.total_amount)  AS total_spent,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT o.id), 2) AS avg_order_value,
    (
        SELECT p2.category
        FROM order_items oi2
        JOIN products p2 ON p2.id = oi2.product_id
        JOIN orders o2   ON o2.id = oi2.order_id
        WHERE o2.user_id = u.id
          AND o2.status != 'cancelled'
          AND o2.created_at BETWEEN '2025-10-01' AND '2025-12-31 23:59:59'
        GROUP BY p2.category
        ORDER BY SUM(oi2.quantity) DESC
        LIMIT 1
    ) AS top_category
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.status != 'cancelled'
  AND o.created_at BETWEEN '2025-10-01' AND '2025-12-31 23:59:59'
GROUP BY u.id, u.username
ORDER BY total_spent DESC
LIMIT 10;
```

索引优化建议：
1. `idx_user_created(user_id, created_at)` —— 加速按用户 + 时间范围查询订单
2. `idx_status_created(status, created_at)` —— 加速按状态 + 时间过滤
3. `idx_category(category)` —— 加速商品类别分组
4. `idx_order(order_id)` / `idx_product(product_id)` —— 加速 JOIN

潜在性能问题：
1. `top_category` 子查询对每个用户执行一次，数据量大时变慢，可改为 JOIN 派生表
2. `SUM(o.total_amount)` 在大表上较慢，可建物化视图或汇总表
3. 时间范围查询若跨大量历史数据，建议按月分区

### 调优建议
- 温度：0.0
- 复杂查询建议追加"请用 EXPLAIN 分析执行计划"
- 若用 PostgreSQL，需调整类型（BIGSERIAL、TIMESTAMPTZ）

---

## 模板 5：正则生成 - 邮箱手机号验证

### 模板说明
- 用途：生成邮箱和手机号的正则表达式与校验函数
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{validation_targets}}`、`{{language}}`

### 完整模板

```text
请用 {{language}} 编写正则表达式与校验函数，用于以下场景：
{{validation_targets}}

要求：
1. 每个正则附带详细注释（解释每个分组的作用）
2. 提供至少 5 个测试用例（含合法 / 非法样本）
3. 校验函数返回 bool，并支持返回错误原因
4. 不使用第三方库

输出：
1. 正则定义（带注释）
2. 校验函数
3. 测试用例与预期结果
```

### 使用示例

#### 输入
```text
请用 Python 3.12 编写正则表达式与校验函数，用于以下场景：
1. 中国大陆手机号（11 位，1 开头，第二位 3-9）
2. 邮箱地址（标准格式，含子域名）
3. 18 位身份证号（含校验位）

要求：
1. 每个正则附带详细注释（解释每个分组的作用）
2. 提供至少 5 个测试用例（含合法 / 非法样本）
3. 校验函数返回 bool，并支持返回错误原因
4. 不使用第三方库

输出：
1. 正则定义（带注释）
2. 校验函数
3. 测试用例与预期结果
```

#### 预期输出
```python
import re
from typing import tuple

# 中国大陆手机号：1 开头，第二位 3-9，共 11 位
PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")

# 邮箱：用户名@域名，支持子域名
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@"        # 用户名部分
    r"([A-Za-z0-9-]+\.)+"          # 域名（可含子域名）
    r"[A-Za-z]{2,}$"               # 顶级域
)

# 18 位身份证：6 位地区码 + 8 位生日 + 3 位顺序 + 1 位校验
ID_CARD_PATTERN = re.compile(
    r"^(?P<region>\d{6})"          # 地区码
    r"(?P<birth>\d{8})"            # 出生日期
    r"\d{3}"                       # 顺序码
    r"[0-9Xx]$"                    # 校验位
)


def validate_phone(value: str) -> tuple[bool, str]:
    if not value:
        return False, "手机号不能为空"
    if not PHONE_PATTERN.match(value):
        return False, f"手机号格式错误: {value}"
    return True, "OK"


def validate_email(value: str) -> tuple[bool, str]:
    if not value:
        return False, "邮箱不能为空"
    if not EMAIL_PATTERN.match(value):
        return False, f"邮箱格式错误: {value}"
    return True, "OK"


def validate_id_card(value: str) -> tuple[bool, str]:
    if not value:
        return False, "身份证号不能为空"
    if not ID_CARD_PATTERN.match(value):
        return False, f"身份证号格式错误: {value}"
    return True, "OK"


# 测试用例
test_cases = [
    ("phone", "13812345678", True),
    ("phone", "12345678901", False),   # 第二位非法
    ("phone", "1381234567",  False),   # 位数不足
    ("email", "user@example.com",     True),
    ("email", "user.name@sub.example.com", True),
    ("email", "invalid-email",        False),
    ("id_card", "11010119900307845X", True),
    ("id_card", "11010119900307845",  False),  # 位数不足
]

for kind, value, expected in test_cases:
    fn = {"phone": validate_phone, "email": validate_email,
          "id_card": validate_id_card}[kind]
    ok, msg = fn(value)
    assert ok == expected, f"{kind} {value} 期望 {expected}，实际 {ok}: {msg}"
print("全部通过")
```

### 调优建议
- 温度：0.0
- 正则极易出错，务必要求 LLM 给出测试用例
- 复杂正则可让 LLM 使用 `re.VERBOSE` 模式分段注释

---

## 模板 6：配置生成 - Docker Compose 配置

### 模板说明
- 用途：生成多服务 Docker Compose 配置
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{services}}`、`{{network_requirement}}`

### 完整模板

```text
请生成一份 docker-compose.yml 配置文件，版本：Compose Specification（兼容 Docker Compose v2）。

需要包含的服务：
{{services}}

网络与数据卷要求：
{{network_requirement}}

约束：
1. 每个服务设置合理的 restart 策略、健康检查、资源限制
2. 敏感配置通过 .env 文件注入，不硬编码
3. 服务间通过服务名访问
4. 数据卷持久化数据库数据
5. 给出对应的 .env.example 文件

输出：
1. docker-compose.yml
2. .env.example
3. 启动与停止命令
4. 服务依赖关系说明
```

### 使用示例

#### 输入
```text
请生成一份 docker-compose.yml 配置文件，版本：Compose Specification（兼容 Docker Compose v2）。

需要包含的服务：
1. web: FastAPI 应用，镜像 myapp:latest，暴露 8000 端口
2. db: MySQL 8.0，暴露 3306，持久化数据
3. redis: Redis 7，暴露 6379，持久化数据
4. nginx: Nginx 1.25，反向代理 web 服务，暴露 80

网络与数据卷要求：
- 自定义桥接网络 appnet
- db_data 持久化 MySQL
- redis_data 持久化 Redis
- nginx 通过挂载卷加载配置

约束：
1. 每个服务设置合理的 restart 策略、健康检查、资源限制
2. 敏感配置通过 .env 文件注入，不硬编码
3. 服务间通过服务名访问
4. 数据卷持久化数据库数据
5. 给出对应的 .env.example 文件

输出：
1. docker-compose.yml
2. .env.example
3. 启动与停止命令
4. 服务依赖关系说明
```

#### 预期输出
```yaml
# docker-compose.yml
services:
  web:
    image: myapp:latest
    container_name: app-web
    restart: unless-stopped
    env_file: .env
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks: [appnet]
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: mysql:8.0
    container_name: app-db
    restart: unless-stopped
    env_file: .env
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
    networks: [appnet]
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: app-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks: [appnet]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:1.25-alpine
    container_name: app-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web
    networks: [appnet]

networks:
  appnet:
    driver: bridge

volumes:
  db_data:
  redis_data:
```

```bash
# .env.example
MYSQL_ROOT_PASSWORD=change_me_root
MYSQL_DATABASE=appdb
DB_HOST=db
REDIS_HOST=redis
```

```bash
# 启动
docker compose --env-file .env up -d

# 查看状态
docker compose ps

# 停止
docker compose down

# 停止并清除数据卷（谨慎）
docker compose down -v
```

服务依赖关系：
- nginx → web（反向代理）
- web → db（条件：db 健康）
- web → redis（条件：redis 健康）
- db、redis 无依赖

### 调优建议
- 温度：0.0
- 生产环境追加"使用 docker secrets 管理敏感配置"
- 若需多环境，追加"生成 docker-compose.override.yml 用于开发"
