# Day02 代码说明

## 运行方式

```bash
cd "Ollama/Day02 - 模型管理与拉取/Code"

python 01_pull_list.py        # pull/list 流程与命名规则
python 02_model_detail.py     # 模型元信息
python 03_model_manager.py    # 模型管理器封装
```

**注意**：本目录的 .py 依赖同目录 `ollama_util.py`（与 Day01 相同）。已有真实 Ollama 环境则自动走真实 API。

## 文件说明

| 文件 | 内容 | 关键概念 |
|------|------|---------|
| `01_pull_list.py` | 本地列表、pull 流程（模拟进度）、命名规则 | 模型生命周期 |
| `02_model_detail.py` | `/api/show` 字段解析、参数量/量化/内存换算 | 元信息 |
| `03_model_manager.py` | `ModelManager` 类：list/search/show/disk_summary/remove | 管理器封装 |

## 观察要点

**01_pull_list.py**
- `is_ollama_available("llama3.1")`：有环境出真实列表，无则用示例数据
- pull 流程以"阶段+百分比"模拟分片下载，理解 `manifest -> layers -> verify` 的过程
- 命名规则清单：标签携带参数量、量化、指令版本等

**02_model_detail.py**
- 字段语义表：architecture/parameters/context/quantization/capabilities
- `format_size` 把字节转 KB/MB/GB
- "参数量 × 比特"换算内存：FP16/Q8/Q4 的近似占用对比

**03_model_manager.py**
- 一个 dataclass 封装全部管理操作，环境无关
- `_all()` 自动切换真实 tags 或 DEMO 数据
- `disk_summary()` 按家族汇总，看到磁盘大头在哪

## 切换真实模式

```bash
ollama pull llama3.1 nomic-embed-text
python 03_model_manager.py   # 显示真实列表与大小
```