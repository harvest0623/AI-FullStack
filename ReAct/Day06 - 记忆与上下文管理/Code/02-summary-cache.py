"""
Day06 练习二：摘要压缩与工具结果缓存
=====================================
1. 摘要压缩: 把"太老的对话"交给"模拟摘要模型"压成一句, 放入 system
2. 工具结果缓存: 相同 (工具, 参数) 只执行一次, 减少开销

运行:
  python "Day06 - 记忆与上下文管理/Code/02-summary-cache.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import text, tool_call  # noqa: F401  # noqa: E402


def fake_summarizer(old_messages) -> str:
    """模拟"摘要 LLM": 把若干条老消息压成一个摘要。"""
    items = [m["content"][:12] for m in old_messages if m["role"] != "system"]
    return "此前对话摘要: " + " | ".join(items[-6:]) + " (已压缩)"


def summarize_old(messages, keep_last: int):
    """太老的归入摘要(放 system), 最近 keep_last 条保持原样。"""
    if len(messages) <= keep_last:
        return messages
    old = messages[: len(messages) - keep_last]
    recent = messages[len(messages) - keep_last:]
    # 把 system 摘要在最前
    summary = fake_summarizer(old)
    return [{"role": "system", "content": summary}] + recent


# ---------- 工具结果缓存 ----------
_cache: dict = {}


def run_cached(name: str, **kw) -> str:
    key = (name, tuple(sorted(kw.items())))
    if key in _cache:
        return f"[cache] {_cache[key]}"
    result = _expensive_tool(name, **kw)
    _cache[key] = result
    return result


def _expensive_tool(name: str, **kw) -> str:
    print(f"   > 真正执行 {name}({kw})…")
    if name == "get_price":
        return f"{kw['sku']} 价格 $10"
    if name == "get_rating":
        return f"{kw['sku']} 评分 4.8"
    return "unk"


def main() -> None:
    print("≈≈≈ 摘要压缩 ≈≈≈")
    hist = [{"role": "system", "content": "老 system"}]
    for i in range(10):
        hist.append({"role": "user", "content": f"第{i+1}句很长的历史用户输入..."})
        hist.append({"role": "assistant", "content": f"第{i+1}句很长的历史回复..."})

    compressed = summarize_old(hist, keep_last=4)
    print(f"原始 {len(hist)} 条 -> 压缩后 {len(compressed)} 条")
    print("压缩后的 system: ", compressed[0]["content"])
    print("保留的最近 roles:", [m["role"] for m in compressed[1:]])
    print()

    print("≈≈≈ 工具结果缓存 ≈≈≈")
    print(run_cached("get_price", sku="A"))     # 真执行
    print(run_cached("get_price", sku="A"))     # 命中缓存
    print(run_cached("get_rating", sku="A"))    # 换工具真执行


if __name__ == "__main__":
    main()