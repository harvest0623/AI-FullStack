# -*- coding: utf-8 -*-
"""
Day12 - AgentHub：把 12 天所学的核心机制组装成一个微型 Agent 框架

组件构成（全部来自前面的课程）：
  ToolRegistry     (Day03) 工具注册、schema 校验、白名单
  Memory           (Day04) 工作记忆 + 长期记忆
  Planner          (Day05) 任务分解
  ReActLoop        (Day02) 思考-行动-观察循环
  Guard            (Day09) 输入/行为/输出三层护栏
  ApprovalGate     (Day09) 高危操作人工审批
  TrajectoryLogger (Day10) 步骤级轨迹日志

LLM 用规则模拟（识别任务类型选择工具），生产中换成 API 调用即可。
完全离线可运行，零依赖（仅标准库）。
"""

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional


# ============================================================
# 组件 1：工具注册表（Day03 工具调用与 Function Calling）
# ============================================================

@dataclass
class Tool:
    name: str
    description: str
    params_schema: dict          # 参数名 -> 类型描述
    handler: callable
    risk: str = "low"            # low / high（供审批门使用）


class ToolRegistry:
    """工具的注册-发现-调用三段式，含 schema 校验与白名单"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> str:
        self._tools[tool.name] = tool
        return f"已注册工具：{tool.name}（{tool.risk}风险）"

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def validate(self, tool: Tool, params: dict) -> str | None:
        """schema 校验：缺失必需参数返回错误信息"""
        for pname in tool.params_schema:
            if pname not in params:
                return f"缺少必需参数：{pname}"
        return None

    def names(self) -> list[str]:
        return list(self._tools)


# ============================================================
# 组件 2：记忆系统（Day04 Agent记忆系统）
# ============================================================

class Memory:
    """工作记忆（当前任务的上下文）+ 长期记忆（跨任务偏好）"""

    def __init__(self):
        self.working: list[str] = []       # 本任务的观察序列
        self.longterm: dict[str, str] = {} # 跨任务的用户偏好

    def add_observation(self, obs: str):
        self.working.append(obs)

    def remember(self, key: str, value: str):
        self.longterm[key] = value

    def recall(self, key: str) -> str | None:
        return self.longterm.get(key)

    def render_context(self) -> str:
        return "\n".join(f"  观察{i}: {o}" for i, o in enumerate(self.working, 1))

    def reset_working(self):
        self.working = []


# ============================================================
# 组件 3：规划器（Day05 任务规划与分解）
# ============================================================

@dataclass
class Step:
    action: str        # 工具名
    params: dict
    description: str


class Planner:
    """
    模拟 LLM 的任务分解：
    识别任务文本中提到的需求，输出有序步骤（先查后算再执行）。
    """

    def plan(self, task: str, available_tools: list[str]) -> list[Step]:
        steps = []
        # 查询类步骤（只注册了才用）
        if "库存" in task or "查" in task:
            if "query_inventory" in available_tools:
                steps.append(Step("query_inventory", {"sku": self._extract_sku(task)}, "查询库存"))
        if "价格" in task or "报价" in task:
            if "query_price" in available_tools:
                steps.append(Step("query_price", {"sku": self._extract_sku(task)}, "查询价格"))
        if "物流" in task or "快递" in task:
            if "query_logistics" in available_tools:
                steps.append(Step("query_logistics", {"order": "ORD-1"}, "查询物流"))
        if "供应商" in task:
            if "lookup_supplier" in available_tools:
                steps.append(Step("lookup_supplier", {"name": "华北供应商"}, "查询供应商"))
        if "退款" in task:
            if "submit_refund" in available_tools:
                m = re.search(r"(\d+(?:\.\d+)?)\s*元", task)
                amount = float(m.group(1)) if m else 0.0
                m2 = re.search(r"(ORD[-\w]+)", task)
                order = m2.group(1) if m2 else "ORD-1"
                steps.append(Step("submit_refund", {"order": order, "amount": amount}, "提交退款"))
        # 高危执行类步骤放最后
        if "下单" in task or "购买" in task:
            if "place_order" in available_tools:
                steps.append(Step("place_order",
                                  {"sku": self._extract_sku(task), "qty": self._extract_qty(task)},
                                  "下单采购"))
        if "发票" in task:
            if "create_invoice" in available_tools:
                steps.append(Step("create_invoice", {"order": "ORD-1"}, "开具发票"))
        return steps

    @staticmethod
    def _extract_sku(task: str) -> str:
        m = re.search(r"[A-Z]\d{2,4}", task)
        return m.group(0) if m else "A100"

    @staticmethod
    def _extract_qty(task: str) -> int:
        m = re.search(r"(\d+)\s*(个|件|台)", task)
        return int(m.group(1)) if m else 1


# ============================================================
# 组件 4：护栏（Day09 人机协同与安全护栏）
# ============================================================

class Guard:
    """输入 / 行为 / 输出三层护栏"""

    INJECTION = [r"忽略.{0,4}指令", r"打印.{0,4}(提示词|prompt)", r"你现在是管理员"]

    def input_check(self, text: str) -> str | None:
        """输入护栏：返回 None 表示放行，否则返回拦截原因"""
        for pat in self.INJECTION:
            if re.search(pat, text):
                return f"输入护栏：疑似注入攻击（命中 [{pat}]）"
        return None

    def behavior_check(self, tool: Tool, params: dict) -> str | None:
        """行为护栏：路径越界 / 金额上限"""
        if "path" in params and not params["path"].startswith("/data"):
            return f"行为护栏：路径越界 {params['path']}"
        if "qty" in params and params["qty"] > 1000:
            return f"行为护栏：数量 {params['qty']} 超过单笔上限 1000"
        return None

    def output_check(self, text: str) -> str:
        """输出护栏：手机号脱敏（最后防线，从严）"""
        return re.sub(r"1[3-9]\d{9}", "1********78", text)


# ============================================================
# 组件 5：审批门（Day09）
# ============================================================

class ApprovalGate:
    """高危工具调用前的人工审批。approve_fn 由外部注入（人机交互点）"""

    def __init__(self, approve_fn: Optional[Callable] = None):
        self.approve_fn = approve_fn or (lambda req: True)  # 默认自动批准（演示用）

    def check(self, tool: Tool, params: dict, reason: str) -> bool:
        if tool.risk != "high":
            return True
        req = {"tool": tool.name, "params": params, "reason": reason}
        return bool(self.approve_fn(req))


# ============================================================
# 组件 6：轨迹日志（Day10 Agent服务化与可观测）
# ============================================================

@dataclass
class TrajectoryLogger:
    trace_id: str
    steps: list = field(default_factory=list)

    def log(self, step_no: int, phase: str, detail: str, blocked: bool = False):
        entry = {"step": step_no, "phase": phase, "detail": detail, "blocked": blocked,
                 "ts": round(time.time() * 1000) % 100000}
        self.steps.append(entry)

    def render(self) -> str:
        lines = [f"轨迹日志 trace_id={self.trace_id}（共 {len(self.steps)} 条）"]
        for e in self.steps:
            mark = "[拦截]" if e["blocked"] else "      "
            lines.append(f"  {mark} #{e['step']} {e['phase']:<6} {e['detail']}")
        return "\n".join(lines)


# ============================================================
# 组件 7：ReAct 循环 + 总装（Day02 核心循环）
# ============================================================

class AgentHub:
    """
    总装入口：串起所有组件。
    run(task) 内部流程：
      输入护栏 -> 规划器 -> 逐步 ReAct（思考/行动/观察）
      -> 行为护栏 -> 审批门 -> 工具调用 -> 记忆
      -> 输出护栏 -> 轨迹日志
    """

    MAX_STEPS = 8  # 循环上限（防失控）

    def __init__(self, approve_fn: Optional[Callable] = None):
        self.tools = ToolRegistry()
        self.memory = Memory()
        self.planner = Planner()
        self.guard = Guard()
        self.gate = ApprovalGate(approve_fn)
        self.logger: TrajectoryLogger | None = None

    def register_tools(self, tool_list: list[Tool]):
        for t in tool_list:
            print(f"  {self.tools.register(t)}")

    def run(self, task: str) -> str:
        self.logger = TrajectoryLogger(trace_id=f"tr-{uuid.uuid4().hex[:8]}")
        self.memory.reset_working()
        step_no = 0

        # ---- 输入护栏 ----
        step_no += 1
        blocked = self.guard.input_check(task)
        if blocked:
            self.logger.log(step_no, "输入护栏", blocked, blocked=True)
            return f"任务被拒绝：{blocked}"

        # ---- 规划 ----
        step_no += 1
        steps = self.planner.plan(task, self.tools.names())
        self.logger.log(step_no, "规划", f"分解为 {len(steps)} 步：{[s.action for s in steps]}")
        if not steps:
            return "无法识别任务需求（没有可用的工具匹配）"

        # ---- ReAct 循环 ----
        for step in steps[: self.MAX_STEPS]:
            step_no += 1
            # 思考
            self.logger.log(step_no, "思考", f"需要执行：{step.description}（调用 {step.action}）")

            # 行动前：查工具 -> 行为护栏 -> 审批门
            tool = self.tools.get(step.action)
            if tool is None:
                self.memory.add_observation(f"工具 {step.action} 未注册，跳过")
                self.logger.log(step_no, "观察", f"工具未注册，跳过", blocked=True)
                continue

            err = self.guard.behavior_check(tool, step.params)
            if err:
                self.logger.log(step_no, "行为护栏", err, blocked=True)
                self.memory.add_observation(f"{err}")
                continue

            if not self.gate.check(tool, step.params, step.description):
                self.logger.log(step_no, "审批门", f"{tool.name} 高危操作未获批准", blocked=True)
                self.memory.add_observation("高危操作被拒绝")
                continue

            # 校验参数
            verr = self.tools.validate(tool, step.params)
            if verr:
                self.logger.log(step_no, "参数校验", verr, blocked=True)
                continue

            # 行动：调用工具
            observation = tool.handler(**step.params)
            self.memory.add_observation(f"{step.action} -> {observation}")
            self.logger.log(step_no, "观察", f"{step.action}({step.params}) => {observation}")

        # ---- 汇总与输出护栏 ----
        step_no += 1
        summary = self._summarize(task)
        safe = self.guard.output_check(summary)
        self.logger.log(step_no, "输出护栏", "手机号等敏感信息已脱敏" if safe != summary else "无需脱敏")
        return safe

    def _summarize(self, task: str) -> str:
        """模拟 LLM 汇总：把所有观察整合成回答"""
        obs = self.memory.working
        if not obs:
            return f"关于「{task}」：所有步骤均被拦截，无可用结果。"
        body = "；".join(o.split("->")[-1].strip() for o in obs)
        return f"关于「{task}」的处理结果：{body}。"


# ============================================================
# 内置示例工具（供演示脚本使用）
# ============================================================

def _mock_inventory(sku: str) -> str:
    return f"{sku} 库存 42 件"

def _mock_price(sku: str) -> str:
    return f"{sku} 单价 99 元"

def _mock_order(sku: str, qty: int) -> str:
    return f"订单创建成功：{sku} x {qty}，总价 {99 * qty} 元"

def _mock_logistics(order: str) -> str:
    return f"{order} 已发货，预计 3 天送达，联系人手机 13812345678"

def _mock_invoice(order: str) -> str:
    return f"{order} 的电子发票已开具"


def default_tools() -> list[Tool]:
    """返回一组内置工具"""
    return [
        Tool("query_inventory", "查询商品库存", {"sku": "商品编号"}, _mock_inventory, risk="low"),
        Tool("query_price", "查询商品价格", {"sku": "商品编号"}, _mock_price, risk="low"),
        Tool("place_order", "创建采购订单（高危）", {"sku": "商品编号", "qty": "数量"},
             _mock_order, risk="high"),
        Tool("query_logistics", "查询订单物流", {"order": "订单号"}, _mock_logistics, risk="low"),
        Tool("create_invoice", "开具发票（高危）", {"order": "订单号"}, _mock_invoice, risk="high"),
    ]
