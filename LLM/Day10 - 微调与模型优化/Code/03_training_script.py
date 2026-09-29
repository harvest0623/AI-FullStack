# 文件用途：微调训练脚本框架
# TrainingScriptGenerator 类：生成完整微调脚本（含数据加载/模型加载/LoRA配置/训练循环/评估/保存）
# 支持 LLaMA-Factory CLI 命令生成和 HuggingFace TRL 脚本生成
# 含 GPU 显存检查
# Python 3.10+ 可运行（纯标准库，生成的脚本需额外依赖）

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TrainingConfig:
    """训练配置。"""

    base_model: str = "Qwen/Qwen2-7B-Instruct"
    train_file: str = "data/train.jsonl"
    val_file: str = "data/val.jsonl"
    output_dir: str = "output/aisearch_lora"
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation: int = 4
    max_seq_length: int = 1024
    use_qlora: bool = False
    use_unsloth: bool = False  # 是否使用 Unsloth 加速


class TrainingScriptGenerator:
    """微调训练脚本生成器。"""

    def __init__(self, config: TrainingConfig | None = None) -> None:
        self.config = config or TrainingConfig()

    def check_gpu_requirements(self) -> str:
        """生成 GPU 显存需求检查说明。"""
        c = self.config
        # 粗略估算显存需求
        base_vram = 14  # 7B FP16
        if c.use_qlora:
            base_vram = 6
        train_overhead = c.batch_size * c.max_seq_length * 0.001  # 训练开销
        total = base_vram + train_overhead + 2  # +2GB 余量

        return f"""# GPU 显存需求检查

## 当前配置预估显存

| 项目 | 估算 |
| --- | --- |
| 基座模型 ({'QLoRA 4bit' if c.use_qlora else 'FP16'}) | {base_vram} GB |
| 训练开销 (batch={c.batch_size}, seq={c.max_seq_length}) | {train_overhead:.1f} GB |
| LoRA 适配器 + 优化器状态 | ~2 GB |
| **总预估** | **{total:.1f} GB** |

## 检查命令

```bash
# 查看 GPU 显存
nvidia-smi

# 查看 CUDA 版本
nvcc --version

# 查看 PyTorch 是否可用 GPU
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

## 显存不足时的优化建议

1. 启用 QLoRA（4bit 量化）：显存降至约 6GB
2. 减小 batch_size（如 1-2）
3. 增大 gradient_accumulation_steps（保持等效 batch）
4. 减小 max_seq_length（如 512）
5. 使用 Unsloth 加速（2-5x 显存优化）
6. 使用梯度检查点 gradient checkpointing
"""

    def generate_llamafactory_cli(self) -> str:
        """生成 LLaMA-Factory CLI 命令。"""
        c = self.config
        qlora_flag = "--quantization_bit 4 " if c.use_qlora else ""
        return f"""# LLaMA-Factory CLI 微调命令
# 前置：pip install llamafactory[torch,metrics]

# 1. 数据集注册（在 data/dataset_info.json 中添加）
# "aisearch_train": {{
#   "file_name": "train.jsonl",
#   "columns": {{ "prompt": "instruction", "query": "input", "response": "output" }}
# }}

# 2. 启动训练
llamafactory-cli train \\
  --model_name_or_path {c.base_model} \\
  --dataset aisearch_train \\
  --dataset_dir data \\
  --template qwen \\
  --finetuning_type lora \\
  --lora_target q_proj,k_proj,v_proj,o_proj \\
  --lora_rank {c.lora_rank} \\
  --lora_alpha {c.lora_alpha} \\
  --lora_dropout {c.lora_dropout} \\
  {qlora_flag}--output_dir {c.output_dir} \\
  --per_device_train_batch_size {c.batch_size} \\
  --gradient_accumulation_steps {c.gradient_accumulation} \\
  --learning_rate {c.learning_rate} \\
  --num_train_epochs {c.num_epochs} \\
  --cutoff_len {c.max_seq_length} \\
  --logging_steps 10 \\
  --save_steps 500 \\
  --plot_loss true

# 3. 训练后合并 LoRA 权重
llamafactory-cli export \\
  --model_name_or_path {c.base_model} \\
  --adapter_name_or_path {c.output_dir} \\
  --template qwen \\
  --finetuning_type lora \\
  --export_dir {c.output_dir}_merged

# 4. 部署到 Ollama（需先转换为 GGUF）
# 参考 llama.cpp 的 convert 与 quantize 命令
"""

    def generate_hf_trl_script(self) -> str:
        """生成 HuggingFace TRL 完整训练脚本。"""
        c = self.config
        unsloth_import = ""
        unsloth_load = ""
        if c.use_unsloth:
            unsloth_import = """
from unsloth import FastLanguageModel"""
            unsloth_load = f"""# 使用 Unsloth 加载模型（2-5x 加速）
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="{c.base_model}",
    max_seq_length={c.max_seq_length},
    dtype=None,
    load_in_4bit={c.use_qlora},
)
model = FastLanguageModel.get_peft_model(
    model,
    r={c.lora_rank},
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha={c.lora_alpha},
    lora_dropout={c.lora_dropout},
    bias="none",
    use_gradient_checkpointing="unsloth",
)
"""

        return f'''# 文件用途：HuggingFace TRL LoRA 微调脚本（自动生成）
# Python 3.10+ 可运行
# 依赖：pip install torch transformers peft trl datasets accelerate
# {"可选 Unsloth 加速：pip install unsloth" if c.use_unsloth else ""}

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model{unsloth_import}
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
)
from trl import SFTTrainer


def main():
    # 1. 加载 tokenizer 与模型
    model_name = "{c.base_model}"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
{unsloth_load if c.use_unsloth else f"""
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        {"load_in_4bit=True," if c.use_qlora else ""}
    )

    # 2. 配置 LoRA
    lora_config = LoraConfig(
        r={c.lora_rank},
        lora_alpha={c.lora_alpha},
        lora_dropout={c.lora_dropout},
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()"""}

    # 3. 加载数据
    dataset = load_dataset("json", data_files={{
        "train": "{c.train_file}",
        "validation": "{c.val_file}",
    }})

    def format_example(example):
        text = f"### 指令：{{example['instruction']}}\\n"
        if example.get("input"):
            text += f"### 输入：{{example['input']}}\\n"
        text += f"### 输出：{{example['output']}}"
        return {{"text": text}}

    train_dataset = dataset["train"].map(format_example)
    eval_dataset = dataset["validation"].map(format_example)

    # 4. 训练参数
    training_args = TrainingArguments(
        output_dir="{c.output_dir}",
        per_device_train_batch_size={c.batch_size},
        per_device_eval_batch_size={c.batch_size},
        gradient_accumulation_steps={c.gradient_accumulation},
        learning_rate={c.learning_rate},
        num_train_epochs={c.num_epochs},
        logging_steps=10,
        save_steps=500,
        eval_strategy="steps",
        eval_steps=500,
        save_total_limit=3,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.01,
        max_grad_norm=1.0,
        fp16=True,
        {"gradient_checkpointing=True," if c.use_qlora else ""}
        report_to="none",
    )

    # 5. 训练器
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        max_seq_length={c.max_seq_length},
        dataset_text_field="text",
    )

    # 6. 训练
    trainer.train()

    # 7. 保存
    trainer.save_model("{c.output_dir}/final")
    print("训练完成，模型已保存到 {c.output_dir}/final")


if __name__ == "__main__":
    main()
'''

    def generate_all(self, output_dir: str | Path = "training_scripts") -> None:
        """生成所有脚本文件。"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # GPU 检查说明
        (output_dir / "gpu_check.md").write_text(
            self.check_gpu_requirements(), encoding="utf-8"
        )
        print(f"[TrainingScript] GPU 检查说明已保存")

        # LLaMA-Factory CLI
        (output_dir / "llamafactory_cli.md").write_text(
            self.generate_llamafactory_cli(), encoding="utf-8"
        )
        print(f"[TrainingScript] LLaMA-Factory CLI 命令已保存")

        # HuggingFace TRL 脚本
        script_name = "unsloth_train.py" if self.config.use_unsloth else "trl_train.py"
        (output_dir / script_name).write_text(
            self.generate_hf_trl_script(), encoding="utf-8"
        )
        print(f"[TrainingScript] TRL 训练脚本已保存: {script_name}")


def demo_training_script() -> None:
    """演示训练脚本生成。"""
    # 标准 LoRA 训练
    config = TrainingConfig(
        base_model="Qwen/Qwen2-7B-Instruct",
        lora_rank=8,
        learning_rate=2e-4,
        num_epochs=3,
    )
    generator = TrainingScriptGenerator(config)

    print("=" * 60)
    print("GPU 显存检查")
    print("=" * 60)
    print(generator.check_gpu_requirements())

    print("=" * 60)
    print("LLaMA-Factory CLI 命令")
    print("=" * 60)
    print(generator.generate_llamafactory_cli())

    print("=" * 60)
    print("HuggingFace TRL 脚本（片段）")
    print("=" * 60)
    script = generator.generate_hf_trl_script()
    print(script[:800] + "\n...（完整脚本见生成文件）")

    # 保存所有脚本
    generator.generate_all()

    # QLoRA + Unsloth 示例
    print("\n--- QLoRA + Unsloth 配置示例 ---")
    qlora_config = TrainingConfig(
        base_model="Qwen/Qwen2-7B-Instruct",
        use_qlora=True,
        use_unsloth=True,
        batch_size=2,
        gradient_accumulation=8,
    )
    qlora_generator = TrainingScriptGenerator(qlora_config)
    qlora_generator.generate_all("training_scripts_qlora")


if __name__ == "__main__":
    demo_training_script()
