"""
04_tool_roundtrip.py
Function Calling 完整往返：注册 -> 模型决策 -> 校验 -> 执行 -> 回填 -> 再决策。
用 SimLLM 模拟模型输出（接口对齐真实 LLM 的 tool_calls 结构），
循环直到模型给出最终回答——这就是一个真正的最小 Agent。

运行：python 04_tool_roundtrip.py
"""

import json


# ---------------------------------------------------------------------------
# 1) 工具层（注册表，简化版）
# ---------------------------------------------------------------------------
def query_sales(week: str) -> dict:
    db = {"2024-W01": {"sales": 1200, "orders": 340},
          "2024-W02": {"sales": 980, "orders": 290}}
    if week not in db:
        return {"error": f"周次 {week} 不存在", "available": list(db)}
    return {"week": week, **db[week]}


def calc(expression: str) -> dict:
    try:
        return {"result": round(eval(expression, {"__builtins__": {}}, {}), 2)}
    except Exception as e:
        return {"error": f"表达式无法计算: {e}"}


TOOLS = {
    "query_sales": {
        "func": query_sales,
        "schema": {"type": "object",
                   "properties": {"week": {"type": "string", "description": "周次 YYYY-Www"}},
                   "required": ["week"]},
    },
    "calc": {
        "func": calc,
        "schema": {"type": "object",
                   "properties": {"expression": {"type": "string", "description": "数学表达式"}},
                   "required": ["expression"]},
    },
}


def tool_manifest():
    return [{"name": n, "description": f"工具 {n}", "parameters": t["schema"]}
            for n, t in TOOLS.items()]


# ---------------------------------------------------------------------------
# 2) SimLLM：模拟模型的决策（输出结构与 OpenAI tool_calls 对齐）
# ---------------------------------------------------------------------------
class SimLLM:
    """按脚本输出决策：第1步查W02，第2步查W01，第3步算环比，第4步直答。"""

    def __init__(self):
        self.step = 0

    def chat(self, messages: list, tools: list) -> dict:
        self.step += 1
        if self.step == 1:
            return {"role": "assistant", "content": None,
                    "tool_calls": [{"id": "c1", "name": "query_sales",
                                    "arguments": {"week": "2024-W02"}}]}
        if self.step == 2:
            return {"role": "assistant", "content": None,
                    "tool_calls": [{"id": "c2", "name": "query_sales",
                                    "arguments": {"week": "2024-W01"}}]}
        if self.step == 3:
            return {"role": "assistant", "content": None,
                    "tool_calls": [{"id": "c3", "name": "calc",
                                    "arguments": {"expression": "(980-1200)/1200*100"}}]}
        return {"role": "assistant",
                "content": "W02 销量 980（订单 290），环比 W01（1200）下跌 18.33%。"}


# ---------------------------------------------------------------------------
# 3) 完整往返（Agent 循环）
# ---------------------------------------------------------------------------
def run_agent(user_query: str):
    llm = SimLLM()
    messages = [{"role": "user", "content": user_query}]
    tools = tool_manifest()
    print(f"用户：{user_query}\n")

    for step in range(1, 7):
        # 阶段2：模型决策
        reply = llm.chat(messages, tools)

        # 阶段6(终止)：模型给出最终回答
        if not reply.get("tool_calls"):
            print(f"[Step {step}] 模型最终回答：{reply['content']}")
            messages.append(reply)
            return reply["content"]

        messages.append(reply)
        for call in reply["tool_calls"]:
            name, args = call["name"], call["arguments"]
            print(f"[Step {step}] 模型决策 -> 调用 {name}({json.dumps(args, ensure_ascii=False)})")

            # 阶段3：校验（工具存在 + 必填参数）
            if name not in TOOLS:
                result = {"error": f"未知工具 {name}", "available": list(TOOLS)}
            elif missing := [k for k in TOOLS[name]["schema"].get("required", []) if k not in args]:
                result = {"error": f"缺少必填参数 {missing}"}
            else:
                # 阶段4：执行
                result = TOOLS[name]["func"](**args)

            print(f"           执行结果: {json.dumps(result, ensure_ascii=False)}")

            # 阶段5：回填（tool 消息，带 tool_call_id 关联）
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(result, ensure_ascii=False)})
    return "达到最大步数。"


def main():
    print("=" * 62)
    print("Function Calling 六阶段完整往返")
    print("=" * 62)
    run_agent("上周销量涨了还是跌了？请给出精确数字。")

    print("\n消息序列（messages 数组的演化）：")
    # 简化展示：重新跑一遍只打印结构
    llm = SimLLM()
    msgs = [{"role": "user", "content": "..."}]
    for _ in range(3):
        r = llm.chat(msgs, [])
        msgs.append(r)
        if r.get("tool_calls"):
            for c in r["tool_calls"]:
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": "..."})
    for m in msgs:
        tc = m.get("tool_calls")
        extra = f" tool_calls={[(t['name'], t['arguments']) for t in tc]}" if tc else ""
        print(f"  role={m['role']}{extra}")

    print("\n要点：")
    print("  1. 六阶段：注册(manifest) -> 决策(tool_calls) -> 校验 -> 执行 -> 回填(tool消息) -> 再决策")
    print("  2. tool 消息用 tool_call_id 关联，模型才知道结果属于哪次调用（并行时关键）")
    print("  3. 真实项目把 SimLLM 换成 openai/anthropic SDK 调用，循环代码不变")


if __name__ == "__main__":
    main()