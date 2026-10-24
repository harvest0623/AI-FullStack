# Day01 代码说明

## 运行方式

```bash
cd "Ollama/Day01 - Ollama概述与快速体验/Code"

python 01_what_is_ollama.py    # Ollama 定位与架构
python 02_install_check.py     # 环境诊断
python 03_quick_chat.py        # 第一段对话（双模式）
```

无 Ollama 环境也能运行 —— 自动走 `SimOllama` 模拟。

## 文件说明

| 文件 | 内容 | 关键概念 |
|------|------|---------|
| `ollama_util.py` | 共享工具：`_server_alive` 探测、`list_local_models`、`is_ollama_available`、`SimOllama` 模拟器、`chat_wrapper`/`embed_wrapper` 封装 | 双模式骨架 |
| `01_what_is_ollama.py` | 三层架构图、三种使用方式、常见开源模型清单 | Ollama 定位 |
| `02_install_check.py` | 探测服务存活/版本/本地模型，输出环境诊断报告 | 环境就绪 |
| `03_quick_chat.py` | 双模式对话 + `chat_wrapper` 演示（verbose 显示模式） | 第一条对话 |

## 观察要点

**ollama_util.py**（后续每天都会用到）
- `_server_alive` / `list_local_models` 用标准库 `urllib` 探测 127.0.0.1:11434
- `is_ollama_available(model)`：服务存活 **且** 模型已拉取才返回 True
- `SimOllama`：`chat/generate/embed` 三个方法都是规则模拟，接口对齐真实 Ollama
- `chat_wrapper(model, messages, options, verbose=True)`：推荐入口，自动切模式

**02_install_check.py**
- 输出现状诊断：服务是否存活、有几个本地模型、结论建议
- 完全无副作用，实时探测你的真实环境

**03_quick_chat.py**
- 同一段对话，两种路径（真实 / 模拟）——理解"照搬就能跑"的骨架

## 切到真实模式的步骤

```bash
# 1. 启动服务
ollama serve
# 2. 拉模型（本天用到 llama3.1）
ollama pull llama3.1
# 3. 再运行 03_quick_chat.py -> 显示真实模型输出
```