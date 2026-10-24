# Day02 - 模型管理与拉取

## 今日目标

上个模型爽完，开始剩下的一半：**管理**。今天掌握 Ollama 关于模型的全部命令与 API，理解模型是如何被拉取、存储、查看、删除的。

学完今天，你将能够：

1. 熟练使用 `pull/push/rm/list/cp/show` 模型管理命令
2. 理解模型仓库的命名（仓库:标签）与来源
3. 查看模型参数量、量化、上下文等元信息
4. 封装一个 Python 模型管理器（列表/搜索/删除/磁盘汇总）

---

## 一、模型命令总览

| 命令 | 作用 | 对应 API |
|------|------|---------|
| `ollama list` | 列出本地已安装模型 | `GET /api/tags` |
| `ollama pull <model>` | 从仓库拉取模型 | `POST /api/pull` |
| `ollama push <model>` | 推送到仓库 | `POST /api/push` |
| `ollama rm <model>` | 删除本地模型 | `DELETE /api/delete` |
| `ollama cp <a> <b>` | 复制模型 | `POST /api/copy` |
| `ollama show <model>` | 查看模型详情 | `POST /api/show` |
| `ollama ps` | 查看当前已加载（内存中）模型 | `GET /api/ps` |

### 1.1 模型命名：仓库:标签

```
llama3.1:latest      ← 最高频（省略标签默认 latest）
qwen2.5:7b           ← 7B 版本
llama3.1:8b-instruct  ← 带子标签
ollama.com/library/llama3.1  ← 完整仓库地址
```

**标签（标签）** 常用来区分：参数量（7b/13b）、量化（q4_0/q8_0）、指令版本（instruct）。

### 1.2 pull 的实质

`ollama pull llama3.1` 做的事：

```
Client         Server          仓库
  │ pull 请求   │               │
  │──────────▶ │   拉取分片     │
  │            │──────────────▶│
  │            │◀──────────────│ 分片校验
  │            │  存入 ~/.ollama/models
  │◀───────────│ 完成
```

模型不是一个大文件，而是**按 digest 分片下载**，可断点续传，重复的分片（共享层）会复用。

---

## 二、模型元信息（show 到底展示什么）

`ollama show llama3.1` 输出字段：

| 字段 | 含义 |
|------|------|
| `architecture` | 模型架构（llama/qwen/...） |
| `parametersize` | 参数量（如 8.0B） |
| `context length` | 最大上下文长度 |
| `embedding length` | 嵌入维度 |
| `quantization` | 量化方式（如 Q4_K_M） |
| `parameters` | 原始参数字典（如 temperature 默认） |
| `capabilities` | 能力（如 completion/vision） |
| `modified_at` / `size` | 时间与磁盘大小 |

**参数量 vs 内存占用**：一样的 7B，量化不同占用不同。
- FP16：约 14GB
- Q8：约 7GB
- Q4：约 4GB

这也是为什么 Q4 量化在小内存机器上最流行。

对应代码：`Code/02_model_detail.py`

---

## 三、模型管理器（Python 封装）

我们把命令层变薄成 Python 类，便于程序化管理：

```
├── list()            列出所有模型（名 + 大小 + 细节）
├── search(keyword)   按关键词过滤
├── show(name)        显示某模型详情
├── disk_summary()    汇总磁盘占用
├── remove(name)      删除模型
```

同时双模式兼容：无 Ollama 环境时用内置示例数据模拟。

对应代码：`Code/03_model_manager.py`

---

## 四、从 OpenAI/其他格式导入（进阶）

Ollama 不仅能拉它的仓库，还能import 其他格式模型：

```
1. 用 llama.cpp 等转成 GGUF 格式
2. Ollama.create(model=..., modelfile=Modelfile(... path=xxx.gguf))
```

> 渲染（Create）通常是模型格式转换的场景，初学者了解即可，不必深究。

---

## 五、磁盘占用与清理

- 每个模型是一个或多个大文件（几百 MB ~ 几十 GB）
- 多标签共享分片，删除一个不立即回收共享层
- `ollama rm <model>` 删除；`ollama list` 看大小决定删谁

一个小建议：**只保留"当前场景"的模型**，别的标签用完即删，避免磁盘悄无声息被占满。

---

## 六、今日核心要点

```
1. 六条核心命令：list/pull/push/rm/cp/show
2. 模型命名 = 仓库:标签，标签含参数量/量化/版本
3. pull 是分片下载，共享层复用，可断点续传
4. show 揭示参数量/上下文/量化/能力等元信息
5. 内存占用 ≈ 参数量 × 量化比特（Q4 最省）
6. 管理器把命令薄封装成 Python API，双模式兼容
```

---

## 七、代码文件说明

| 文件 | 内容 | 关键知识点 |
|------|------|-----------|
| `01_pull_list.py` | pull/list 的命令式演示（含模拟进度条） | 拉取与列表 |
| `02_model_detail.py` | 解析模型元信息字段 | show 详解 |
| `03_model_manager.py` | ModelManager 类：列表/搜索/删除/磁盘汇总 | 管理器封装 |

`ollama_util.py` 复用 Day01 的检测与模拟能力。

---

## 八、延伸思考

1. 为什么 Ollama 用"共享分片"而不是每个模型存独立副本？省了什么？
2. Q4 量化省一半内存，代价是什么？（精读让模型敏感的任务要谨慎）
3. `ollama show` 里的 context length 和推理时的 num_ctx 是什么关系？（提示：Day06）
4. 多个标签共用一个基础模型的场景下，删除会怎样？

---

## 九、明日预告

Day03 学习 **HTTP API 编程调用**：不再敲命令，而是用 `requests` 调 REST API，掌握 chat/generate/embed 三大端点，重点是**流式逐 token 生成**与响应的完整解析。