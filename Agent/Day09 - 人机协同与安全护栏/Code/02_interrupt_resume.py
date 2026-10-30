# -*- coding: utf-8 -*-
"""
Day09 - 02 中断与恢复（Interrupt & Resume）

演示内容：
1. 长任务执行到一半需要人类输入 → 保存现场并中断
2. 人类输入到位后 → 从断点恢复，不重跑已完成步骤
3. 超时策略：超过时限自动取消 / 降级

全部离线可运行，用字典模拟状态持久化。
"""

import json
import time
from dataclasses import dataclass, field, asdict


# ============================================================
# 第一部分：可持久化的任务状态
# ============================================================

@dataclass
class TaskState:
    """Agent 任务的执行现场，可随时序列化保存"""
    task_id: str
    goal: str
    plan: list = field(default_factory=list)          # 完整计划
    done: list = field(default_factory=list)          # 已完成步骤的结果
    pending_input: dict | None = None                 # 等待人类输入的请求
    saved_at: float = 0.0

    def save(self) -> str:
        """持久化：真实场景写入 Redis/DB，这里存内存字典并返回 JSON"""
        self.saved_at = time.time()
        data = json.dumps(asdict(self), ensure_ascii=False)
        STATE_STORE[self.task_id] = data
        return data

    @classmethod
    def load(cls, task_id: str) -> "TaskState | None":
        data = STATE_STORE.get(task_id)
        if data is None:
            return None
        d = json.loads(data)
        return cls(**d)


STATE_STORE: dict[str, str] = {}  # 模拟持久化存储


# ============================================================
# 第二部分：带中断的 Agent 执行器
# ============================================================

WAITING_HUMAN = "__WAITING_HUMAN__"
TIMEOUT_SEC = 2.0  # 演示用：超时阈值 2 秒


class InterruptibleAgent:
    """
    可中断的 Agent：
    - 遇到需要人类确认的步骤 → 持久化状态并返回 WAITING_HUMAN
    - resume() 时从断点继续
    """

    # 步骤执行器：每个步骤是一个函数，返回结果或抛出 NeedHuman
    def __init__(self, task_id: str, goal: str, plan: list[dict]):
        self.state = TaskState(task_id=task_id, goal=goal, plan=plan)

    # ---------- 需要人类输入的信号 ----------
    class NeedHuman(Exception):
        def __init__(self, question: str, kind: str):
            self.question = question
            self.kind = kind  # confirm / supply / correct

    # ---------- 模拟步骤执行 ----------
    def _exec_step(self, step: dict) -> str:
        """模拟执行一个步骤，某些步骤需要人类输入"""
        if step.get("needs_human"):
            raise self.NeedHuman(step["question"], step["kind"])
        # 模拟普通步骤的执行结果
        return f"完成：{step['name']}(结果数据...)" if "name" in step else f"完成：{step['action']}"

    # ---------- 主循环 ----------
    def run(self) -> str:
        """
        执行剩余步骤。
        返回 WAITING_HUMAN 表示中断等待人类；否则返回最终结果。
        """
        start_idx = len(self.state.done)  # 断点：已完成 N 步，从第 N+1 步继续
        for step in self.state.plan[start_idx:]:
            try:
                result = self._exec_step(step)
                self.state.done.append(result)
            except self.NeedHuman as nh:
                # 中断：记录等待中的问题并持久化
                self.state.pending_input = {
                    "at_step": self.state.plan.index(step),
                    "step": step,
                    "question": nh.question,
                    "kind": nh.kind,
                }
                self.state.save()
                return WAITING_HUMAN

        self.state.pending_input = None
        return f"任务完成！共 {len(self.state.plan)} 步：\n  " + "\n  ".join(self.state.done)

    # ---------- 恢复 ----------
    def resume(self, human_input: str) -> str:
        """人类输入到位后从断点恢复"""
        pend = self.state.pending_input
        if not pend:
            return "没有待处理的等待项，直接执行剩余计划"

        step = pend["step"]
        kind = pend["kind"]

        # 确认型：批准则继续，拒绝则终止
        if kind == "confirm":
            if human_input.lower() in ("yes", "y", "是", "批准"):
                self.state.done.append(f"[人类批准] {step['action']} -> 继续执行")
            else:
                return "人类拒绝了关键步骤，任务终止（状态已保存，可重新规划）"
        else:  # supply / correct：把人类输入当作步骤产出
            self.state.done.append(f"[人类补充] {human_input}")

        self.state.pending_input = None
        return self.run()  # 从断点继续剩余步骤


# ============================================================
# 第三部分：超时策略
# ============================================================

def check_timeout(state: TaskState, timeout: float = TIMEOUT_SEC) -> str:
    """
    检查等待人类输入是否超时。
    生产环境由定时任务轮询，这里演示三种默认策略。
    """
    if state.pending_input is None:
        return "无等待项"

    waited = time.time() - state.saved_at
    if waited < timeout:
        return f"仍在等待中（已等 {waited:.1f}s < {timeout}s）"

    # 超时：演示降级策略 —— 高危步骤取消，其余继续
    return f"已等待 {waited:.1f}s 超时 -> 默认策略：取消该高危步骤，尝试低风险替代方案"


# ============================================================
# 第四部分：演示
# ============================================================

def main():
    plan = [
        {"action": "搜索供应商报价", },
        {"action": "对比三家报价生成比价表"},
        {"action": "下单采购 5000 元", "needs_human": True,
         "question": "本次采购金额 5000 元，是否批准下单？", "kind": "confirm"},
        {"action": "通知财务备案"},
        {"action": "归档采购记录"},
    ]

    agent = InterruptibleAgent(task_id="T-001", goal="完成办公用品采购", plan=plan)

    print("=" * 56)
    print("第一轮执行：跑到第 3 步（下单）时中断等待人类")
    print("=" * 56)
    result = agent.run()
    print(f"返回值：{result}\n")

    print("--- 中断时的现场（已持久化） ---")
    print(f"已完成：{len(agent.state.done)} 步")
    for d in agent.state.done:
        print(f"  - {d}")
    print(f"等待输入：{agent.state.pending_input['question']}\n")

    # 模拟：先演示超时检查（不真正等待，直接看逻辑）
    print("--- 超时策略检查 ---")
    print(check_timeout(agent.state), "\n")

    print("=" * 56)
    print("第二轮：模拟人类批准后恢复（从断点继续，不重跑前两步）")
    print("=" * 56)
    final = agent.resume("批准")
    print(final, "\n")

    # 验证：确实没有重跑
    print("=" * 56)
    print("验证断点续跑：前两步只执行了一次")
    print("=" * 56)
    rerun_count = sum(1 for d in agent.state.done if "搜索供应商" in d)
    print(f"'搜索供应商' 出现次数 = {rerun_count}（应为 1）")
    print(f"状态存储中的任务数：{len(STATE_STORE)}")


if __name__ == "__main__":
    main()
