# Day09 - 本地模型部署

将大语言模型从云端 API 搬到本地运行，是企业级 LLM 应用落地的关键一步。本地部署让 LLM 摆脱对第三方 API 的依赖，实现数据不出域、成本可控、离线可用，同时为后续的微调与定制化提供基础。本章围绕 Ollama、vLLM、llama.cpp 三大主流部署方案，结合模型量化技术，讲解如何在本地环境高效部署 LLM，并通过 AISearch 智能问答服务项目串联实践。

## 学习目标

- 理解本地部署 LLM 的核心需求场景与适用条件
- 掌握 Ollama 的安装、模型管理与 API 调用方式
- 掌握 vLLM 的高吞吐量推理服务部署
- 了解 llama.cpp 在边缘设备与纯 CPU 环境下的应用
- 理解模型量化原理（GGUF/AWQ/GPTQ）及其对质量的影响
- 学会根据硬件条件选择合适的模型与量化方案
- 能够对比本地部署与 API 调用的成本、性能与质量差异

## 理论知识讲解

### 一、本地部署的需求场景

并非所有 LLM 应用都适合走 API 路线，以下五类场景是本地部署的典型刚需：

| 场景 | 说明 | 典型行业 |
| --- | --- | --- |
| 数据隐私 | 敏感数据不能出域，需在本地完成推理 | 医疗、金融、法律 |
| 成本控制 | 高频调用时本地一次性投入低于 API 按量付费 | 客服、批量处理 |
| 离线环境 | 无网络或网络不稳定，必须本地运行 | 制造、户外、保密网络 |
| 定制化 | 需要微调模型或修改推理参数 | 垂直领域专用模型 |
| 合规要求 | 数据本地化法规强制要求数据不得出境 | 政府、跨国企业中国区 |

### 二、Ollama

Ollama 是目前最易用的本地 LLM 运行工具，开箱即用，适合开发、测试和轻量级生产环境。

**安装（Linux/macOS）：**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Windows 用户可直接从官网下载安装包。

**模型管理：**

```bash
# 拉取模型
ollama pull qwen2.5:7b

# 查看已安装模型
ollama list

# 删除模型
ollama rm qwen2.5:7b

# 查看模型详情
ollama show qwen2.5:7b
```

**运行模型：**

```bash
ollama run qwen2.5:7b
ollama run llama3.1:8b
```

**API 服务：**

Ollama 启动后默认监听 `11434` 端口，并兼容 OpenAI API 格式，可直接用 `openai` SDK 调用：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "你好"}],
)
print(response.choices[0].message.content)
```

**模型库：** 官方维护的模型仓库位于 [ollama.com/library](https://ollama.com/library)，支持 Qwen、LLaMA、Mistral、Phi 等主流模型。

**Modelfile 自定义模型：**

```
FROM qwen2.5:7b

# 对话模板
TEMPLATE """{{ .System }}
USER: {{ .Prompt }}
ASSISTANT:"""

# 推理参数
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

# 系统提示词
SYSTEM """你是一个专业的中文智能问答助手。"""
```

### 三、vLLM

vLLM 是面向生产环境的高吞吐量推理引擎，适合高并发场景。

**定位：** 生产级推理服务，吞吐量可达原生 Transformers 的 10 倍以上。

**核心技术：**

- **PagedAttention：** 借鉴操作系统虚拟内存管理思想，将 KV Cache 分页存储，显著减少显存碎片，提升显存利用率。
- **连续批处理 Continuous Batching：** 动态将新请求加入当前批次，已完成请求立即返回，避免传统静态批处理中"等待最慢请求"的浪费。

**安装：**

```bash
pip install vllm
```

**启动服务：**

```bash
vllm serve --model Qwen/Qwen2-7B-Instruct --port 8000
```

**API 兼容：** 同样兼容 OpenAI API 格式，`base_url` 指向 `http://localhost:8000/v1` 即可。

**适用场景：** 高并发生产环境、需要同时处理大量请求的在线服务。

### 四、llama.cpp

llama.cpp 是轻量级 C++ 推理引擎，主打纯 CPU 推理与低资源消耗。

