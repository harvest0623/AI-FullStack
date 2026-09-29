# 文件用途：LoRA 配置示例
# 生成 LoRA 微调配置：rank/alpha/dropout/learning_rate/epochs/batch_size
# 支持 LLaMA-Factory 和 Axolotl 两种配置格式生成
# 含配置参数说明和建议值，配置文件生成器
# Python 3.10+ 可运行（纯标准库）

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class LoRAConfig:
    """LoRA 微调核心配置。"""

    # 模型配置
    base_model: str = "Qwen/Qwen2-7B-Instruct"
    adapter_name: str = "aisearch_lora"
    template: str = "qwen"  # LLaMA-Factory 模板名

    # LoRA 参数
    lora_rank: int = 8           # 秩 r，常用 8/16/32/64
    lora_alpha: int = 16         # 缩放系数，通常为 rank 的 2 倍
    lora_dropout: float = 0.05   # dropout 防过拟合
    lora_target: str = "q_proj,k_proj,v_proj,o_proj"  # 应用 LoRA 的模块

    # 训练参数
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation: int = 4  # 有效 batch = batch_size × gradient_accumulation
    warmup_ratio: float = 0.03
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    scheduler: str = "cosine"   # 学习率调度器

    # 数据配置
    train_file: str = "data/train.jsonl"
    val_file: str = "data/val.jsonl"
    max_seq_length: int = 1024

    # 输出配置
    output_dir: str = "output/aisearch_lora"
    save_steps: int = 500
    logging_steps: int = 10

    # 量化（QLoRA）
    quantization: str | None = None  # None / "4bit" / "8bit"


