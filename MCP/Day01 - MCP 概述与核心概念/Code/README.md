# Day01 - Code 代码目录说明

本目录提供 Day01（MCP 概述与核心概念）的全部代码与说明。所有讲解脚本**离线可运行**，无需安装 `mcp` 包。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_what_is_mcp.py` | 讲解脚本 | 介绍 MCP 定位与解决的核心痛点 |
| `02_roles.py` | 讲解脚本 | Host / Client / Server 三角色详解与关系 |
| `03_compare.py` | 讲解脚本 | MCP vs 普通 API / Function Calling / Agent |
| `mcp_check.py` | 工具脚本 | 检测本机 MCP 环境（后面各 Day 复用） |

## 运行方式

```bash
# 概念讲解（无需安装任何依赖）
python 01_what_is_mcp.py
python 02_roles.py
python 03_compare.py

# 环境检测
python mcp_check.py
```

## 说明

- 讲解脚本输出均为中文字符，控制台请使用 UTF-8 编码
- `mcp_check.py` 检测的 `mcp` SDK 主要用于 Day04 之后真实的 Server/Client 模板