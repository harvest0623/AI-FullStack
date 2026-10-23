"""
01_agent_intro.py
Chatbot vs Agent：同一个任务，两种系统的行为对比。

- Chatbot：一次性生成文本，无真实数据来源，可能幻觉。
- Agent：循环决策 -> 调用工具 -> 基于观察回答。

运行：python 01_agent_intro.py（纯离线，无需任何依赖）
"""

import json


# ---------------------------------------------------------------------------
# 模拟世界：一个微型"企业数据"环境（Agent 的工具将访问它，Chatbot 不会）
# ---------------------------------------------------------------------------
SALES_DB = {
    "2024-W01": {"sales": 1200, "orders": 340},
    "2024-W02": {"sales": 980, "orders": 290},   # 注意：本周下跌
    "2024-W03": {"sales": 1450, "orders": 410},
}


def query_sales(week: str) -> str:
    """工具：查询某周真实销量。"""
    row = SALES_DB.get(week)
    return json.dumps({"week": week, **row}, ensure_ascii=False) if row else json.dumps(
        {"error": f"未找到周 {week}", "available": list(SALES_DB)}, ensure_ascii=False)


def query_orders(week: str) -> str:
    """工具：查询某周订单量。"""
    return query_sales(week)  # 同一数据源，演示用


# ---------------------------------------------------------------------------
# 1. Chatbot：直接"背答案"（模型记忆里 2024-W02 涨了——是错的）
# ---------------------------------------------------------------------------
def chatbot_answer(question: str) -> str:
    return ("根据我的了解，上周（2024-W02）销量上涨了约 15%，达到约 1500，"
            "整体表现非常不错！")   # ← 幻觉：与真实数据不符


# ---------------------------------------------------------------------------
# 2. Agent：最小循环（感知->思考->行动->观察），这里用规则模拟"思考"
# ---------------------------------------------------------------------------
def agent_answer(question: str) -> str:
    steps = []

    # 第 1 步：思考需要真实数据 -> 行动：查销量
    steps.append(("Thought", "用户问上周销量，我不能凭记忆回答，先查数据库。"))
    obs1 = query_sales("2024-W02")
    steps.append(("Action", "query_sales(week='2024-W02')"))
    steps.append(("Observation", obs1))

    # 第 2 步：思考需要对比基线 -> 行动：再查上周
    steps.append(("Thought", "只看绝对值不够，用户说『涨了还是跌了』，需要对比前一周。"))
    obs2 = query_sales("2024-W01")
    steps.append(("Action", "query_sales(week='2024-W01')"))
    steps.append(("Observation", obs2))

    # 第 3 步：基于两份观察作答
    cur, prev = json.loads(obs1), json.loads(obs2)
    delta = (cur["sales"] - prev["sales"]) / prev["sales"] * 100
    answer = (f"2024-W02 销量 {cur['sales']}（订单 {cur['orders']}），"
              f"相比 W01 的 {prev['sales']} 实际{'下跌' if delta < 0 else '上涨'}了 {abs(delta):.1f}%。")

    # 打印轨迹
    print("Agent 轨迹：")
    for kind, content in steps:
        print(f"  [{kind:<11}] {content}")
    return answer


def main():
    q = "上周销量涨了还是跌了？"

    print("=" * 60)
    print("问题：", q)
    print("=" * 60)

    print("\n--- Chatbot（无工具，凭模型记忆直答） ---")
    print("回答：", chatbot_answer(q))
    print("点评：看似自信，实际与真实数据不符（幻觉）。")

    print("\n--- Agent（有工具，先查再答） ---")
    print("回答：", agent_answer(q))
    print("\n点评：每个结论都有 Observation 撑腰，可验证、可回放。")
    print("核心差异：Chatbot 输出文本；Agent 输出『经过验证的事实』并改变了世界（查询发生）。")


if __name__ == "__main__":
    main()