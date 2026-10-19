# 文件用途：描述符练习
# 演示内容：自定义描述符、__get__/__set__/__delete__、数据描述符 vs 非数据描述符
# 电商场景：ValidatedField 验证商品价格非负、CachedField 缓存计算结果
# Python 3.10+ 可运行


# ============================================================
# 1. 描述符基础 - __get__ / __set__ / __delete__
# ============================================================

class SimpleDescriptor:
    """简单描述符：记录属性访问"""

    def __set_name__(self, owner, name):
        """当描述符被赋值给类属性时调用"""
        self.name = name
        self.private_name = f"_descriptor_{name}"
        print(f"  [描述符] __set_name__ owner={owner.__name__} name={name}")

    def __get__(self, obj, objtype=None):
        """获取属性值"""
        if obj is None:
            return self  # 类访问时返回描述符本身
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        """设置属性值"""
        print(f"  [描述符] 设置 {self.name} = {value}")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj):
        """删除属性"""
        print(f"  [描述符] 删除 {self.name}")
        if hasattr(obj, self.private_name):
            delattr(obj, self.private_name)


class SimpleExample:
    """简单描述符示例"""
    value = SimpleDescriptor()


def demo_simple_descriptor() -> None:
    """演示简单描述符"""
    print("=" * 60)
    print("示例 1：描述符基础（__get__/__set__/__delete__）")
    print("=" * 60)

    obj = SimpleExample()
    obj.value = 42       # 触发 __set__
    print(f"读取: {obj.value}")  # 触发 __get__
    del obj.value         # 触发 __delete__

    print("\n类访问返回描述符本身:")
    print(f"SimpleExample.value = {SimpleExample.value}")


# ============================================================
# 2. ValidatedField 描述符 - 验证商品价格非负
# ============================================================

class ValidatedField:
    """验证描述符：验证值是否满足条件

    Args:
        validator: 验证函数，返回 True/False
        error_msg: 验证失败时的错误信息
    """

    def __init__(self, validator, error_msg: str = "验证失败"):
        self.validator = validator
        self.error_msg = error_msg

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_validated_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        if not self.validator(value):
            raise ValueError(f"{self.name}: {self.error_msg}（实际值: {value}）")
        print(f"  ✅ {self.name} 验证通过: {value}")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj):
        if hasattr(obj, self.private_name):
            delattr(obj, self.private_name)


def is_non_negative(value) -> bool:
    """非负验证"""
    return value >= 0


def is_positive(value) -> bool:
    """正数验证"""
    return value > 0


def is_non_empty_string(value) -> bool:
    """非空字符串验证"""
    return bool(value) and isinstance(value, str)


class Product:
    """商品模型 - 使用 ValidatedField 描述符"""

    price = ValidatedField(is_non_negative, "价格不能为负")
    stock = ValidatedField(is_non_negative, "库存不能为负")
    name = ValidatedField(is_non_empty_string, "名称不能为空")

    def __init__(self, id: int, name: str, price: float, stock: int):
        self.id = id
        # 触发描述符验证
        self.name = name
        self.price = price
        self.stock = stock

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name!r}, price={self.price}, stock={self.stock})"


def demo_validated_field() -> None:
    """演示 ValidatedField 验证商品"""
    print("\n" + "=" * 60)
    print("示例 2：ValidatedField 验证商品价格非负")
    print("=" * 60)

    # 正常创建
    print("创建合法商品：")
    p = Product(1, "iPhone", 9999.0, 50)
    print(f"  结果: {p}")

    # 验证失败 - 负价格
    print("\n尝试设置负价格：")
    try:
        p.price = -100.0
    except ValueError as e:
        print(f"  ❌ 验证失败: {e}")

    # 验证失败 - 空名称
    print("\n尝试设置空名称：")
    try:
        p.name = ""
    except ValueError as e:
        print(f"  ❌ 验证失败: {e}")

    # 验证失败 - 负库存
    print("\n尝试创建负库存商品：")
    try:
        Product(2, "Test", 100.0, -5)
    except ValueError as e:
        print(f"  ❌ 验证失败: {e}")


