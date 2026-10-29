"""
01_memory_layers.py
记忆三层结构：工作记忆 / 短时记忆 / 长时记忆 的协作骨架。
演示一个跨任务的 Agent 如何借助三层记忆保持连贯。

运行：python 01_memory_layers.py
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 三层记忆实现
# ---------------------------------------------------------------------------
@dataclass
class WorkingMemory:
    """工作记忆：当前步的草稿纸，用完即弃。"""
    current_thought: str = ""
    scratch: dict = field(default_factory=dict)

    def note(self, k, v):
        self.scratch[k] = v          # 例如暂存中间计算值


class ShortTermMemory:
    """短时记忆：本任务内的消息历史（模拟窗口受限）。"""

    def __init__(self, window: int = 5):
        self.window = window
        self.messages: list[dict] = []

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        # 简单截断（Day02 02_history_mgmt 会展开高级策略）
        if len(self.messages) > self.window:
            self.messages = self.messages[-self.window:]

    def context(self) -> list[dict]:
        return self.messages


class LongTermMemory:
    """长时记忆：跨会话的键值存储 + 关键词检索。"""

    def __init__(self):
        self.store: dict[str, str] = {}

    def write(self, key: str, value: str):
        self.store[key] = value

    def search(self, keyword: str) -> list[str]:
        return [f"{k}: {v}" for k, v in self.store.items() if keyword in v or keyword in k]


# ---------------------------------------------------------------------------
# 组装：带记忆的 Agent 执行两个"会话"
# ---------------------------------------------------------------------------
class RememberingAgent:
    def __init__(self):
        self.working = WorkingMemory()
        self.short = ShortTermMemory(window=3)
        self.long = LongTermMemory()

    def run_session(self, session_name: str, task: str):
        print(f"\n【会话 {session_name}】任务：{task}")

        # 1) 长时记忆检索 -> 注入上下文（工作记忆）
        hits = self.long.search(task.split()[0]) if task else []
        if hits:
            print(f"  [长时检索] 召回 {len(hits)} 条：{hits}")
            self.working.note("recalled", hits)

        # 2) 短时记忆参与（本会话历史）
        self.short.add("user", task)
        print(f"  [短时历史] 当前 {len(self.short.context())} 条（窗口 3）")

        # 3) 工作记忆做点事
        self.working.current_thought = f"处理：{task}"
        print(f"  [工作记忆] thought='{self.working.current_thought}'")

        # 4) 模拟任务产出，沉淀长时记忆
        fact = f"{session_name} 的经验：{task} 已完成，结论是 OK"
        self.long.write(f"exp_{session_name}", fact)
        print(f"  [长时写入] {fact}")

        # 5) 工作记忆用完即弃
        self.working = WorkingMemory()


def main():
    print("=" * 62)
    print("记忆三层结构演示")
    print("=" * 62)

    agent = RememberingAgent()
    agent.run_session("S1", "查询 华东 区域上月销量")
    agent.run_session("S2", "查询 华南 区域上月销量")
    agent.run_session("S3", "查询 华东 区域本月销量")   # 会命中 S1 的长时记忆

    print("\n" + "=" * 62)
    print("最终长时记忆库：")
    for k, v in agent.long.store.items():
        print(f"  {k}: {v}")

    print("\n要点：")
    print("  1. 工作记忆=单步草稿；短时=任务内上下文(窗口受限)；长时=跨会话存储")
    print("  2. 长时记忆『按需检索』注入，而不是全量塞进上下文——这是扩容关键")
    print("  3. S3 召回了 S1 的经验：这就是跨会话记忆在起作用")


if __name__ == "__main__":
    main()