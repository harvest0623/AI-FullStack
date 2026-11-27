# Day01 - LlamaIndex 概述与环境搭建 / 代码说明

本章代码位于 `Code/` 目录，均在 **Python 3.10+** 下可直接运行。运行前先安装依赖并在 `.env` 中配置 API Key。

## 环境准备

```bash
# 1. 创建虚拟环境（可选但推荐）
python -m venv .venv
# Windows: .venv\Scripts\activate   |  Linux/macOS: source .venv/bin/activate

# 2. 安装依赖
pip install llama-index llama-index-readers-file llama-index-readers-web \
            python-dotenv pydantic

# 3. 配置 API Key（复制 .env.example 为 .env 并填写）
```

## 文件说明

| 文件 | 说明 | 是否需联网 |
|------|------|-----------|
| `01_hello_llama.py` | 第一个 LlamaIndex 程序：Load → Index → Query 三步走 | 需要 Key（无 Key 自动降级） |
| `02_environment_setup.py` | 环境检查工具：检查 Python/llama_index/集成包/API Key，并生成 `requirements.txt` 与 `.env.example` | 否 |
| `03_settings.py` | Settings 全局配置：统一配置 llm / embed_model / node_parser / show_progress，并做切分演示 | node_parser 离线可用 |

## 运行方式

```bash
# 环境检查（最推荐先运行）
python 02_environment_setup.py

# 全局配置演示（离线可跑）
python 03_settings.py

# 第一个程序（配置 Key 后有完整问答体验）
python 01_hello_llama.py
```

## 运行后生成的文件

- `requirements.txt`：依赖清单（由 `02` 生成）
- `.env.example`：API Key 模板（由 `02` 生成，复制为 `.env` 使用）
- `data/company_intro.txt`：示例企业文档（由 `01` 自动生成）