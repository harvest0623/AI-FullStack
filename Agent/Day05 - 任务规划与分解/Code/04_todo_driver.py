"""
04_todo_driver.py
TODO 清单驱动执行引擎：Planner 产出清单 -> Executor 逐项勾销 ->
过程中允许动态追加子任务（子目标分解）与判定完成。

运行：python 04_todo_driver.py
"""

import json
from dataclasses import dataclass, field


@dataclass
class Todo:
    text: str
    status: str = "pending"            # pending / in_progress / done / cancelled
    note: str = ""


class TodoDriver:
    """清单驱动的执行器：类似 LangGraph 的 todo 状态管理。"""

    def __init__(self, goal: str):
        self.goal = goal
        self.todos: list[Todo] = []

    def plan(self, items: list[str]):
        self.todos = [Todo(t) for t in items]

    def next_todo(self) -> Todo | None:
        for t in self.todos:
            if t.status == "pending":
                return t
        return None

    def start(self, todo: Todo):
        todo.status = "in_progress"
        self.render(f"开始：{todo.text}")

    def complete(self, todo: Todo, note: str = ""):
        todo.status, todo.note = "done", note
        self.render(f"完成：{todo.text}" + (f"（{note}）" if note else ""))

    def add_dynamic(self, text: str, reason: str = ""):
        """执行中发现需要补充子任务。"""
        self.todos.append(Todo(text))
        self.render(f"追加：{text}" + (f"（原因：{reason}）" if reason else ""))

    def cancel(self, todo: Todo, reason: str):
        todo.status, todo.note = "cancelled", reason
        self.render(f"取消：{todo.text}（{reason}）")

    def render(self, action: str = ""):
        if action:
            print(f"    >> {action}")
        for i, t in enumerate(self.todos, 1):
            icon = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]",
                    "cancelled": "[-]"}[t.status]
            print(f"  {icon} {i}. {t.text}" + (f"  # {t.note}" if t.note else ""))


# ---------------------------------------------------------------------------
# 模拟工具
# ---------------------------------------------------------------------------
def query_sales(week): return {"2024-W03": 1450, "2024-W02": 980}[week]


def main():
    print("=" * 62)
    print("TODO 清单驱动执行")
    print("=" * 62)
    driver = TodoDriver("完成月度销售分析报告")

    # 1) Planner 产出清单
    driver.plan([
        "查询本月销量",
        "查询上月销量",
        "计算环比",
        "撰写报告结论",
    ])
    print("初始清单：")
    driver.render()

    # 2) 执行第 1 项
    t1 = driver.next_todo()
    driver.start(t1)
    v1 = query_sales("2024-W03")
    driver.complete(t1, note=f"1450")

    # 3) 执行第 2 项时发现需要补充子任务
    t2 = driver.next_todo()
    driver.start(t2)
    v2 = query_sales("2024-W02")
    driver.complete(t2, note=f"980")
    driver.add_dynamic("环比出现下滑，补充：查询品类结构", reason="环比 -32%？需要看构成")

    # 4) 动态追加的子任务被排在末尾，继续按序执行
    t3 = driver.next_todo()
    driver.start(t3)
    mom = round((v1 - v2) / v2 * 100, 1)
    driver.complete(t3, note=f"{mom}%")

    # 5) 假设品类结构查询因权限不足被取消
    t4 = next(t for t in driver.todos if t.status == "pending" and "品类" in t.text)
    driver.cancel(t4, "权限不足，报告中注明")

    # 6) 最后一项：撰写结论
    t5 = driver.next_todo()
    driver.start(t5)
    driver.complete(t5, note=f"本月 1450，环比 {mom}%（品类结构待补）")

    print("\n最终清单状态：")
    driver.render()
    done = sum(1 for t in driver.todos if t.status == "done")
    print(f"\n完成 {done}/{len(driver.todos)} 项，取消 1 项（已注明原因）")

    print("\n要点：")
    print("  1. 清单即状态机：pending -> in_progress -> done/cancelled")
    print("  2. 执行中可动态追加子任务（子目标分解），清单是活文档")
    print("  3. 取消而非删除：保留痕迹 + 原因，供最终汇报与审计")
    print("  4. LangGraph 的 plan-and-execute 本质就是这套 [ ]/[x] 状态推进")


if __name__ == "__main__":
    main()