# Day01 - Ollama概述与快速体验

## 今日目标

Ollama 一句话概括：**在本地运行大模型的一条命令**。今天从零开始——搞懂它是什么、解决什么问题、如何安装，然后跑出你的第一条本地对话。

学完今天，你将能够：

1. 讲清 Ollama 的定位、架构与价值（数据不出本地、免费、离线）
2. 在本机安装并启动 Ollama（Win/macOS/Linux）
3. 用 `ollama run` 完成交互式对话，理解模型选择思路
4. 掌握本板块统一的"真实/模拟双模式"代码骨架

---

## 一、Ollama 是什么

Ollama 是一个让本地机器方便地运行开源大模型（LLM）和嵌入模型（Embedding）的工具：

- **一条命令安装模型**：`ollama pull llama3.1`
- **一条命令跑起来**：`ollama run llama3.1`
- **一个 HTTP 服务**：默认监听 `127.0.0.1:11434`，提供 REST API
- **OpenAI 兼容**：可用 `/v1/chat/completions`，无缝替换云 API

### 1.1 它解决什么问题

| 痛点 | Ollama 的解法 |
|------|--------------|
| 云 API 按量付费 | 本地免费跑（耗自己算力） |
| 数据出本地有隐私风险 | 模型本地，数据不出走 |
| 需要联网 | 完全离线可用 |
| 切换模型麻烦 | `ollama pull` 换一个标签即可 |

### 1.2 架构

```
┌───────────┐   CLI / REST API / SDK    ┌───────────────┐
│ Client    │ ────────────────────────▶ │ Ollama Server │
│ (app/库)  │  HTTP (127.0.0.1:11434)   │  (服务进程)    │
└───────────┘                           └───────┬───────┘
                                                │ 加载/推理
                                       ┌────────▼────────┐
                                       │  模型仓库 Model │
                                       │  ~/.ollama/...  │
                                       └─────────────────┘
```

- **Client**：CLI（`ollama` 命令）、REST API 客户端、Python SDK（`ollama`）
- **Server**：常驻服务进程，负责模型加载、推理调度
- **Model Store**：模型文件存在本机 `~/.ollama/models` 下

### 1.3 三个角色分工

```
我们这三类使用方式，对应三种"间接程度"：
  CLI 命令行        ollama run llama3.1      ← 人类手动交互
  HTTP API         requests -> /api/chat     ← 程序调用（Day03）
  Python SDK       ollama.chat()             ← 极简封装（Day04）
```

---

## 二、安装与启动

### 2.1 各平台安装

```bash
# macOS / Windows：下载安装包（含 GUI 与命令行）
# 官网: https://ollama.com/download

# Linux：
curl -fsSL https://ollama.com/install.sh | sh
```

### 2.2 启动服务

```bash
ollama serve     # 前台启动，默认 127.0.0.1:11434

# Windows/macOS 桌面版通常已自动启动，可通过验证：
ollama list      # 能列出（可能为空）即服务正常
```

### 2.3 拉取并运行第一个模型

```bash
# 拉取（约 4.7GB，视网络而定）
ollama pull llama3.1

# 交互式对话
ollama run llama3.1 "你好，请做一句自我介绍"
```

> 如果存储或性能受限，可换小模型：`qwen2.5:3b`（约 2GB）或 `tinyllama`（约 637MB）。

---

## 三、模型选择思路

第一次体验不必纠结，几个原则：

1. **先小后大**：先用 3B/7B 级别跑通流程，再试更大模型
2. **按场景选**：对话用通用模型，中文用 qwen2.5，代码用 codellama
3. **看硬件**：大致按"参数量 × 量化比特"估算所需显存
4. **嵌入另算**：嵌入模型很小（~300MB），做 RAG 必备

| 模型 | 大小 | 用途 |
|------|------|------|
| `llama3.1` | 4.7GB | 通用英文对话 |
| `qwen2.5:7b` | 4.7GB | 通用中文对话 |
| `qwen2.5:3b` | 1.9GB | 轻量中文对话 |
| `nomic-embed-text` | 274MB | 文本嵌入（Day07） |
| `llava` | 4.7GB | 视觉问答 |

---

## 四、双模式代码骨架（贯穿全板块）

本板块所有代码采用统一的**真实/模拟双模式**：

```python
# 核心逻辑：检测到 Ollama 服务且有模型 -> 走真实 API；
#             否则 -> 使用内置 SimOllama 模拟响应。
if is_ollama_available(model):
    result = real_api_call(model, prompt)   # 真实模型输出
else:
    result = SimOllama.chat(model, prompt) # 规则模拟，离线可跑
```

- **有环境**：看到真实模型行为，代码完全可用
- **无环境**：代码逻辑照常运行，不抛异常，便于理解 API 结构

对应代码：`Code/02_install_check.py`（检测）、`Code/03_quick_chat.py`（双模式对话）

---

## 五、今日核心要点

```
1. Ollama = 本地跑大模型的工具：一条命令安装 + 运行
2. 三大价值：免费、数据不出本地、离线可用
3. 架构：Client(CLI/API/SDK) -> Server -> 模型仓库
4. 启动：ollama serve，默认 127.0.0.1:11434
5. 使用 <-> OpenAI 兼容，/v1 端点可无缝替换云 API
6. 双模式骨架：有 Ollama 走真实，没有走 SimOllama
```

---

## 六、代码文件说明

| 文件 | 内容 | 关键知识点 |
|------|------|-----------|
| `01_what_is_ollama.py` | 架构示意图、托管模型清单、使用方式对比 | Ollama 定位 |
| `02_install_check.py` | 检测服务/版本/本地模型，输出环境诊断报告 | 环境就绪 |
| `03_quick_chat.py` | 双模式对话：真实 API 与 SimOllama 自动切换 | 双模式骨架 |

`ollama_util.py` 提供共享工具：`is_ollama_available()` 检测、`SimOllama` 模拟器。

---

## 七、延伸思考

1. 为什么 Ollama 的模型文件不放在程序安装目录，而是 `~/.ollama/models`？
2. "数据不出本地"在哪些场景价值最大？（隐私、合规、涉密）
3. 本地跑模型的瓶颈通常是显存。一个 7B 模型、4-bit 量化大约需要多少显存？
4. 双模式设计对你的开发调试有什么好处？

---

## 八、明日预告

Day02 学习 **模型管理与拉取**：`pull/push/rm/list/cp/show` 全套命令，查看模型参数量与元信息，封装一个模型管理器，理解模型的磁盘占用与清理。