# ============================================================
# 3. CachedField 描述符 - 缓存计算结果
# ============================================================

class CachedField:
    """缓存描述符：缓存计算结果，避免重复计算

    使用 __get__ 的方式，第一次访问时计算并缓存
    """

    def __init__(self, getter):
        self.getter = getter
        self.cache_attr: str = ""

    def __set_name__(self, owner, name):
        self.name = name
        self.cache_attr = f"_cached_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        # 检查缓存
        if hasattr(obj, self.cache_attr):
            return getattr(obj, self.cache_attr)

        # 计算并缓存
        print(f"  [缓存] 首次计算 {self.name}")
        result = self.getter(obj)
        setattr(obj, self.cache_attr, result)
        return result

    def __set__(self, obj, value):
        """手动设置缓存值"""
        print(f"  [缓存] 手动设置 {self.name} = {value}")
        setattr(obj, self.cache_attr, value)

    def invalidate(self, obj):
        """使缓存失效"""
        if hasattr(obj, self.cache_attr):
            print(f"  [缓存] 使 {self.name} 缓存失效")
            delattr(obj, self.cache_attr)


class OrderItem:
    """订单项"""

    def __init__(self, product_id: int, name: str, price: float, qty: int):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.qty = qty

    # 使用 CachedField 缓存计算结果
    # 注意：这里 getter 是一个方法，会在 __get__ 中被调用
    total = CachedField(lambda self: round(self.price * self.qty, 2))
    total_with_tax = CachedField(
        lambda self: round(self.total * 1.13, 2)
    )


def demo_cached_field() -> None:
    """演示 CachedField 缓存计算结果"""
    print("\n" + "=" * 60)
    print("示例 3：CachedField 缓存计算结果")
    print("=" * 60)

    item = OrderItem(1, "iPhone", 9999.0, 3)

    print("第一次访问 total：")
    total1 = item.total
    print(f"  结果: {total1}")

    print("\n第二次访问 total（命中缓存）：")
    total2 = item.total
    print(f"  结果: {total2}")

    print("\n访问 total_with_tax（依赖 total）：")
    tax_total = item.total_with_tax
    print(f"  结果: {tax_total}")

    print("\n使 total 缓存失效后重新访问：")
    OrderItem.total.invalidate(item)
    total3 = item.total
    print(f"  结果: {total3}")


# ============================================================
# 4. 数据描述符 vs 非数据描述符
# ============================================================

class DataDescriptor:
    """数据描述符：有 __get__ 和 __set__"""

    def __get__(self, obj, objtype=None):
        return "数据描述符的值"

    def __set__(self, obj, value):
        print(f"  数据描述符 __set__ 被调用（值: {value}）")


class NonDataDescriptor:
    """非数据描述符：只有 __get__"""

    def __get__(self, obj, objtype=None):
        return "非数据描述符的值"


class DescriptorPriority:
    """演示描述符优先级"""
    data_desc = DataDescriptor()
    non_data_desc = NonDataDescriptor()
    normal_attr = "普通类属性"


def demo_descriptor_priority() -> None:
    """演示数据描述符 vs 非数据描述符的优先级"""
    print("\n" + "=" * 60)
    print("示例 4：数据描述符 vs 非数据描述符（优先级）")
    print("=" * 60)

    obj = DescriptorPriority()

    # 数据描述符：优先级高于实例字典
    print("数据描述符测试：")
    print(f"  访问 data_desc: {obj.data_desc}")
    obj.data_desc = "尝试覆盖"  # 触发 __set__
    print(f"  再次访问 data_desc: {obj.data_desc}")  # 仍是描述符值

    # 非数据描述符：优先级低于实例字典
    print("\n非数据描述符测试：")
    print(f"  访问 non_data_desc: {obj.non_data_desc}")
    obj.__dict__["non_data_desc"] = "实例字典覆盖"  # 直接操作实例字典
    print(f"  被实例字典覆盖: {obj.non_data_desc}")  # 返回实例字典的值

    # 普通属性
    print("\n普通属性测试：")
    print(f"  访问 normal_attr: {obj.normal_attr}")
    obj.normal_attr = "修改后的值"
    print(f"  修改后: {obj.normal_attr}")


