# Day09 - Code 代码目录说明

本目录提供 Day09（综合实战与最佳实践）的代码。所有脚本**离线可运行**。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_best_practice.py` | 讲解脚本 | 工具描述规范、安全、降级 |
| `02_production_check.py` | 讲解脚本 | 上线自检清单 |
| `app_assistant.py` | 综合演示 | 多工具小助手（天气/计算/记账） |
| `README.md` | 说明 | 本目录说明 |

## 运行方式

```bash
python 01_best_practice.py
python 02_production_check.py
python app_assistant.py
```

## 说明

- `app_assistant.py` 用规则决策替身真实模型，示范"循环 + 注册 + 安全执行"的多工具闭环
- `calculate` 用受控白名单 + 受限 eval 演示安全；真实生产请用解析器避免 eval
- 换真实模型时，仅把 `decide` 替换为 LLM tool calling，其余结构复用