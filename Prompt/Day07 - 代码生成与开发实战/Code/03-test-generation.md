# 测试生成模板

> 本文件提供单元测试生成 Prompt 模板，给定函数代码 → 生成测试用例（正常 / 异常 / 边界）→ 覆盖率分析。含 3 个示例：Python pytest / TypeScript Jest / API 接口测试。

---

## 模板说明
- 用途：为给定代码生成覆盖率导向的单元测试
- 适用模型：GPT-4 / Claude / 通用
- 变量：`{{language}}`、`{{test_framework}}`、`{{code}}`、`{{coverage_target}}`

## 完整模板

```text
你是一名资深测试工程师，精通 {{language}} 与 {{test_framework}}。

请为以下代码生成单元测试：

【待测代码】
{{code}}

测试要求：
1. 框架：{{test_framework}}
2. 覆盖率目标：{{coverage_target}}，覆盖所有分支
3. 用例分类：
   - 正常用例：典型业务场景
   - 异常用例：非法输入、依赖失败
   - 边界用例：临界值、空值、极值
4. 每个用例遵循 Arrange-Act-Assert 模式
5. 用例独立，不依赖执行顺序
6. 对外部依赖（DB / HTTP / 文件）使用 Mock
7. 命名规范：test_<场景>_<预期行为>

输出：
1. 完整测试文件
2. 用例清单（表格：用例名 / 分类 / 覆盖分支）
3. 覆盖率分析（哪些分支被覆盖，是否有遗漏）
4. Mock 设计说明
```

## 使用示例

### 示例 1：Python pytest 测试

#### 输入
```text
你是一名资深测试工程师，精通 Python 与 pytest。

请为以下代码生成单元测试：

【待测代码】
```python
from typing import Literal

def calculate_discount(
    user_level: Literal["bronze", "silver", "gold"],
    order_amount: float,
) -> float:
    if user_level not in ("bronze", "silver", "gold"):
        raise ValueError(f"非法用户等级: {user_level}")
    if order_amount <= 0:
        raise ValueError(f"订单金额必须为正数: {order_amount}")

    if user_level == "bronze":
        return round(order_amount - 20 if order_amount >= 200 else order_amount, 2)
    if user_level == "silver":
        return round(order_amount * 0.9, 2)
    # gold
    if order_amount >= 500:
        return round((order_amount - 80) * 0.85, 2)
    return round(order_amount * 0.85, 2)
```

测试要求：
1. 框架：pytest
2. 覆盖率目标：100%，覆盖所有分支
3. 用例分类：正常 / 异常 / 边界
4. 每个用例遵循 Arrange-Act-Assert 模式
5. 用例独立
6. 命名规范：test_<场景>_<预期行为>

输出：
1. 完整测试文件
2. 用例清单
3. 覆盖率分析
4. Mock 设计说明
```

#### 预期输出
```python
import pytest
from pytest import approx
from mymodule import calculate_discount


class TestCalculateDiscount:
    """calculate_discount 单元测试。"""

    # ---------- 正常用例 ----------
    @pytest.mark.parametrize(
        "level,amount,expected",
        [
            ("bronze", 250, 230.0),    # 满 200 减 20
            ("silver", 100, 90.0),     # 9 折
            ("gold",   600, 442.0),    # 满 500 减 80 + 8.5 折
            ("gold",   300, 255.0),    # gold 不满 500 直接 8.5 折
        ],
    )
    def test_normal_levels_return_expected_price(self, level, amount, expected):
        # Arrange & Act
        result = calculate_discount(level, amount)
        # Assert
        assert result == approx(expected, rel=1e-6)

    # ---------- 边界用例 ----------
    def test_bronze_boundary_just_200(self):
        # 刚好满 200，应触发满减
        assert calculate_discount("bronze", 200) == 180.0

    def test_bronze_boundary_just_below_200(self):
        # 差 1 分钱不满 200，不应触发
        assert calculate_discount("bronze", 199.99) == 199.99

    def test_gold_boundary_just_500(self):
        assert calculate_discount("gold", 500) == approx((500 - 80) * 0.85)

    def test_gold_boundary_just_below_500(self):
        assert calculate_discount("gold", 499.99) == approx(499.99 * 0.85)

    def test_minimum_positive_amount(self):
        # 极小正数
        assert calculate_discount("silver", 0.01) == approx(0.009, rel=1e-6)

    def test_large_amount(self):
        # 大金额
        assert calculate_discount("gold", 100000) == approx((100000 - 80) * 0.85)

    def test_float_precision_two_decimals(self):
        # 浮点精度应保留两位
        result = calculate_discount("silver", 33.33)
        assert result == round(33.33 * 0.9, 2)

    # ---------- 异常用例 ----------
    @pytest.mark.parametrize("invalid_level", ["", "GOLD", "platinum", None, 123])
    def test_invalid_level_raises(self, invalid_level):
        with pytest.raises(ValueError, match="非法用户等级"):
            calculate_discount(invalid_level, 100)

    @pytest.mark.parametrize("invalid_amount", [0, -1, -0.01])
    def test_non_positive_amount_raises(self, invalid_amount):
        with pytest.raises(ValueError, match="订单金额必须为正数"):
            calculate_discount("silver", invalid_amount)
```

