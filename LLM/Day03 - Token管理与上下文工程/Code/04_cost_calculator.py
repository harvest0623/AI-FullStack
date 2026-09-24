# 文件用途：成本计算器
# CostCalculator 类：
#   - 内置各主流模型价格表（输入/输出 单价 per 1M tokens）
#   - 计算单次调用成本
#   - 月度成本估算
#   - 成本告警（超出预算时提醒）
# 依赖：仅标准库（无需第三方包），不需要 API Key。
# 体现 AISearch 项目 core/ 中「Token 计数 / 成本管理」的封装思想。

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelPricing:
    """单模型价格（单位：USD / 1M tokens）。"""
    name: str
    input_price: float        # 输入单价
    output_price: float       # 输出单价
    context_window: int       # 上下文窗口
    currency: str = "USD"


# 主流模型价格参考表（随时可能调整，以官网为准）
DEFAULT_PRICING: dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing("gpt-4o", 2.5, 10, 128_000),
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", 0.15, 0.6, 128_000),
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", 10, 30, 128_000),
    "o1": ModelPricing("o1", 15, 60, 128_000),
    "o3-mini": ModelPricing("o3-mini", 1.1, 4.4, 200_000),
    "claude-3-5-sonnet": ModelPricing("claude-3-5-sonnet", 3, 15, 200_000),
    "claude-3-5-haiku": ModelPricing("claude-3-5-haiku", 0.8, 4, 200_000),
    # 国产模型价格以人民币计价，这里统一折算示意（约 1USD=7.2CNY）
    "qwen-plus": ModelPricing("qwen-plus", 0.11, 0.28, 128_000),      # ≈¥0.8/¥2
    "deepseek-chat": ModelPricing("deepseek-chat", 0.14, 0.28, 128_000),  # ≈¥1/¥2
    "glm-4-flash": ModelPricing("glm-4-flash", 0.0, 0.0, 128_000),    # 免费
}


@dataclass
class CostCalculator:
    """
    LLM 调用成本计算器。
    用法：
        calc = CostCalculator()
        cost = calc.estimate_call("gpt-4o-mini", input_tokens=1500, output_tokens=400)
    """
    pricing: dict[str, ModelPricing] = field(
        default_factory=lambda: dict(DEFAULT_PRICING)
    )
    monthly_budget: float = 50.0   # 月度预算（USD），超过则告警
    _month_input_tokens: dict[str, int] = field(default_factory=dict)
    _month_output_tokens: dict[str, int] = field(default_factory=dict)

    def add_pricing(self, model: ModelPricing) -> None:
        self.pricing[model.name] = model

    # ---- 单次成本 ----
    def estimate_call(self, model: str, input_tokens: int,
                      output_tokens: int) -> dict:
        """计算单次调用成本。"""
        p = self.pricing.get(model)
        if not p:
            raise ValueError(f"未知模型: {model}，已知: {list(self.pricing)}")
        input_cost = input_tokens / 1_000_000 * p.input_price
        output_cost = output_tokens / 1_000_000 * p.output_price
        total = input_cost + output_cost
        # 记入月度累计
        self._month_input_tokens[model] = self._month_input_tokens.get(model, 0) + input_tokens
        self._month_output_tokens[model] = self._month_output_tokens.get(model, 0) + output_tokens
        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total, 6),
            "currency": p.currency,
        }

    # ---- 月度估算 ----
    def monthly_estimate(self, calls_per_day: int, avg_input: int,
                         avg_output: int, model: str, days: int = 30) -> dict:
        """按日均调用次数估算月度成本。"""
        total_input = calls_per_day * avg_input * days
        total_output = calls_per_day * avg_output * days
        p = self.pricing[model]
        cost = total_input / 1_000_000 * p.input_price + total_output / 1_000_000 * p.output_price
        return {
            "model": model,
            "calls_per_day": calls_per_day,
            "days": days,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "monthly_cost": round(cost, 4),
            "currency": p.currency,
        }

    def monthly_actual(self) -> dict:
        """汇总已记录的实际月度调用成本（通过 estimate_call 累计）。"""
        details = {}
        grand_total = 0.0
        for model in self.pricing:
            it = self._month_input_tokens.get(model, 0)
            ot = self._month_output_tokens.get(model, 0)
            if it == 0 and ot == 0:
                continue
            p = self.pricing[model]
            cost = it / 1_000_000 * p.input_price + ot / 1_000_000 * p.output_price
            details[model] = {
                "input_tokens": it,
                "output_tokens": ot,
                "cost": round(cost, 4),
            }
            grand_total += cost
        return {"by_model": details, "total_cost": round(grand_total, 4)}

    # ---- 预算告警 ----
    def check_budget(self) -> None:
        """检查月度成本是否超预算，打印告警。"""
        actual = self.monthly_actual()
        total = actual["total_cost"]
        print(f"  月度累计成本: ${total:.4f} / 预算 ${self.monthly_budget:.2f}")
        if total > self.monthly_budget:
            over = total - self.monthly_budget
            print(f"  ⚠️ 成本告警：已超出预算 ${over:.4f}！建议：")
            print(f"     - 切换更便宜的模型（如 gpt-4o-mini / DeepSeek）")
            print(f"     - 压缩上下文历史（见 Day03 上下文管理）")
            print(f"     - 启用上下文缓存（命中缓存输入价大幅下降）")
        elif total > self.monthly_budget * 0.8:
            print(f"  ⚡ 提示：已用预算 {total/self.monthly_budget*100:.0f}%，接近上限")
        else:
            print(f"  ✅ 成本正常，已用预算 {total/self.monthly_budget*100:.0f}%")


def demo() -> None:
    print("=" * 60)
    print("成本计算器 CostCalculator 演示")
    print("=" * 60)

    calc = CostCalculator(monthly_budget=0.5)

    print("\n1. 单次调用成本对比（输入1500/输出400 tokens）")
    print("-" * 50)
    print(f"  {'模型':<20}{'输入$':<10}{'输出$':<10}{'合计$'}")
    for model in ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "deepseek-chat", "glm-4-flash"]:
        r = calc.estimate_call(model, 1500, 400)
        print(f"  {model:<20}{r['input_cost']:<10.6f}{r['output_cost']:<10.6f}{r['total_cost']:.6f}")

    print("\n2. 月度成本估算（每天 1000 次调用，平均 800 入/200 出）")
    print("-" * 50)
    for model in ["gpt-4o", "gpt-4o-mini", "deepseek-chat"]:
        m = calc.monthly_estimate(1000, 800, 200, model)
        print(f"  {model:<20} 月度成本: ${m['monthly_cost']:.2f}")

    print("\n3. 成本告警检查")
    print("-" * 50)
    calc.check_budget()

    print("\n提示：")
    print("- 国产模型（DeepSeek/Qwen/GLM）价格远低于 GPT-4o，中文场景性价比极高")
    print("- 输出 Token 通常比输入贵 3-4 倍，控制输出长度是省钱关键")
    print("- 长对话复用历史会重复计费输入 Token，需配合上下文压缩")


if __name__ == "__main__":
    demo()
