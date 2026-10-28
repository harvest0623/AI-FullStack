# Code 说明

本目录为「Day10 - 综合实战与部署」的可执行代码。

- 01_gpu_check.py     GPU / 硬件检测
- 02_full_agent.py    综合客服实战（对话+记忆+RAG+工具）
- 03_service.py       HTTP 服务化（/chat 接口）
- 04_perf_bench.py    性能基准（延迟/QPS）
- ollama_util.py      双模式共用（综合版）

运行方式：

```bash
python 01_gpu_check.py
python 02_full_agent.py
python 03_service.py        # 本地 HTTP 服务，Ctrl+C 停止
python 04_perf_bench.py
```

> 全离线可运行；有 Ollama 自动切真实调用，增强真实体验。