| 用例名 | 分类 | 覆盖分支 |
|--------|------|---------|
| test_normal_levels_return_expected_price | 正常 | bronze 满/不满、silver、gold 满/不满 |
| test_bronze_boundary_just_200 | 边界 | bronze amount>=200 取真 |
| test_bronze_boundary_just_below_200 | 边界 | bronze amount>=200 取假 |
| test_gold_boundary_just_500 | 边界 | gold amount>=500 取真 |
| test_gold_boundary_just_below_500 | 边界 | gold amount>=500 取假 |
| test_minimum_positive_amount | 边界 | 极小正数路径 |
| test_large_amount | 边界 | 大数路径 |
| test_float_precision_two_decimals | 边界 | round 行为 |
| test_invalid_level_raises | 异常 | 非法等级分支 |
| test_non_positive_amount_raises | 异常 | 非法金额分支 |

覆盖率分析：所有分支均被覆盖，包括等级校验、金额校验、bronze 满减条件、gold 满减条件、round 调用。语句覆盖率与分支覆盖率均达 100%。

Mock 设计说明：本函数为纯函数，无外部依赖，不需要 Mock。

### 示例 2：TypeScript Jest 测试

#### 输入
```text
你是一名资深测试工程师，精通 TypeScript 与 Jest。

请为以下代码生成单元测试：

【待测代码】
```typescript
import axios from "axios";

export interface User { id: number; name: string; }

export async function fetchUser(userId: number): Promise<User> {
    if (userId <= 0) throw new Error("userId 必须为正数");
    const response = await axios.get<User>(`https://api.example.com/users/${userId}`);
    return response.data;
}

export function formatUserName(user: User | null): string {
    if (!user) return "匿名用户";
    return user.name.trim().toUpperCase();
}
```

测试要求：
1. 框架：Jest
2. 覆盖率目标：100%
3. 用例分类：正常 / 异常 / 边界
4. 遵循 Arrange-Act-Assert
5. 用例独立
6. 对 axios 使用 jest.mock

输出：
1. 完整测试文件
2. 用例清单
3. 覆盖率分析
4. Mock 设计说明
```

#### 预期输出
```typescript
import { fetchUser, formatUserName, User } from "./user";
import axios from "axios";

jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("fetchUser", () => {
    beforeEach(() => jest.clearAllMocks());

    it("正常返回用户数据", async () => {
        // Arrange
        const fake: User = { id: 1, name: "Alice" };
        mockedAxios.get.mockResolvedValue({ data: fake } as any);
        // Act
        const result = await fetchUser(1);
        // Assert
        expect(result).toEqual(fake);
        expect(mockedAxios.get).toHaveBeenCalledWith(
            "https://api.example.com/users/1"
        );
    });

    it("userId 为 0 抛错", async () => {
        await expect(fetchUser(0)).rejects.toThrow("userId 必须为正数");
        expect(mockedAxios.get).not.toHaveBeenCalled();
    });

    it("userId 为负数抛错", async () => {
        await expect(fetchUser(-5)).rejects.toThrow("userId 必须为正数");
    });

    it("userId 为最小正整数 1 不抛错", async () => {
        mockedAxios.get.mockResolvedValue({ data: { id: 1, name: "X" } } as any);
        await expect(fetchUser(1)).resolves.toBeDefined();
    });

    it("axios 抛错时向上传播", async () => {
        mockedAxios.get.mockRejectedValue(new Error("Network"));
        await expect(fetchUser(1)).rejects.toThrow("Network");
    });
});

describe("formatUserName", () => {
    it("user 为 null 返回匿名用户", () => {
        expect(formatUserName(null)).toBe("匿名用户");
    });

    it("user 为 undefined 返回匿名用户", () => {
        expect(formatUserName(undefined as any)).toBe("匿名用户");
    });

    it("name 含空格应 trim 后大写", () => {
        expect(formatUserName({ id: 1, name: "  alice  " })).toBe("ALICE");
    });

    it("name 为空字符串返回空字符串", () => {
        expect(formatUserName({ id: 1, name: "" })).toBe("");
    });

    it("name 为非英文应正常大写", () => {
        expect(formatUserName({ id: 1, name: "张三" })).toBe("张三");
    });
});
```