**特点：**

- 纯 C++ 实现，无重型依赖
- 支持 GGUF 量化格式，显存/内存占用极低
- 可在无 GPU 环境下运行

**适用场景：** 边缘设备、嵌入式系统、无 GPU 的服务器、个人电脑本地体验。

**安装：** 可从源码编译，或直接下载预编译版本（GitHub Releases）。

### 五、模型量化

量化是将模型权重从高精度浮点（FP16）降为低精度整数（INT8/INT4）的技术，是本地部署的关键使能技术。

**量化原理：**

```
原始权重 (FP16, 2字节)  →  量化权重 (INT4, 0.5字节)
显存占用减少 75%，推理速度提升，精度略降
```

**主流量化格式：**

| 格式 | 全称 | 特点 | 适用工具 |
| --- | --- | --- | --- |
| GGUF | GPT-Generated Unified Format | llama.cpp 专用，支持 Q4_K_M/Q5_K_M/Q8_0 等多级别 | llama.cpp / Ollama |
| AWQ | Activation-aware Weight Quantization | 基于激活值感知，精度损失小 | vLLM / Transformers |
| GPTQ | Generalized Post-Training Quantization | 训练后量化，社区支持广泛 | vLLM / Transformers |

**INT4 vs INT8 vs FP16 对比：**

| 精度 | 7B 模型显存 | 推理速度 | 质量损失 | 适用场景 |
| --- | --- | --- | --- | --- |
| FP16 | ~14 GB | 基准 | 无 | 质量优先、显存充足 |
| INT8 | ~7 GB | 提升 1.5x | 几乎无损 | 平衡场景 |
| INT4 | ~4 GB | 提升 2x | 略降（约 1-2%） | 显存受限、追求吞吐 |

### 六、硬件需求

**GPU 显存计算公式：**

```
显存 ≈ 参数量 × 每参数字节数
例如：7B 模型 FP16 ≈ 7 × 2 = 14 GB
     7B 模型 INT4 ≈ 7 × 0.5 = 3.5 GB
```

**推荐硬件配置表：**

| 模型规模 | 精度 | 最低显存 | 推荐显存 | 推荐 GPU |
| --- | --- | --- | --- | --- |
| 7B | INT4 | 4 GB | 8 GB | RTX 3060 / 4060 |
| 7B | FP16 | 14 GB | 16 GB | RTX 4080 / 4090 |
| 13B | INT4 | 8 GB | 12 GB | RTX 4070 Ti |
| 13B | FP16 | 26 GB | 32 GB | RTX 4090 / A100 |
| 70B | INT4 | 40 GB | 80 GB | 2×A100 80G |
| 70B | FP16 | 140 GB | 160 GB | 2×H100 80G |

**CPU 推理：** 内存足够（参数量 × 字节数 + 2GB 余量）时，可用 llama.cpp 跑 CPU 推理，速度较慢但可用。

**多 GPU 并行：**

- **张量并行 Tensor Parallel：** 将单层权重切分到多卡，通信开销大但延迟低
- **流水线并行 Pipeline Parallel：** 将不同层分配到不同卡，通信开销小但存在气泡

### 七、模型下载与管理

| 来源 | 命令 | 特点 |
| --- | --- | --- |
| HuggingFace Hub | `huggingface-cli download Qwen/Qwen2-7B-Instruct` | 模型最全，国内访问慢 |
| ModelScope（国内镜像） | `modelscope download --model Qwen/Qwen2-7B-Instruct` | 国内速度快，魔搭社区 |
| Ollama Library | `ollama pull qwen2.5:7b` | 最简单，自动量化 |

**国内加速镜像设置：**

```bash
# HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download Qwen/Qwen2-7B-Instruct
```

### 八、本地模型 vs API 对比

| 维度 | 本地部署 | API 调用 |
| --- | --- | --- |
| 成本 | 一次性硬件投入，边际成本趋近 0 | 按量付费，高频调用成本高 |
| 性能 | 受本地硬件限制，延迟波动大 | 通常更快更稳定 |
| 质量 | 受开源模型能力限制 | 闭源旗舰模型通常更强 |
| 灵活性 | 可微调、可改推理参数、可定制 | 受服务商限制 |
| 数据安全 | 数据不出域，最安全 | 数据需传给服务商 |
| 运维 | 需自行维护硬件与服务 | 服务商托管，零运维 |