class LoRAConfigGenerator:
    """LoRA 配置文件生成器，支持 LLaMA-Factory 与 Axolotl 格式。"""

    def __init__(self, config: LoRAConfig | None = None) -> None:
        self.config = config or LoRAConfig()

    def generate_llamafactory_yaml(self) -> str:
        """生成 LLaMA-Factory 的 YAML 配置。"""
        c = self.config
        return f"""# LLaMA-Factory LoRA 微调配置
# 用法：llamafactory-cli train this_config.yaml
# 文档：https://llamafactory.readthedocs.io/

### 模型配置
model_name_or_path: {c.base_model}
adapter_name_or_path: {c.adapter_name}
template: {c.template}
finetuning_type: lora

### 数据配置
dataset_dir: data
dataset: aisearch_train
eval_dataset: aisearch_val
cutoff_len: {c.max_seq_length}
max_samples: 100000
overwrite_cache: true

### LoRA 参数
lora_rank: {c.lora_rank}
lora_alpha: {c.lora_alpha}
lora_dropout: {c.lora_dropout}
lora_target: [{c.lora_target}]

### 训练参数
output_dir: {c.output_dir}
per_device_train_batch_size: {c.batch_size}
per_device_eval_batch_size: {c.batch_size}
gradient_accumulation_steps: {c.gradient_accumulation}
learning_rate: {c.learning_rate}
num_train_epochs: {c.num_epochs}
lr_scheduler_type: {c.scheduler}
warmup_ratio: {c.warmup_ratio}
weight_decay: {c.weight_decay}
max_grad_norm: {c.max_grad_norm}
logging_steps: {c.logging_steps}
save_steps: {c.save_steps}
overwrite_output_dir: true

### 评估
val_size: 0.2
eval_strategy: steps
eval_steps: {c.save_steps}
plot_loss: true

### 量化（QLoRA，可选）
{'quantization_bit: 4' if c.quantization == '4bit' else '# quantization_bit: 4'}
"""

    def generate_axolotl_yaml(self) -> str:
        """生成 Axolotl 的 YAML 配置。"""
        c = self.config
        target_modules = c.lora_target.split(",")
        return f"""# Axolotl LoRA 微调配置
# 用法：accelerate launch -m axolotl.cli.train this_config.yml
# 文档：https://docs.axolotl.ai/

base_model: {c.base_model}
model_type: AutoModelForCausalLM
tokenizer_type: AutoTokenizer
trust_remote_code: true

# 数据
datasets:
  - path: {c.train_file}
    type: sharegpt
    conversation: chat_template
val_set_size: 0.2
max_seq_length: {c.max_seq_length}

# LoRA
adapter: lora
lora_rank: {c.lora_rank}
lora_alpha: {c.lora_alpha}
lora_dropout: {c.lora_dropout}
lora_target_modules: {target_modules}

# 训练
micro_batch_size: {c.batch_size}
gradient_accumulation_steps: {c.gradient_accumulation}
num_epochs: {c.num_epochs}
learning_rate: {c.learning_rate}
lr_scheduler: {c.scheduler}
warmup_ratio: {c.warmup_ratio}
weight_decay: {c.weight_decay}
max_grad_norm: {c.max_grad_norm}
optimizer: adamw_torch

# 输出
output_dir: {c.output_dir}
save_steps: {c.save_steps}
logging_steps: {c.logging_steps}

# QLoRA（可选）
{'load_in_4bit: true' if c.quantization == '4bit' else '# load_in_4bit: true'}
"""

    def generate_param_guide(self) -> str:
        """生成参数说明与建议值文档。"""
        c = self.config
        return f"""# LoRA 微调参数说明

## LoRA 参数

| 参数 | 当前值 | 推荐范围 | 说明 |
| --- | --- | --- | --- |
| lora_rank | {c.lora_rank} | 8-64 | 秩 r，越大表达能力越强，参数越多 |
| lora_alpha | {c.lora_alpha} | = 2×rank | 缩放系数，控制 LoRA 更新的幅度 |
| lora_dropout | {c.lora_dropout} | 0.05-0.1 | 防止过拟合 |
| lora_target | {c.lora_target} | q_proj,v_proj 等 | 应用 LoRA 的注意力模块 |

## 训练参数

| 参数 | 当前值 | 推荐范围 | 说明 |
| --- | --- | --- | --- |
| learning_rate | {c.learning_rate} | 1e-4 ~ 3e-4 | LoRA 学习率，比全量微调大 |
| num_epochs | {c.num_epochs} | 2-5 | 过多易过拟合 |
| batch_size | {c.batch_size} | 4-16 | 受显存限制 |
| gradient_accumulation | {c.gradient_accumulation} | 4-8 | 梯度累积，等效增大 batch |
| warmup_ratio | {c.warmup_ratio} | 0.03-0.1 | 学习率预热比例 |
| max_seq_length | {c.max_seq_length} | 512-2048 | 最大序列长度，影响显存 |

## 参数选择建议

- **入门/快速验证**：rank=8, alpha=16, epochs=3, lr=2e-4
- **生产级/追求效果**：rank=32, alpha=64, epochs=5, lr=1e-4
- **显存受限（QLoRA）**：rank=8, 4bit 量化, batch_size=2, gradient_accumulation=8
- **长文本任务**：max_seq_length=2048, 适当减小 batch_size

## 有效 batch size 计算

有效 batch = batch_size × gradient_accumulation × GPU 数量
当前配置：{c.batch_size} × {c.gradient_accumulation} × 1 = {c.batch_size * c.gradient_accumulation}
"""

    def save_configs(self, output_dir: str | Path = "lora_configs") -> None:
        """保存所有配置文件。"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # LLaMA-Factory 配置
        lf_path = output_dir / "llamafactory_lora.yaml"
        lf_path.write_text(self.generate_llamafactory_yaml(), encoding="utf-8")
        print(f"[LoRAConfig] LLaMA-Factory 配置已保存: {lf_path}")

        # Axolotl 配置
        ax_path = output_dir / "axolotl_lora.yml"
        ax_path.write_text(self.generate_axolotl_yaml(), encoding="utf-8")
        print(f"[LoRAConfig] Axolotl 配置已保存: {ax_path}")

        # 参数说明
        guide_path = output_dir / "param_guide.md"
        guide_path.write_text(self.generate_param_guide(), encoding="utf-8")
        print(f"[LoRAConfig] 参数说明已保存: {guide_path}")

        # 原始配置 JSON
        json_path = output_dir / "lora_config.json"
        json_path.write_text(
            json.dumps(asdict(self.config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[LoRAConfig] 原始配置已保存: {json_path}")


def demo_lora_config() -> None:
    """演示 LoRA 配置生成。"""
    # 标准配置
    config = LoRAConfig(
        base_model="Qwen/Qwen2-7B-Instruct",
        lora_rank=8,
        lora_alpha=16,
        learning_rate=2e-4,
        num_epochs=3,
    )
    generator = LoRAConfigGenerator(config)

    print("=" * 60)
    print("LLaMA-Factory 配置")
    print("=" * 60)
    print(generator.generate_llamafactory_yaml())

    print("=" * 60)
    print("Axolotl 配置")
    print("=" * 60)
    print(generator.generate_axolotl_yaml())

    print("=" * 60)
    print("参数说明")
    print("=" * 60)
    print(generator.generate_param_guide())

    # 保存到文件
    generator.save_configs()

    # QLoRA 配置示例
    print("\n--- QLoRA 配置示例（4bit 量化）---")
    qlora_config = LoRAConfig(
        base_model="Qwen/Qwen2-7B-Instruct",
        lora_rank=8,
        lora_alpha=16,
        batch_size=2,
        gradient_accumulation=8,
        quantization="4bit",
    )
    qlora_generator = LoRAConfigGenerator(qlora_config)
    print(qlora_generator.generate_llamafactory_yaml())


if __name__ == "__main__":
    demo_lora_config()
