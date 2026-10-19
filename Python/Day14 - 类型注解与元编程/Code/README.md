# Day14 代码文件说明

本目录包含 Day14 类型注解与元编程的 4 个 Python 演示脚本，所有代码围绕电商场景 `eshop` 展开。

## 文件清单

| 文件 | 内容 | 主要特性 |
|------|------|---------|
| `type_hints.py` | 类型注解基础 | 基本注解 / 函数注解 / 复合类型 / Optional / Union / Literal |
| `typing_advanced.py` | 高级类型 | TypeVar / Generic / Protocol / Callable / TypedDict / NewType |
| `metaclass_demo.py` | 元类练习 | type 动态创建 / 自定义元类 / __init_subclass__ / __class_getitem__ |
| `descriptor_demo.py` | 描述符练习 | __get__ / __set__ / __delete__ / 数据描述符 / 非数据描述符 |

## 运行方式

```bash
# 运行代码示例
python type_hints.py
python typing_advanced.py
python metaclass_demo.py
python descriptor_demo.py

# 用 mypy 进行静态类型检查（需先 pip install mypy）
mypy type_hints.py --strict
mypy typing_advanced.py --strict
```

## 各文件演示内容

### type_hints.py

- 示例 1：基本类型注解（int / str / float / bool）
- 示例 2：复合类型注解（list / dict / tuple / set）
- 示例 3：Optional 与 Union（`|` 语法）
- 示例 4：Literal 字面量类型限定
- 示例 5：dataclass 电商数据模型（Product / OrderItem / Order）
- 示例 6：带类型注解的函数

### typing_advanced.py

- 示例 1：TypeVar 泛型类型变量（无约束 / 约束 / bound）
- 示例 2：Generic 泛型 Repository[T]
- 示例 3：Protocol 结构子类型（Identifiable / ReadOnlyRepository）
- 示例 4：Callable 可调用类型（回调函数）
- 示例 5：TypedDict API 响应（ProductResponse / OrderResponse / PaginatedResponse）
- 示例 6：NewType 新类型（ProductId / CustomerId 防混淆）

### metaclass_demo.py

- 示例 1：type() 的两面性（查看类型 + 动态创建类）
- 示例 2：动态创建电商模型类
- 示例 3：模型注册元类（自动注册所有 Model 子类）
- 示例 4：元类方法调用顺序（__new__ / __init__ / __call__）
- 示例 5：__init_subclass__ 替代元类（插件注册）
- 示例 6：__class_getitem__ 类参数化

### descriptor_demo.py

- 示例 1：描述符基础（__get__ / __set__ / __delete__ / __set_name__）
- 示例 2：ValidatedField 验证商品价格非负
- 示例 3：CachedField 缓存计算结果（订单总金额）
- 示例 4：数据描述符 vs 非数据描述符（优先级对比）
- 示例 5：property 就是描述符
- 示例 6：综合电商模型验证系统（RangeField + ChoiceField）

## 环境要求

- Python 3.10+（使用了 `|` 联合类型语法）
- 仅使用标准库，无需额外安装依赖
- 可选：`pip install mypy` 进行静态类型检查

## 类型检查

```bash
# 安装 mypy
pip install mypy

# 严格模式检查（会检查所有类型注解）
mypy type_hints.py --strict
mypy typing_advanced.py --strict

# metaclass_demo.py 和 descriptor_demo.py 主要演示运行时行为，
# 类型注解相对宽松
```
