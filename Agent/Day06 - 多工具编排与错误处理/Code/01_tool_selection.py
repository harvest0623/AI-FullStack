"""
01_tool_selection.py
工具选择的准确性：两级路由（先选域，再选工具）。
演示把 12 个工具的"大海捞针"变成 4 选 1。

运行：python 01_tool_selection.py
"""

import json


# ---------------------------------------------------------------------------
# 12 个工具，分属 3 个域
# ---------------------------------------------------------------------------
ALL_TOOLS = {
    # —— 数据域 ——
    "query_sales":    "查询销量数据（周/区域）。当用户问销售额、订单量时用。",
    "query_user":     "查询用户信息（注册/活跃/画像）。当用户问用户数据时用。",
    "query_orders":   "查询订单明细（状态/金额/商品）。当用户问订单详情时用。",
    "calc":           "计算数学表达式。涉及数字计算时用；纯文字问题不要用。",
    # —— 沟通域 ——
    "send_email":     "发送邮件给外部联系人。仅在明确要求发邮件时用。",
    "send_im":        "发送站内消息。仅在明确要求发消息时用。",
    "create_ticket":  "创建工单。需要人工跟进的任务用。",
    "query_kb":       "检索企业知识库文档。找制度/流程/文档时用。",
    # —— 文件域 ——
    "read_file":      "读取文件内容。",
    "write_file":     "写入/覆盖文件（高危：需要审批）。",
    "list_dir":       "列出目录内容。",
    "export_csv":     "把数据导出为 CSV 文件。",
}

DOMAINS = {
    "data":   ["query_sales", "query_user", "query_orders", "calc"],
    "comm":   ["send_email", "send_im", "create_ticket", "query_kb"],
    "file":   ["read_file", "write_file", "list_dir", "export_csv"],
}

DOMAIN_HINTS = {
    "data": "涉及数字、销量、用户、订单、计算的任务",
    "comm": "涉及发送消息、邮件、工单、查资料的任务",
    "file": "涉及读写文件、目录、导出的任务",
}


# ---------------------------------------------------------------------------
# 两级路由
# ---------------------------------------------------------------------------
def route_domain(query: str) -> str:
    """第一级：判断任务域（真实场景由 LLM/分类器完成）。"""
    if any(k in query for k in ("销量", "订单", "用户", "计算", "环比", "多少")):
        return "data"
    if any(k in query for k in ("发", "邮件", "消息", "工单", "知识库", "查资料")):
        return "comm"
    if any(k in query for k in ("文件", "目录", "导出", "读写")):
        return "file"
    return "data"


def select_tool(query: str, domain: str) -> str:
    """第二级：在域内选工具（真实场景由 LLM 完成，此处规则模拟）。"""
    if domain == "data":
        if "环比" in query or "计算" in query:
            return "calc"
        if "订单" in query:
            return "query_orders"
        if "用户" in query:
            return "query_user"
        return "query_sales"
    if domain == "file":
        return "export_csv" if "导出" in query else "read_file"
    return "query_kb" if "知识库" in query else "send_email"


def main():
    print("=" * 62)
    print("两级路由：12 个工具 50 选 1 的困境 -> 域内 4 选 1")
    print("=" * 62)

    queries = [
        "查一下本周各区域销量",
        "算一下环比增长百分之多少",
        "把这个数据导出成 CSV",
        "查一下用户张三的订单",
        "帮我发邮件给运营组",
    ]

    for q in queries:
        domain = route_domain(q)
        tool = select_tool(q, domain)
        exposed = DOMAINS[domain]
        print(f"\n查询：{q}")
        print(f"  一级路由 -> 域 [{domain}]（{DOMAIN_HINTS[domain]}）")
        print(f"  暴露工具：{exposed}（仅 {len(exposed)} 个，而非全部 {len(ALL_TOOLS)} 个）")
        print(f"  二级选择 -> {tool}：{ALL_TOOLS[tool]}")

    print("\n" + "=" * 62)
    print("对比：一次性给模型 12 个工具的清单")
    print("=" * 62)
    for name, desc in ALL_TOOLS.items():
        print(f"  {name:<14} {desc}")
    print("\n  -> 工具越多，描述区分度要求越高，误选率越高；")
    print("     动态注入子集（按域）+ 负面描述（何时不用）是低成本解法。")

    print("\n要点：")
    print("  1. 两级路由：先选域，再在域内选工具（50选1 -> 4选1）")
    print("  2. 描述要含『何时不用』：calc 的『纯文字问题不要用』就是负面示例")
    print("  3. 动态注入：只把相关域的工具发给模型，省 token 又提准确率")


if __name__ == "__main__":
    main()