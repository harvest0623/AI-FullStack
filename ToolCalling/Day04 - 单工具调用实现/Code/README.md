# Day04 - Code 代码目录说明

本目录提供 Day04（单工具调用实现）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_single_call.py` | 讲解+演示 | 模拟模型完整跑通一次工具调用闭环 |
| `02_real_shape.py` | 讲解脚本 | OpenAI 风格请求/返回形态示意 |
| `03_parse_arguments.py` | 工具函数 | 参数安全解析 + 必填/类型校验 |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_single_call.py
python 02_real_shape.py
python 03_parse_arguments.py
```

## 说明

- `01_single_call.py` 的模拟模型仅用于离线演示"应用侧执行与回填"逻辑；真实时换成任意支持 tool calling 的端点
- `03_parse_arguments.py` 的解析/校验函数是后续多工具、循环的最佳复用件