| 用例名 | 分类 | 覆盖分支 |
|--------|------|---------|
| 正常返回用户数据 | 正常 | axios 成功路径 |
| userId 为 0 抛错 | 边界 | userId<=0 取真 |
| userId 为负数抛错 | 异常 | userId<=0 取真 |
| userId 为最小正整数 | 边界 | userId<=0 取假 |
| axios 抛错向上传播 | 异常 | axios reject 路径 |
| user 为 null | 边界 | !user 取真 |
| user 为 undefined | 边界 | !user 取真 |
| name 含空格 | 正常 | trim+upper 路径 |
| name 为空字符串 | 边界 | 空字符串路径 |
| name 非英文 | 边界 | 非英文路径 |

覆盖率分析：所有分支覆盖，包括 userId 校验、null 判断、axios 成功/失败路径。语句覆盖率 100%。

Mock 设计说明：使用 jest.mock("axios") 替换 axios 模块，每个用例前 clearAllMocks 避免污染。

### 示例 3：API 接口测试

#### 输入
```text
你是一名资深测试工程师，精通 Python 与 FastAPI + httpx 异步测试。

请为以下 API 生成接口测试：

【待测代码】
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

_products: dict[int, dict] = {}
_next_id = 1

@app.post("/products", status_code=201)
def create_product(payload: ProductCreate):
    global _next_id
    product = {"id": _next_id, **payload.model_dump()}
    _products[_next_id] = product
    _next_id += 1
    return product

@app.get("/products/{pid}")
def get_product(pid: int):
    if pid not in _products:
        raise HTTPException(status_code=404, detail="not found")
    return _products[pid]
```

测试要求：
1. 框架：pytest + httpx.AsyncClient
2. 覆盖率目标：100%
3. 用例分类：正常 / 异常 / 边界
4. 每个用例独立（fixture 重置 _products）
5. 命名规范：test_<场景>_<预期>

输出：
1. 完整测试文件
2. 用例清单
3. 覆盖率分析
4. Mock 设计说明
```

#### 预期输出
```python
import pytest
from httpx import AsyncClient, ASGITransport
from mymodule import app, _products, _next_id


@pytest.fixture(autouse=True)
def reset_store():
    _products.clear()
    import mymodule
    mymodule._next_id = 1
    yield
    _products.clear()


@pytest.mark.asyncio
async def test_create_product_success_returns_201():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        resp = await client.post("/products", json={
            "name": "耳机", "price": 299, "stock": 10
        })
    assert resp.status_code == 201
    assert resp.json()["id"] == 1
    assert resp.json()["name"] == "耳机"


@pytest.mark.asyncio
async def test_create_product_with_empty_name_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        resp = await client.post("/products", json={
            "name": "", "price": 10, "stock": 1
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_product_with_zero_price_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        resp = await client.post("/products", json={
            "name": "X", "price": 0, "stock": 1
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_product_with_negative_stock_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        resp = await client.post("/products", json={
            "name": "X", "price": 10, "stock": -1
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_product_success_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        await client.post("/products", json={
            "name": "X", "price": 10, "stock": 1
        })
        resp = await client.get("/products/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"


@pytest.mark.asyncio
async def test_get_product_not_found_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        resp = await client.get("/products/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_product_with_invalid_id_type_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        resp = await client.get("/products/abc")
    assert resp.status_code == 422
```

| 用例名 | 分类 | 覆盖分支 |
|--------|------|---------|
| test_create_product_success_returns_201 | 正常 | 创建成功路径 |
| test_create_product_with_empty_name_returns_422 | 异常 | name 校验失败 |
| test_create_product_with_zero_price_returns_422 | 边界 | price gt=0 边界 |
| test_create_product_with_negative_stock_returns_422 | 异常 | stock 校验失败 |
| test_get_product_success_returns_200 | 正常 | 查询成功路径 |
| test_get_product_not_found_returns_404 | 异常 | pid 不在 _products |
| test_get_product_with_invalid_id_type_returns_422 | 异常 | 类型校验失败 |

覆盖率分析：覆盖创建与查询全部成功 / 失败路径，包括 Pydantic 校验失败、404、422。语句覆盖率 100%。

Mock 设计说明：使用 ASGITransport 直接挂载 app，无需启动真实 HTTP 服务；autouse fixture 在每个用例前后重置内存存储，保证用例独立。

## 调优建议
- 温度：0.0（测试需稳定可重复）
- 若被测代码有复杂依赖，先让 LLM 列出"依赖清单"，再分别设计 Mock
- 若覆盖率不达标，追加 Prompt："以下分支未覆盖：xxx，请补充用例"
- API 测试推荐 httpx + ASGITransport，性能优于 TestClient
