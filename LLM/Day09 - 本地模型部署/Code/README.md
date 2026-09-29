# Day09 Code - 本地模型部署实践

本目录提供 LLM 本地部署的完整工具链代码，覆盖 Ollama、vLLM、llama.cpp 三大方案，以及模型量化与本地 vs API 对比。所有脚本均可独立运行，配合 AISearch 智能问答服务项目使用。

## 环境准备

### 1. 安装 Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows：从 https://ollama.com/download 下载安装包
```

启动服务并拉取模型：

```bash
# 启动 Ollama 服务（默认监听 11434 端口）
ollama serve

# 拉取模型
ollama pull qwen2.5:7b

# 验证
ollama list
```

### 2. 安装 vLLM

```bash
pip install vllm
# 启动服务
vllm serve --model Qwen/Qwen2-7B-Instruct --port 8000
```

### 3. 安装 Python 依赖

```bash
pip install openai requests
```

## 文件说明

| 文件 | 说明 | 运行命令 |
| --- | --- | --- |
| `01_ollama_demo.py` | Ollama 客户端封装，支持对话/流式/多模型对比 | `python 01_ollama_demo.py` |
| `02_vllm_server.py` | vLLM 部署配置生成与性能基准测试 | `python 02_vllm_server.py` |
| `03_local_vs_api.py` | 本地模型与 API 性能/成本对比 | `python 03_local_vs_api.py` |
| `04_quantization_guide.py` | 量化方案推荐与 Modelfile 生成（纯标准库） | `python 04_quantization_guide.py` |

## 量化选择决策表

| 显存 | 推荐模型 | 推荐量化 | 说明 |
| --- | --- | --- | --- |
| 4 GB | qwen2.5:1.5b | INT4 (Q4_K_M) | 入门体验 |
| 8 GB | qwen2.5:7b | INT4 (Q4_K_M) | 消费级显卡主力 |
| 16 GB | qwen2.5:7b | FP16 | 质量优先 |
| 24 GB | qwen2.5:14b | INT4 / INT8 | 中端生产力 |
| 48 GB+ | qwen2.5:32b | INT4 | 专业场景 |
| 80 GB+ | qwen2.5:72b | INT4 | 旗舰开源 |

## Docker 部署配置

### Ollama Docker

```yaml
# docker-compose.ollama.yml
version: "3.9"
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped
volumes:
  ollama_data:
```

### vLLM Docker

参见 `02_vllm_server.py` 中 `generate_docker_config()` 方法生成的配置。

## 安全配置指南

### 1. 服务监听地址

```bash
# 仅本机访问（推荐）
OLLAMA_HOST=127.0.0.1:11434 ollama serve

# 切勿使用 0.0.0.0 暴露到公网，除非有反向代理 + 认证
```

### 2. 模型文件完整性校验

```bash
# 下载后校验 SHA256
sha256sum model.gguf
# 与官方发布的校验值比对
```

### 3. 反向代理 + 认证（Nginx 示例）

```nginx
server {
    listen 443 ssl;
    server_name llm.internal;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        # 基础认证
        auth_basic "LLM Service";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. 审计日志

建议在应用层记录每次 LLM 调用：

- 请求时间戳
- 用户 ID
- 模型名称
- 输入 Token 数
- 输出 Token 数
- 响应延迟
- 请求状态

## 硬件配置建议

| 用途 | GPU | 显存 | 适用模型 |
| --- | --- | --- | --- |
| 个人开发 | RTX 4060 | 8 GB | 7B INT4 |
| 日常生产 | RTX 4090 | 24 GB | 7B FP16 / 13B INT4 |
| 团队服务 | A100 40G | 40 GB | 13B FP16 / 32B INT4 |
| 企业级 | 2×A100 80G | 160 GB | 70B INT4 |

## 常见问题

**Q: Ollama 服务无法连接？**
确认 `ollama serve` 已启动，端口 11434 未被占用，防火墙放行。

**Q: vLLM 启动报显存不足？**
降低 `--gpu-memory-utilization`（如 0.85），或减小 `--max-model-len`，或使用量化模型。

**Q: 本地模型回答质量不如 API？**
属于正常现象。可尝试：使用更大参数模型、提高量化精度（INT8/FP16）、优化 Prompt、或进行微调。
