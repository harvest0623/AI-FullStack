# 文件用途：模型量化指南
# 量化配置生成工具：根据 GPU 显存推荐量化级别和模型大小
# 含显存计算器、Modelfile 生成器、量化格式说明文档生成
# Python 3.10+ 可运行（纯标准库，无需额外依赖）

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# 各精度每参数占用字节数
BYTES_PER_PARAM = {
    "FP32": 4.0,
    "FP16": 2.0,
    "BF16": 2.0,
    "INT8": 1.0,
    "INT4": 0.5,
}

# GGUF 量化级别说明
GGUF_LEVELS = {
    "Q4_0": {"bytes": 0.5, "desc": "最基础的 4bit 量化，速度最快，质量略低"},
    "Q4_K_M": {"bytes": 0.55, "desc": "推荐的 4bit 量化，质量与速度平衡"},
    "Q5_K_M": {"bytes": 0.68, "desc": "5bit 量化，质量更高，显存占用略增"},
    "Q6_K": {"bytes": 0.82, "desc": "6bit 量化，接近 FP16 质量"},
    "Q8_0": {"bytes": 1.0, "desc": "8bit 量化，几乎无损，显存占用较大"},
}

# 常见模型参数量（十亿）
COMMON_MODELS = {
    "qwen2.5:1.5b": 1.5,
    "qwen2.5:7b": 7.0,
    "qwen2.5:14b": 14.0,
    "qwen2.5:32b": 32.0,
    "qwen2.5:72b": 72.0,
    "llama3.1:8b": 8.0,
    "llama3.1:70b": 70.0,
    "mistral:7b": 7.0,
    "phi3:14b": 14.0,
}


@dataclass
class QuantRecommendation:
    """量化推荐结果。"""

    model: str
    params_b: float
    precision: str
    vram_gb: float
    fits: bool
    note: str


