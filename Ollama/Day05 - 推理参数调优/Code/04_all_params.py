# -*- coding: utf-8 -*-
"""
Day05 - 04 综合参数调优演示

把 temperature / top_p / top_k / num_predict / stop / seed 组合起来，
理解"参数组合"如何控制输出的确定性、长度与终止条件。

双模式：有 Ollama -> 真实调用不同 options；无 -> 规则演示参数语义。
"""

from ollama_util import is_ollama_available, real_chat

# 预设几套"场景参数组合"
PRESETS = {
    "事实问答（稳）": {"temperature": 0.1, "top_p": 0.3, "top_k": 10},
    "创意写作（活）": {"temperature": 1.0, "top_p": 0.95, "top_k": 40},
    "代码生成（准）": {"temperature": 0.2, "top_p": 0.5, "top_k": 20},
}


def print_table():
    print("┌───────────────┬────────────────┬──────────┬──────────┬──────────────┐")
    print("│    参数        │      作用        │  常取值   │  偏大→    │  偏小→        │")
    print("├───────────────┼────────────────┼──────────┼──────────┼──────────────┤")
    rows = [
        ("temperature", "随机性/发散度", "0.1~1.0", "更自由", "更稳定"),
        ("top_p", "核采样阈值", "0.8~0.95", "更发散", "更聚焦"),
        ("top_k", "候选范围", "20~40", "更发散", "更保守"),
        ("num_predict", "最大输出长度", "128~4096", "更长", "更短"),
        ("seed", "随机种子", "任意整数", "—", "—"),
        ("stop", "停止序列", '["<|end|>"]', "更早停", "更晚停"),
    ]
    for r in rows:
        print("│" + "".join(f"{c:^15}|" for c in r))
    print("└───────────────┴────────────────┴──────────┴──────────┴──────────────┘")


def apply(preset: dict) -> str:
    """把参数组合渲染成人话说明"""
    return ", ".join(f"{k}={v}" for k, v in preset.items())


def main():
    print(">> 综合参数调优\n")
    print_table()

    print("\n一、三套场景组合")
    for name, opts in PRESETS.items():
        print(f"  {name}:  {apply(opts)}")

    if not is_ollama_available("llama3.1"):
        print("\n  本机无 Ollama，仅展示参数语义；安装后自动走真实对比。")
        return

    print("\n二、真实模型对比（同样的问题，不同参数组合看差异）")
    question = "请写一句关于春天的短句，约 10 个字："
    for name, opts in PRESETS.items():
        full = dict(opts)
        full["num_predict"] = 40
        out = real_chat("llama3.1", [{"role": "user", "content": question}], full)
        print(f"\n  [{name}] ({apply(full)})")
        print(f"  → {out}")

    print("\n  tips: 稳定性看重时降 temperature，控制长短用 num_predict，"
          "防跑题用 top_p/top_k。")


if __name__ == "__main__":
    main()