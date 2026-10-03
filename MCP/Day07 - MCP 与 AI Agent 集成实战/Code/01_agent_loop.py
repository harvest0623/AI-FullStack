# -*- coding: utf-8 -*-
"""
Day07 - 01 用 MCP 让 Agent 拥有工具能力（离线模拟）

演示多 Server 汇聚成统一工具面，再跑一遍 Agent 决策循环：
观察 → 决策 → 调 MCP 工具 → 回填 → 回复。

离线可运行（用规则函数代替真实 LLM）。
"""

# —— 模拟两个 MCP Server 提供的工具（含归属路由） ——
TOOLS_ROUTE = {
    # Server A：银行
    "get_balance": {"server": "bank", "fn": lambda account: 1000.0,
                    "desc": "查询指定账户余额"},
    "transfer": {"server": "bank", "fn": lambda acc, amt: f"已向{acc}转账{amt}",
                 "desc": "向指定账户转账"},
    # Server B：文件
    "list_files": {"server": "files", "fn": lambda path: ["a.txt", "b.txt", "c.log"],
                   "desc": "列出目录文件"},
}


def discover_all():
    """模拟对每个 Server 做 list_tools，汇聚工具面。"""
    tools = [{"name": k, "server": v["server"], "description": v["desc"]}
             for k, v in TOOLS_ROUTE.items()]
    return tools


def mock_llm_decide(query: str):
    """极简模型决策：识别意图 → 返回 (工具名, 参数)。"""
    if "余额" in query:
        return "get_balance", {"account": "10001"}
    if "文件" in query or "目录" in query:
        return "list_files", {"path": "/docs"}
    if "转账" in query:
        return "transfer", {"acc": "8888", "amt": "200"}
    return None, None


def agent_loop(query: str):
    print(f"  用户：『{query}』")
    tools = discover_all()
    print(f"  [发现] MCP 工具面 → {[(t['name'], t['server']) for t in tools]}")

    name, args = mock_llm_decide(query)
    if name is None:
        print("  [决策] 无需调用工具，直接由模型回答。\n")
        return
    route = TOOLS_ROUTE[name]
    print(f"  [决策] 调用工具 {name}（路由到 {route['server']}）args={args}")
    result = route["fn"](**args)
    print(f"  [执行] {route['server']} 返回 → {result}")
    print(f"  [回复] 模型回答 → 「{result}」\n")


def main():
    print(">> MCP + Agent 决策循环（离线模拟）\n")
    agent_loop("我的账户余额是多少？")
    agent_loop("把/docs里的文件列出来")
    agent_loop("帮我给8888转账200元")
    agent_loop("今天天气怎么样？")  # 不在能力范围内，纯 LLM 回答

    print("=" * 60)
    print("真实落地：")
    print("  · 每个 Server 一个 Client 连接（见 server_bank.py）")
    print("  · mock_llm_decide 替换为真实 LLM 的 tool calling")
    print("  · 工具→Server 的路由表，在真实代码里由『哪个 Client 提供该工具』决定")


if __name__ == "__main__":
    main()