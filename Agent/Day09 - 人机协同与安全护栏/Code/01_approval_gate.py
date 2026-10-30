# -*- coding: utf-8 -*-
"""
Day09 - 01 审批门（Approval Gate）

演示内容：
1. 工具风险分级（低/中/高三级）
2. 高危工具调用前的审批请求生成
3. 人类审批的三种响应：批准 / 拒绝 / 修改后批准
4. 拒绝后 Agent 的应对：尝试替代方案 / 优雅终止

全部用规则模拟，不依赖任何 LLM API，离线可运行。
"""

from dataclasses import dataclass, field


# ============================================================
# 第一部分：工具风险分级
# ============================================================

# 工具风险等级表：工具名 -> 风险等级
TOOL_RISK = {
    "read_file":      "low",
    "search_web":     "low",
    "write_report":   "low",
    "send_email":     "medium",   # 对外发送，中等风险
    "delete_file":    "high",     # 不可逆删除，高风险
    "transfer_money": "high",     # 资金操作，高风险
    "deploy_code":    "high",     # 生产部署，高风险
}


@dataclass
class ToolCall:
    """一次工具调用请求"""
    tool: str
    params: dict
    reason: str  # Agent 给出的调用理由


@dataclass
class ApprovalRequest:
    """审批请求：发送给人类审批者的结构化信息"""
    call: ToolCall
    risk: str
    impact: str          # 影响描述
    reversible: bool     # 是否可逆
    options: list = field(default_factory=list)

    def render(self) -> str:
        """渲染成人类易读的审批卡片"""
        lines = [
            "=" * 52,
            f"【审批请求】风险等级：{self.risk.upper()}",
            f"操作    ：{self.call.tool}",
            f"参数    ：{self.call.params}",
            f"理由    ：{self.call.reason}",
            f"影响    ：{self.impact}",
            f"可逆性  ：{'可逆' if self.reversible else '不可逆'}",
            "选项    ：[approve] 批准 / [reject] 拒绝 / [modify <k>=<v>] 修改后批准",
            "=" * 52,
        ]
        return "\n".join(lines)


def assess_risk(call: ToolCall) -> tuple:
    """
    风险评估：工具等级 + 参数细节动态调整
    返回 (风险等级, 是否可逆, 影响描述)
    """
    base = TOOL_RISK.get(call.tool, "medium")

    # 参数级风险加成：转账金额超过 1000 升级为 high
    if call.tool == "transfer_money":
        amount = call.params.get("amount", 0)
        if amount > 1000:
            base = "high"

    reversible_map = {
        "delete_file": (False, "文件将被永久删除，无法恢复"),
        "transfer_money": (False, "资金转出后无法自动撤回"),
        "deploy_code": (False, "生产环境变更，回滚成本高"),
        "send_email": (False, "邮件发出后无法撤回"),
    }
    reversible, impact = reversible_map.get(call.tool, (True, "仅产生本地变更，可随时撤销"))
    return base, reversible, impact


# ============================================================
# 第二部分：审批门 Agent
# ============================================================

# 模拟人类审批者：不同场景下的审批决策
def human_approver(req: ApprovalRequest) -> dict:
    """
    模拟人类的审批响应。
    返回 {"action": "approve"|"reject"|"modify", "reason": str, "params": dict}
    """
    tool = req.call.tool

    if tool == "delete_file":
        return {
            "action": "reject",
            "reason": "生产数据禁止直接删除，请改为归档",
            "params": req.call.params,
        }
    if tool == "transfer_money":
        # 金额太大，修改后批准：先转一半验证
        return {
            "action": "modify",
            "reason": "金额超预期，先小额验证账户无误",
            "params": {**req.call.params, "amount": 100},  # 10000 -> 100
        }
    if tool == "send_email":
        return {"action": "approve", "reason": "收件人是内部同事，放行", "params": req.call.params}

    return {"action": "approve", "reason": "低风险操作", "params": req.call.params}


class AgentWithGate:
    """带审批门的 Agent：高危操作必须人工确认后才执行"""

    def __init__(self, approver):
        self.approver = approver
        self.executed: list[str] = []

    def run_step(self, call: ToolCall) -> str:
        """执行一步：先过审批门"""
        risk, reversible, impact = assess_risk(call)

        # 低风险：免审直接执行
        if risk == "low":
            return self._execute(call, note="低风险，免审执行")

        # 中/高风险：生成审批请求，等人类决策
        req = ApprovalRequest(call=call, risk=risk, impact=impact, reversible=reversible)
        print(req.render())
        decision = self.approver(req)
        print(f"[人类决策] {decision['action'].upper()} - {decision['reason']}")

        if decision["action"] == "approve":
            return self._execute(call, note="审批通过后执行")

        if decision["action"] == "modify":
            modified = ToolCall(call.tool, decision["params"], f"（按审批意见修改）{call.reason}")
            return self._execute(modified, note="按修改后的参数执行")

        # 拒绝：尝试替代方案
        return self._handle_rejection(call, decision["reason"])

    def _execute(self, call: ToolCall, note: str) -> str:
        self.executed.append(f"{call.tool}({call.params})")
        return f"[执行成功] {call.tool} {call.params} | {note}"

    def _handle_rejection(self, call: ToolCall, reason: str) -> str:
        """被拒绝后：尝试低风险替代方案，没有则优雅终止"""
        if call.tool == "delete_file":
            archive = ToolCall(
                "write_report",
                {"path": call.params["path"], "content": "归档标记"},
                "删除被拒，改为归档记录",
            )
            result = self.run_step(archive)  # 低风险，免审
            return f"[拒绝处理] {reason} -> 已切换替代方案：{result}"

        return f"[终止] {call.tool} 被拒绝且无替代方案，任务终止。拒绝原因：{reason}"


# ============================================================
# 第三部分：演示
# ============================================================

def main():
    agent = AgentWithGate(human_approver)

    calls = [
        ToolCall("read_file", {"path": "/data/report.csv"}, "读取数据以完成分析"),
        ToolCall("send_email", {"to": "colleague@corp.com", "subject": "周报"}, "向同事发送周报"),
        ToolCall("delete_file", {"path": "/data/old_logs/"}, "清理过期日志释放空间"),
        ToolCall("transfer_money", {"to": "supplier", "amount": 10000}, "支付供应商货款"),
    ]

    print("=" * 52)
    print("审批门演示：4 个工具调用，观察哪些需要人工确认")
    print("=" * 52)
    for i, c in enumerate(calls, 1):
        print(f"\n--- 步骤 {i} ---")
        print(agent.run_step(c))

    print("\n" + "=" * 52)
    print("最终实际执行的操作：")
    for e in agent.executed:
        print(f"  - {e}")
    print("=" * 52)


if __name__ == "__main__":
    main()
