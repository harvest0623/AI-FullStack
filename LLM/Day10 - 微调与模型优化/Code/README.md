# Day10 Code - 微调实践指南

本目录提供 LLM 微调全流程的代码工具，从数据准备、配置生成、训练脚本到效果评估，覆盖微调的每个关键环节。配合 AISearch 智能问答服务，可完成领域模型定制。

## 环境准备

### 1. 安装微调工具链

```bash
# LLaMA-Factory（推荐，最易用）
pip install llamafactory[torch,metrics]

# 或使用 Unsloth（显存优化 + 加速）
pip install "unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git"

# HuggingFace 工具（代码级控制）
pip install torch transformers peft trl datasets accelerate
```

### 2. Python 依赖

```bash
pip install openai  # 评估脚本需要
```

## 文件说明

| 文件 | 说明 | 运行命令 |
| --- | --- | --- |
| `01_data_preparation.py` | 数据准备工具（加载/清洗/格式转换/质量报告） | `python 01_data_preparation.py` |
| `02_lora_config.py` | LoRA 配置生成（LLaMA-Factory/Axolotl 格式） | `python 02_lora_config.py` |
| `03_training_script.py` | 训练脚本生成（LLaMA-Factory CLI / TRL 脚本） | `python 03_training_script.py` |
| `04_eval_finetuned.py` | 微调效果评估（准确率/格式/灾难性遗忘） | `python 04_eval_finetuned.py` |

## LLaMA-Factory 完整使用教程

### 1. 数据准备

```bash
# 准备数据（运行 01_data_preparation.py 生成）
python 01_data_preparation.py

# 数据会输出到 finetune_data/ 目录
# - train.jsonl / val.jsonl（指令格式）
# - train_conversations.jsonl（对话格式）
# - quality_report.json（质量报告）
```

### 2. 注册数据集

在 `data/dataset_info.json` 中注册数据集：

```json
{
  "aisearch_train": {
    "file_name": "train.jsonl",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  },
  "aisearch_val": {
    "file_name": "val.jsonl",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}
```

### 3. 启动 Web UI（可选）

```bash
llamafactory-cli webui
# 访问 http://localhost:7860 可视化配置训练
```

### 4. 命令行训练

```bash
# 使用生成的配置（运行 02_lora_config.py / 03_training_script.py 生成）
llamafactory-cli train lora_configs/llamafactory_lora.yaml
```

### 5. 合并 LoRA 权重

```bash
llamafactory-cli export \
  --model_name_or_path Qwen/Qwen2-7B-Instruct \
  --adapter_name_or_path output/aisearch_lora \
  --template qwen \
  --finetuning_type lora \
  --export_dir output/aisearch_merged
```

### 6. 转换为 GGUF 并部署到 Ollama

```bash
# 转换为 GGUF（需要 llama.cpp）
python convert.py output/aisearch_merged --outfile aisearch.gguf

# 量化
./llama-quantize aisearch.gguf aisearch-q4km.gguf Q4_K_M

# 创建 Ollama 模型
echo 'FROM ./aisearch-q4km.gguf' > Modelfile
ollama create qwen2.5:7b-aisearch -f Modelfile
```

## 数据准备最佳实践

### 数据质量检查清单

- [ ] 数据来源合法，无版权问题
- [ ] 去除完全重复与高度相似数据
- [ ] 过滤空值、过短、含乱码的内容
- [ ] 统一格式（指令 or 对话）
- [ ] 覆盖多种场景与难度
- [ ] 训练/验证集划分（8:2）
- [ ] 人工抽检输出质量

### 数据量建议

| 任务复杂度 | 建议数据量 | 训练时长（7B LoRA） |
| --- | --- | --- |
| 简单分类 | 500-1000 | 1-2 小时 |
| 领域问答 | 2000-5000 | 3-6 小时 |
| 风格定制 | 1000-2000 | 2-3 小时 |
| 复杂推理 | 5000+ | 6+ 小时 |

## LoRA 参数调优建议

### 参数选择决策表

| 场景 | rank | alpha | epochs | lr | 备注 |
| --- | --- | --- | --- | --- | --- |
| 快速验证 | 8 | 16 | 2 | 3e-4 | 先验证可行性 |
| 标准微调 | 8 | 16 | 3 | 2e-4 | 通用推荐 |
| 追求效果 | 32 | 64 | 5 | 1e-4 | 更强表达力 |
| 显存受限 | 8 | 16 | 3 | 2e-4 | QLoRA 4bit |

### 调参经验

- **学习率**：LoRA 通常 1e-4 ~ 3e-4，比全量微调大 10 倍
- **epochs**：2-5 为宜，超过 5 易过拟合
- **rank**：8 通用，32 较强，64+ 收益递减
- **alpha**：固定为 rank 的 2 倍
- **过拟合信号**：训练 loss 持续下降但验证 loss 上升

## 微调效果评估方法

### 评估流程

1. 准备任务测试集（50-100 条，含期望输出）
2. 准备通用能力测试集（MMLU 子集，30-50 条）
3. 运行 `04_eval_finetuned.py` 对比微调前后
4. 检查任务准确率提升与通用能力是否下降
5. 撰写评估报告

### 灾难性遗忘判断标准

- 通用能力下降 < 5%：正常，可接受
- 通用能力下降 5%-10%：需关注，建议混入通用数据
- 通用能力下降 > 10%：严重遗忘，需减少 epochs 或降低学习率

## 常见问题排查清单

**Q: 训练 loss 不下降？**
- 检查学习率是否过小（建议 2e-4）
- 检查数据格式是否正确
- 检查 LoRA target 模块是否正确

**Q: 训练 loss 下降但效果没提升？**
- 可能过拟合，减少 epochs
- 验证集质量检查
- 数据多样性不足

**Q: 显存不足（OOM）？**
- 启用 QLoRA 4bit 量化
- 减小 batch_size，增大 gradient_accumulation
- 减小 max_seq_length
- 使用 Unsloth 加速

**Q: 微调后通用能力下降？**
- 减少 epochs（2-3）
- 降低学习率
- 在训练数据中混入 10-20% 通用数据
- 降低 LoRA rank
