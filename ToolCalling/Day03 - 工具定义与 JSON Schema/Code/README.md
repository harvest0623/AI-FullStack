# Day03 - Code 代码目录说明

本目录提供 Day03（工具定义与 JSON Schema）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_schema_basics.py` | 讲解+演示 | JSON Schema 常用关键字示例 |
| `02_description_matters.py` | 讲解+演示 | description 对调用准确度的影响 |
| `03_signature_to_schema.py` | 讲解+工具 | 从函数签名+注解+docstring 生成工具 schema |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_schema_basics.py
python 02_description_matters.py
python 03_signature_to_schema.py
```

## 说明

- `03_signature_to_schema.py` 提供了一个简化的 schema 生成函数，是后续把 Python 函数注册成工具的雏形
- 本日聚焦"如何定义工具"；下一日起开始把它们接进调用闭环