class QuantizationGuide:
    """模型量化指南工具。"""

    @staticmethod
    def calc_vram(params_b: float, precision: str) -> float:
        """计算模型显存占用（GB）。

        params_b: 参数量（十亿）
        precision: 精度（FP16/INT8/INT4 等）
        返回：显存 GB（含约 20% 的上下文与开销余量）
        """
        bytes_per = BYTES_PER_PARAM.get(precision.upper(), 2.0)
        # 模型权重 + 约 20% 余量（KV Cache、激活值等）
        return round(params_b * bytes_per * 1.2, 2)

    @staticmethod
    def recommend(
        params_b: float,
        vram_gb: float,
    ) -> list[QuantRecommendation]:
        """根据显存推荐可用的量化级别。"""
        results: list[QuantRecommendation] = []
        # 从低精度到高精度尝试
        for prec in ["INT4", "INT8", "FP16"]:
            need = QuantizationGuide.calc_vram(params_b, prec)
            fits = need <= vram_gb
            if prec == "INT4":
                note = "推荐：显存最省，质量略降（约1-2%）"
            elif prec == "INT8":
                note = "平衡：几乎无损，显存适中"
            else:
                note = "质量优先：无损，显存占用大"
            if fits:
                note = "✅ " + note
            else:
                note = "❌ 显存不足 - " + note
            results.append(
                QuantRecommendation(
                    model=f"{params_b}B",
                    params_b=params_b,
                    precision=prec,
                    vram_gb=need,
                    fits=fits,
                    note=note,
                )
            )
        return results

    @staticmethod
    def recommend_model(vram_gb: float) -> list[dict[str, Any]]:
        """根据显存推荐可跑的常见模型与量化方案。"""
        suggestions: list[dict[str, Any]] = []
        for model, params in COMMON_MODELS.items():
            for prec in ["INT4", "INT8", "FP16"]:
                need = QuantizationGuide.calc_vram(params, prec)
                if need <= vram_gb:
                    suggestions.append(
                        {
                            "model": model,
                            "params_b": params,
                            "precision": prec,
                            "vram_gb": need,
                        }
                    )
                    break  # 每个模型只推荐最高可用的精度
        # 按参数量排序
        suggestions.sort(key=lambda x: x["params_b"], reverse=True)
        return suggestions

    @staticmethod
    def generate_modelfile(
        base_model: str = "qwen2.5:7b",
        system_prompt: str = "你是一个专业的中文智能问答助手，回答准确、简洁。",
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_ctx: int = 4096,
    ) -> str:
        """生成 Ollama Modelfile。"""
        return f"""# Modelfile - 自定义模型配置
# 用法：ollama create mymodel -f Modelfile

FROM {base_model}

# 对话模板
TEMPLATE \"\"\"{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
\"\"\"

# 推理参数
PARAMETER temperature {temperature}
PARAMETER top_p {top_p}
PARAMETER num_ctx {num_ctx}
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"

# 系统提示词
SYSTEM \"\"\"{system_prompt}\"\"\"
"""

    @staticmethod
    def generate_format_doc() -> str:
        """生成量化格式说明文档。"""
        lines = [
            "# 模型量化格式说明",
            "",
            "## 精度与字节数对照",
            "",
            "| 精度 | 每参数字节 | 7B 模型显存(含余量) | 质量损失 |",
            "| --- | --- | --- | --- |",
        ]
        for prec, b in BYTES_PER_PARAM.items():
            vram = round(7 * b * 1.2, 2)
            loss = {
                "FP32": "无（基准）",
                "FP16": "无",
                "BF16": "无",
                "INT8": "几乎无损",
                "INT4": "略降（1-2%）",
            }.get(prec, "-")
            lines.append(f"| {prec} | {b} | {vram} GB | {loss} |")

        lines.extend(["", "## GGUF 量化级别", "", "| 级别 | 字节/参数 | 说明 |", "| --- | --- | --- |"])
        for level, info in GGUF_LEVELS.items():
            lines.append(f"| {level} | {info['bytes']} | {info['desc']} |")

        lines.extend(
            [
                "",
                "## 量化格式选型建议",
                "",
                "- **Ollama / llama.cpp**：使用 GGUF 格式，推荐 Q4_K_M",
                "- **vLLM 生产部署**：使用 AWQ 或 GPTQ，推荐 INT4",
                "- **质量优先**：使用 FP16 或 Q8_0",
                "- **显存极度受限**：使用 Q4_0 或 INT4",
            ]
        )
        return "\n".join(lines)

    def print_guide(self, vram_gb: float = 16.0) -> None:
        """打印量化指南报告。"""
        print("=" * 60)
        print(f"量化推荐报告（可用显存：{vram_gb} GB）")
        print("=" * 60)

        print("\n--- 7B 模型量化方案 ---")
        for r in self.recommend(7.0, vram_gb):
            print(f"  {r.precision:<6} 显存={r.vram_gb:<6}GB  {r.note}")

        print("\n--- 可部署的模型推荐 ---")
        models = self.recommend_model(vram_gb)
        for m in models:
            print(
                f"  {m['model']:<18} 参数={m['params_b']}B  "
                f"精度={m['precision']:<5} 显存={m['vram_gb']}GB"
            )

        print("\n--- Modelfile 示例 ---")
        print(self.generate_modelfile())


def demo_quantization() -> None:
    """演示量化指南工具的用法。"""
    guide = QuantizationGuide()

    # 显存计算
    print("--- 显存计算器 ---")
    for params in [7, 13, 70]:
        for prec in ["FP16", "INT8", "INT4"]:
            vram = guide.calc_vram(params, prec)
            print(f"  {params}B {prec:<5} → {vram} GB")

    # 根据显存推荐
    guide.print_guide(vram_gb=16.0)

    # 量化格式文档
    print("\n--- 量化格式说明文档 ---")
    print(guide.generate_format_doc())


if __name__ == "__main__":
    demo_quantization()
