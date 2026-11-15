"""
Day07 练习一：异常变 Observation
==================================
工具抛错时, 不崩溃, 而是把错误文本转成 Observation 喂回历史,
模拟的"模型"读到错误后修正参数, 最终重试成功。

运行:
  python "Day07 - 错误处理与重试/Code/01-error-observation.py"
"""
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402


@tool
def get_product(sku: str) -> str:
    """查询商品价格; 若 sku 不是以 'P' 开头则抛错"""
    if not sku.startswith("P"):
        raise ValueError(f"无效 sku '{sku}', 应以 P 开头")
    return f"{sku} 价格 $10"


def safe_run(name, reg, args):
    """安全执行: 异常转成可读 Observation。"""
    t = reg.get(name)
    if not t:
        return f"错误: 没有工具 {name}"
    try:
        return t.run(**args)
    except Exception as e:
        return f"调用 {name} 出错: {e}"


def decider(messages, tools=None):
    obs = [m["content"] for m in messages if m.get("role") == "tool"]
    if not obs:
        # 第一次: 故意传错参数(带错误 sku, 触发异常)
        return {"content": '{"name":"get_product","args":{"sku":"xyz"}}', "tool_calls": []}
    if "出错" in obs[-1]:
        # 读到错误 -> 自纠: 传正确参数
        return {"content": '{"name":"get_product","args":{"sku":"P001"}}', "tool_calls": []}
    if "价格" in obs[-1]:
        return {"content": "Final: 商品 P001 价格 $10。", "tool_calls": []}
    return {"content": "重试", "tool_calls": []}


def main() -> None:
    reg = ToolRegistry([get_product])
    history = [{"role": "user", "content": "查一下 sku=xyz 的商品, 再修正查 P001"}]
    print("异常->Observation->自纠 演示\n")
    for step in range(6):
        raw = decider(history)["content"]
        print(f"── 第 {step+1} 轮 ──")
        print("   模型:", raw)
        if raw.startswith("Final"):
            print("✅ ", raw)
            return
        try:
            spec = json.loads(raw)
        except json.JSONDecodeError:
            history.append({"role": "tool", "content": "参数无法解析, 请重发"})
            print("   (Observation: 参数无法解析)")
            continue
        obs = safe_run(spec["name"], reg, spec["args"])
        print(f"   (Observation: {obs})")
        history.append({"role": "tool", "content": obs})
    print("⚠️ 未完成")


if __name__ == "__main__":
    main()