# ============================================================
# 5. property 就是描述符
# ============================================================

class ProductWithProperty:
    """用 property 实现验证（对比 ValidatedField 描述符）"""

    def __init__(self, price: float):
        self.price = price  # 通过 setter 验证

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float):
        if value < 0:
            raise ValueError(f"价格不能为负（实际值: {value}）")
        self._price = value


def demo_property_is_descriptor() -> None:
    """演示 property 就是描述符"""
    print("\n" + "=" * 60)
    print("示例 5：property 就是描述符")
    print("=" * 60)

    p = ProductWithProperty(999.0)
    print(f"商品价格: {p.price}")

    # property 本质是数据描述符
    print(f"\nproperty 类型: {type(ProductWithProperty.price)}")
    print(f"有 __get__: {hasattr(ProductWithProperty.price, '__get__')}")
    print(f"有 __set__: {hasattr(ProductWithProperty.price, '__set__')}")

    print("\n尝试设置负价格：")
    try:
        p.price = -100
    except ValueError as e:
        print(f"  ❌ {e}")


# ============================================================
# 6. 综合应用 - 电商模型验证系统
# ============================================================

class RangeField:
    """范围验证描述符"""

    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_range_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"{self.name} 不能小于 {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"{self.name} 不能大于 {self.max_val}")
        setattr(obj, self.private_name, value)


class ChoiceField:
    """选项验证描述符"""

    def __init__(self, choices):
        self.choices = choices

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_choice_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        if value not in self.choices:
            raise ValueError(f"{self.name} 必须是 {self.choices} 之一")
        setattr(obj, self.private_name, value)


class EcommerceProduct:
    """电商商品模型 - 综合描述符验证"""

    price = RangeField(min_val=0.01, max_val=1_000_000)
    stock = RangeField(min_val=0, max_val=100_000)
    status = ChoiceField(choices=["draft", "active", "inactive", "deleted"])
    category = ChoiceField(choices=["电子产品", "服装", "食品", "图书", "其他"])

    def __init__(self, id: int, name: str, price: float, stock: int,
                 status: str, category: str):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.status = status
        self.category = category

    def __repr__(self):
        return (f"EcommerceProduct(id={self.id}, name={self.name!r}, "
                f"price={self.price}, stock={self.stock}, "
                f"status={self.status!r}, category={self.category!r})")


def demo_ecommerce_validation() -> None:
    """演示综合电商模型验证"""
    print("\n" + "=" * 60)
    print("示例 6：综合电商模型验证系统")
    print("=" * 60)

    # 合法商品
    print("创建合法商品：")
    p = EcommerceProduct(
        id=1, name="iPhone 15 Pro", price=9999.0,
        stock=50, status="active", category="电子产品"
    )
    print(f"  {p}")

    # 各种验证失败
    print("\n测试各种验证失败：")

    for desc, kwargs in [
        ("价格过低", {"id": 2, "name": "T", "price": 0.005, "stock": 1, "status": "active", "category": "食品"}),
        ("价格过高", {"id": 3, "name": "T", "price": 2_000_000, "stock": 1, "status": "active", "category": "食品"}),
        ("库存为负", {"id": 4, "name": "T", "price": 100, "stock": -1, "status": "active", "category": "食品"}),
        ("非法状态", {"id": 5, "name": "T", "price": 100, "stock": 1, "status": "xxx", "category": "食品"}),
        ("非法类目", {"id": 6, "name": "T", "price": 100, "stock": 1, "status": "active", "category": "武器"}),
    ]:
        try:
            EcommerceProduct(**kwargs)
            print(f"  {desc}: 未触发验证 ❌")
        except ValueError as e:
            print(f"  {desc}: {e} ✅")


def main() -> None:
    """主函数"""
    demo_simple_descriptor()
    demo_validated_field()
    demo_cached_field()
    demo_descriptor_priority()
    demo_property_is_descriptor()
    demo_ecommerce_validation()
    print("\n" + "=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
