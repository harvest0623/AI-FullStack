"""
02_agent_anatomy.py
Agent 四大组成（LLM 大脑 / 工具 / 记忆 / 规划）的最小可运行骨架。
用规则模拟 LLM 决策，展示组件如何拼装成一个完整 Agent。

运行：python 02_agent_anatomy.py
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 组件一：工具（Tools）—— Agent 的双手
# ---------------------------------------------------------------------------
@dataclass
class Tool:
    name: str
    description: str
    func: callable

    def run(self, **kwargs):
        return self.func(**kwargs)


def tool_search(query: str) -> str:
    return f"搜索结果：关于『{query}』的 3 条要点 …"


def tool_calc(expression: str) -> str:
    try:
        return f"计算结果：{expression} = {eval(expression, {'__builtins__': {}}, {}) }"
    except Exception as e:
        return f"计算失败：{e}"


TOOLS = [
    Tool("search", "搜索互联网获取实时信息", tool_search),
    Tool("calc", "计算数学表达式", tool_calc),
]


# ---------------------------------------------------------------------------
# 组件二：记忆（Memory）—— Agent 的经验
# ---------------------------------------------------------------------------
@dataclass
class Memory:
    short_term: list = field(default_factory=list)   # 短时：本轮任务的轨迹
    long_term: dict = field(default_factory=dict)    # 长时：跨会话键值

    def add(self, role, content):
        self.short_term.append({"role": role, "content": content})

    def remember(self, key, value):
        self.long_term[key] = value

    def recall(self, key):
        return self.long_term.get(key)


# ---------------------------------------------------------------------------
# 组件三：规划（Planning）—— Agent 的路线图
# ---------------------------------------------------------------------------
@dataclass
class Planner:
    goal: str

    def make_plan(self) -> list[str]:
        if "对比" in self.goal or "比较" in self.goal:
            return ["搜索获取资料", "计算关键指标", "综合对比并总结"]
        return ["搜索获取资料", "总结回答"]


# ---------------------------------------------------------------------------
# 组件四：LLM 大脑（Brain）—— 每步的决策器（此处用规则模拟）
# ---------------------------------------------------------------------------
class SimBrain:
    """模拟 LLM：根据当前进度，决定下一步调哪个工具/参数。"""

    def decide(self, plan: list[str], done: list[str]) -> tuple:
        step = plan[len(done)]
        if "搜索" in step:
            return "search", {"query": "2024 新能源汽车销量数据"}
        if "计算" in step:
            return "calc", {"expression": "1450 - 1200"}
        return None  # 无需工具，直接总结


class Agent:
    """把四大组件拼成完整 Agent：循环执行计划直至完成。"""

    def __init__(self, goal: str):
        self.tools = {t.name: t for t in TOOLS}
        self.memory = Memory()
        self.planner = Planner(goal)
        self.brain = SimBrain()

    def run(self):
        plan = self.planner.make_plan()
        print(f"目标：{self.planner.goal}")
        print(f"规划：{plan}\n")

        done = []
        for i, step in enumerate(plan, 1):
            print(f"Step {i}/{len(plan)}：{step}")
            decision = self.brain.decide(plan, done)
            if decision is None:
                observation = "（LLM 直接基于已有信息总结）"
                print(f"  [Thought] 信息已足够，直接总结")
            else:
                name, kwargs = decision
                print(f"  [Thought] 需要外部能力 -> 调用工具 {name}({kwargs})")
                observation = self.tools[name].run(**kwargs)
                print(f"  [Observation] {observation}")
            self.memory.add("step", f"{step}: {observation}")
            done.append(step)

        # 长时记忆沉淀
        self.memory.remember("last_plan", plan)
        print(f"\n执行完成 {len(done)} 步。长时记忆已沉淀：{list(self.memory.long_term)}")
        return self.memory.short_term


def main():
    agent = Agent("对比近两年新能源汽车销量趋势")
    agent.run()
    print("\n要点：")
    print("  1. 工具=行动能力；记忆=经验沉淀；规划=路线图；大脑=每步决策")
    print("  2. 本例大脑是规则模拟；真实场景替换为 LLM 调用（Day02/03 展开）")


if __name__ == "__main__":
    main()