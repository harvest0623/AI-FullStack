# -*- coding: utf-8 -*-
"""
Day10 - 02 轨迹日志（Trajectory Log）

演示内容：
1. 请求级日志：trace_id、用户输入、最终输出、总耗时
2. 步骤级日志：每轮循环的思考/行动/观察/Token/耗时
3. 依赖级日志：LLM 与工具的原始请求响应
4. 结构化 JSON 输出（生产可直接接入 ELK / Loki）

离线可运行。
"""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict


# ============================================================
# 第一部分：日志数据结构
# ============================================================

@dataclass
class StepLog:
    """步骤级：Agent 每轮循环"""
    step: int
    thought: str
    action: str
    params: dict
    observation: str
    tokens: int
    duration_ms: float


@dataclass
class DepsLog:
    """依赖级：LLM 调用 / 外部工具的原始请求"""
    kind: str          # llm | tool
    name: str
    request: dict
    response: dict
    duration_ms: float


@dataclass
class RequestLog:
    """请求级：一次用户请求的完整记录"""
    trace_id: str
    user: str
    input: str
    output: str | None = None
    success: bool = True
    total_tokens: int = 0
    total_ms: float = 0.0
    steps: list = field(default_factory=list)
    deps: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# ============================================================
# 第二部分：带日志的 Agent 执行器
# ============================================================

class TracedAgent:
    """
    模拟一个 3 步 Agent，执行过程全程记录三层日志。
    """

    def __init__(self):
        self.log: RequestLog | None = None

    def run(self, user: str, task_input: str) -> str:
        self.log = RequestLog(trace_id=f"tr-{uuid.uuid4().hex[:8]}", user=user, input=task_input)
        t0 = time.time()

        # --- 第 1 步：思考 + LLM 调用 ---
        s1 = self._record_dep("llm", "gpt-sim", {"prompt": f"分析任务：{task_input}"},
                              {"thought": "先查询库存数据"}, 300)
        step1 = StepLog(1, "先查询库存数据", "query_inventory",
                        {"sku": "A100"}, "库存 42 件", s1, 320)
        self._append(step1)

        # --- 第 2 步：调用数据库工具 ---
        s2 = self._record_dep("tool", "db_query",
                              {"sql": "SELECT * FROM inventory WHERE sku='A100'"},
                              {"rows": 42}, 150)
        step2 = StepLog(2, "拿到库存，再查价格", "query_price",
                        {"sku": "A100"}, "单价 99 元", 0, 160)
        self._append(step2)

        # --- 第 3 步：LLM 生成最终回答 ---
        s3 = self._record_dep("llm", "gpt-sim",
                              {"prompt": "库存42件单价99元，生成回答"},
                              {"answer": "可下单，总价 4158 元"}, 400)
        step3 = StepLog(3, "信息齐全，生成回答", "finish",
                        {}, "可下单，总价 4158 元", s3, 420)
        self._append(step3)

        # --- 请求级收尾 ---
        self.log.output = "可下单，总价 4158 元（42 件 x 99 元）"
        self.log.total_ms = (time.time() - t0) * 1000
        self.log.total_tokens = sum(s.tokens for s in self.log.steps)
        return self.log.output

    def _append(self, step: StepLog):
        self.log.steps.append(step)

    def _record_dep(self, kind: str, name: str, req: dict, resp: dict, dur: float) -> int:
        self.log.deps.append(DepsLog(kind, name, req, resp, dur))
        return 180  # 模拟该依赖的 token 消耗


# ============================================================
# 第三部分：日志查询示例（排障场景）
# ============================================================

def failure_replay(agent_log: RequestLog) -> str:
    """
    模拟排障：任务失败了，从轨迹日志定位失败步骤。
    """
    # 找出观察结果为异常的步骤
    failed = [s for s in agent_log.steps if "ERROR" in s.observation or "超时" in s.observation]
    if not failed:
        return "无失败步骤"
    s = failed[0]
    return f"定位失败：第 {s.step} 步调用 {s.action}({s.params}) 时返回「{s.observation}」"


# ============================================================
# 演示
# ============================================================

def main():
    agent = TracedAgent()

    print("=" * 56)
    print("正常执行一次任务，产出完整轨迹日志")
    print("=" * 56)
    result = agent.run(user="u_1001", task_input="帮我检查 A100 还能订多少")
    print(f"最终回答：{result}\n")

    print("--- 轨迹日志（结构化 JSON） ---")
    print(agent.log.to_json())

    print()
    print("=" * 56)
    print("排障演示：人为制造一个失败步骤后回放")
    print("=" * 56)
    bad_log = RequestLog(trace_id="tr-bad01", user="u_1002", input="查库存")
    bad_log.steps.append(StepLog(1, "先查库存", "query_inventory",
                                  {"sku": "B200"}, "ERROR: 连接超时", 120, 5000))
    print(failure_replay(bad_log))

    print()
    print("=" * 56)
    print("三层日志的用途总结")
    print("=" * 56)
    print("  请求级 -> 用户说没成功？先看这层（对账入口）")
    print("  步骤级 -> 哪一轮循环出错？（定位失败步骤）")
    print("  依赖级 -> LLM 返回了什么/工具原始响应？（深挖根因）")


if __name__ == "__main__":
    main()
