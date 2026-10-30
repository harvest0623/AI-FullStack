# -*- coding: utf-8 -*-
"""
Day12 - 02 自定义工具与记忆系统

演示内容：
1. 编写两个新工具并注册进框架（扩展性）
2. 长期记忆：第一次任务记住的信息，第二次任务直接使用
3. 工作记忆：单任务内多步观察的串联
"""

from agenthub import AgentHub, Tool, default_tools


# ============================================================
# 第一部分：自定义新工具
# ============================================================

def lookup_supplier(name: str) -> str:
    return f"供应商「{name}」：华北仓，账期 30 天"

def submit_refund(order: str, amount: float) -> str:
    return f"退款申请已提交：{order} 金额 {amount} 元（等待审核）"


CUSTOM_TOOLS = [
    Tool("lookup_supplier", "查询供应商信息", {"name": "供应商名称"}, lookup_supplier, risk="low"),
    Tool("submit_refund", "提交退款申请（高危）", {"order": "订单号", "amount": "金额"},
         submit_refund, risk="high"),
]


# ============================================================
# 第二部分：带长期记忆的扩展 Agent
# ============================================================

class MemoryAwareHub(AgentHub):
    """演示长期记忆：把任务中学到的信息写入长期记忆"""

    def run(self, task: str) -> str:
        # 长期记忆命中：之前学过 SKU 对应的供应商
        if "供应商" in task:
            known = self.memory.recall("supplier")
            if known:
                print(f"  [长期记忆命中] 该商品的供应商是：{known}（不再查询）")
                return f"根据记忆直接回答：{known}"

        result = super().run(task)

        # 任务完成后学习：从观察中提取供应商信息存入长期记忆
        for obs in self.memory.working:
            if "供应商" in obs:
                self.memory.remember("supplier", obs.split("->")[-1].strip())
                print(f"  [长期记忆写入] {obs.split('->')[-1].strip()}")
        return result


# ============================================================
# 演示
# ============================================================

def main():
    hub = MemoryAwareHub()

    print("=" * 56)
    print("1. 注册内置工具 + 自定义工具")
    print("=" * 56)
    hub.register_tools(default_tools() + CUSTOM_TOOLS)
    hub.gate.approve_fn = lambda req: True

    print()
    print("=" * 56)
    print("2. 第一次任务：查询 A100 的库存、价格")
    print("=" * 56)
    r1 = hub.run("帮我查 A100 的库存和价格")
    print(f"\n回答：{r1}")

    print("\n--- 本次任务的工作记忆 ---")
    print(hub.memory.render_context())

    print()
    print("=" * 56)
    print("3. 第二次任务：同样涉及 A100（复用工作流程）")
    print("=" * 56)
    r2 = hub.run("A100 的价格")
    print(f"\n回答：{r2}")

    print()
    print("=" * 56)
    print("4. 使用自定义工具：退款（高危，需审批）")
    print("=" * 56)

    # 这次用真实的审批函数：金额超过 500 拒绝
    def human_approval(req):
        amount = req["params"].get("amount", 0)
        if amount > 500:
            print(f"  [审批门] {req['tool']} 金额 {amount} 元 > 500，拒绝")
            return False
        print(f"  [审批门] {req['tool']} 金额 {amount} 元 <= 500，批准")
        return True

    hub.gate.approve_fn = human_approval

    r3 = hub.run("帮我给订单 ORD-2026 提交 800 元退款")
    print(f"\n回答：{r3}")
    print("（注意：高危工具被审批门拒绝，任务没有执行退款）")

    r4 = hub.run("帮我给订单 ORD-2026 提交 300 元退款")
    print(f"\n回答：{r4}")
    print("（300 元在阈值内，审批通过并执行）")

    print()
    print("=" * 56)
    print("关键结论")
    print("=" * 56)
    print("  1. 新工具只需 Tool(...) 定义 + register，框架即插即用")
    print("  2. 长期记忆让跨任务的信息不用重复查询")
    print("  3. 审批函数可注入任意人机交互逻辑（控制台/网页/飞书卡片）")


if __name__ == "__main__":
    main()