### 九、本地部署安全考量

- **模型文件完整性验证：** 下载后校验 SHA256，防止模型被篡改
- **推理服务网络安全：** 监听 `127.0.0.1` 而非 `0.0.0.0`，不暴露公网
- **日志与审计：** 记录所有推理请求，便于追溯

## 代码文件说明

| 文件 | 用途 |
| --- | --- |
| `Code/01_ollama_demo.py` | Ollama 本地调用演示，封装 OllamaClient 类，支持对话、流式、多模型切换、模型管理 |
| `Code/02_vllm_server.py` | vLLM 服务部署管理器，生成启动命令、Docker 配置，含性能测试脚本 |
| `Code/03_local_vs_api.py` | 本地模型与 API 性能对比工具，测量延迟、吞吐量、质量、成本 |
| `Code/04_quantization_guide.py` | 模型量化指南工具，根据显存推荐量化级别，含显存计算器与 Modelfile 生成器 |
| `Code/README.md` | 本地部署完整指南，含安装步骤、量化决策表、Docker 配置、安全配置 |

## 关键知识点总结

### 1. 部署工具对比

| 工具 | 定位 | 易用性 | 性能 | 适用场景 |
| --- | --- | --- | --- | --- |
| Ollama | 开箱即用本地运行 | ★★★★★ | ★★★ | 开发测试、轻量生产 |
| vLLM | 高吞吐推理引擎 | ★★★ | ★★★★★ | 高并发生产环境 |
| llama.cpp | 轻量 CPU 推理 | ★★★ | ★★ | 边缘设备、无 GPU |

### 2. 量化格式对比

| 格式 | 最小量化 | 推荐量化 | 工具支持 |
| --- | --- | --- | --- |
| GGUF | Q4_0 | Q4_K_M | Ollama / llama.cpp |
| AWQ | INT4 | INT4 | vLLM / Transformers |
| GPTQ | INT4 | INT4 | vLLM / Transformers |

### 3. 硬件配置需求

| 模型 | INT4 最低 | FP16 推荐 | 备注 |
| --- | --- | --- | --- |
| 7B | 4 GB | 16 GB | 消费级显卡可跑 |
| 13B | 8 GB | 32 GB | 中高端显卡 |
| 70B | 40 GB | 160 GB | 企业级多卡 |

### 4. 本地 vs API 对比

| 场景 | 推荐 |
| --- | --- |
| 数据敏感 | 本地 |
| 高频调用且预算固定 | 本地 |
| 追求最强质量 | API |
| 快速验证原型 | API |
| 离线环境 | 本地 |

### 5. Ollama / vLLM 命令速查

```bash
# Ollama
ollama pull <model>          # 拉取模型
ollama run <model>           # 运行模型
ollama list                  # 列出模型
ollama rm <model>            # 删除模型
ollama serve                 # 启动 API 服务（默认 11434）

# vLLM
vllm serve --model <model> --port 8000
# 张量并行
vllm serve --model <model> --tensor-parallel-size 2
# 量化模型
vllm serve --model <model> --quantization awq
```

## 实战练习

### 练习一：搭建多模型本地问答服务

使用 Ollama 拉取 `qwen2.5:7b` 和 `llama3.1:8b` 两个模型，编写一个脚本，根据用户问题复杂度自动路由到不同模型（简单问题用小模型，复杂问题用大模型），并对比两个模型的响应。

### 练习二：量化模型质量对比

分别用 FP16 和 INT4 量化的同一模型回答 20 道常识题，人工评分并统计质量损失百分比，验证"INT4 几乎无损"的结论。

### 练习三：本地 vs API 成本测算

假设一个客服场景每天 10000 次调用，每次平均 500 token 输入 + 200 token 输出，分别计算使用 GPT-4o API 和本地 7B 模型（初始硬件投入 10000 元）的月成本，找出盈亏平衡点。
