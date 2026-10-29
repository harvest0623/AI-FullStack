"""
02_history_mgmt.py
短时记忆（对话历史）管理：三种策略对比。
- 滑动窗口：直接截断
- 摘要压缩：旧消息压成摘要
- 混合策略：系统提示+目标+摘要+最近K条（生产常用）

运行：python 02_history_mgmt.py
"""

import json


# 模拟一次多轮对话（含大工具结果）
def build_dialog() -> list[dict]:
    return [
        {"role": "system", "content": "你是数据分析助手。"},
        {"role": "user", "content": "帮我分析上月华东区的销售情况。"},   # 任务目标（关键！）
        {"role": "assistant", "content": "好的，先查询数据库。"},
        {"role": "tool", "content": json.dumps({"region": "华东", "sales": 9800,
                                                 "orders": 340, "detail": [("*" * 200)] * 10},
                                                ensure_ascii=False)},
        {"role": "assistant", "content": "华东区上月销量 9800。请告诉我对比基准。"},
        {"role": "user", "content": "和前月对比。"},
        {"role": "tool", "content": json.dumps({"region": "华东", "sales": 8000})},
        {"role": "assistant", "content": "环比增长 22.5%。需要细分的品类数据吗？"},
        {"role": "user", "content": "要，看品类明细。"},
        {"role": "tool", "content": json.dumps({"categories": [{"name": "家电", "sales": 5000},
                                                               {"name": "数码", "sales": 4800}]})},
        {"role": "assistant", "content": "家电 5000、数码 4800，是两大主力。"},
        {"role": "user", "content": "总结一下。"},
    ]


def token_of(msg) -> int:
    """粗略 token 估算（演示用）。"""
    return max(1, len(msg["content"]) // 4)


def total_tokens(msgs) -> int:
    return sum(token_of(m) for m in msgs)


# ---------------------------------------------------------------------------
# 策略一：滑动窗口
# ---------------------------------------------------------------------------
def sliding_window(msgs: list[dict], keep: int = 4) -> list[dict]:
    system = [m for m in msgs if m["role"] == "system"]
    rest = [m for m in msgs if m["role"] != "system"]
    return system + rest[-keep:]


# ---------------------------------------------------------------------------
# 策略二：摘要压缩
# ---------------------------------------------------------------------------
def fake_summarize(msgs: list[dict]) -> str:
    """模拟 LLM 摘要（真实实现是一次 LLM 调用）。"""
    return ("历史摘要：用户要求分析上月华东区销售。已查明：上月销量 9800/订单 340；"
            "前月 8000，环比 +22.5%；品类明细：家电 5000、数码 4800。")


def summary_compress(msgs: list[dict], keep: int = 4) -> list[dict]:
    system = [m for m in msgs if m["role"] == "system"]
    rest = [m for m in msgs if m["role"] != "system"]
    if len(rest) <= keep:
        return msgs
    summary_msg = {"role": "system", "content": fake_summarize(rest[:-keep])}
    return system + [summary_msg] + rest[-keep:]


# ---------------------------------------------------------------------------
# 策略三：混合策略（生产常用）
# ---------------------------------------------------------------------------
def hybrid_strategy(msgs: list[dict], keep: int = 4) -> list[dict]:
    """system + 任务目标(首条 user) + 摘要 + 最近K条 + 工具结果截断。"""
    system = [m for m in msgs if m["role"] == "system"]
    rest = [m for m in msgs if m["role"] != "system"]
    goal = [rest[0]] if rest and rest[0]["role"] == "user" else []

    middle = rest[1:-keep] if len(rest) > keep + 1 else []
    summary = [{"role": "system", "content": fake_summarize(middle)}] if middle else []

    recent = []
    for m in rest[-keep:]:
        m2 = dict(m)
        # 工具大结果截断：只保留结论，丢原始数据
        if m["role"] == "tool":
            try:
                data = json.loads(m["content"])
                data.pop("detail", None)
                m2["content"] = json.dumps(data, ensure_ascii=False)
            except Exception:
                m2["content"] = m["content"][:100]
        recent.append(m2)

    return system + goal + summary + recent


def show(name, msgs):
    print(f"\n[{name}] 共 {len(msgs)} 条，估算 {total_tokens(msgs)} tokens")
    for m in msgs:
        c = m["content"][:56].replace("\n", " ")
        print(f"  {m['role']:<9} {c}")


def main():
    msgs = build_dialog()
    print(f"原始对话：{len(msgs)} 条，估算 {total_tokens(msgs)} tokens")
    show("原始", msgs)

    show("策略1 滑动窗口(保留4)", sliding_window(msgs))
    print("  ⚠ 丢了首条 user（任务目标），Agent 会『忘记自己要干嘛』")

    show("策略2 摘要压缩(保留4)", summary_compress(msgs))
    print("  ✅ 长程要点保留，但摘要有损且多一次 LLM 调用")

    show("策略3 混合策略(生产)", hybrid_strategy(msgs))
    print("  ✅ 目标+摘要+最近细节+工具结果截断，兼顾关键信息与窗口")

    print("\n要点：")
    print("  1. 截断最简单但会丢任务目标；摘要保留要点但贵")
    print("  2. 混合策略 = system + 目标 + 摘要 + 最近K条 + 工具结果瘦身")
    print("  3. 工具返回的大 JSON 必须截断/结论化后再入历史（本例 detail 被剥离）")


if __name__ == "__main__":
    main()