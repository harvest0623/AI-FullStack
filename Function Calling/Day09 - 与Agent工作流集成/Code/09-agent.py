"""
Day09 与 Agent/工作流集成
========================
把 Function Calling 封装成一个迷你 ReAct Agent:
  一个 ToolAgent 类, 持有 registry, 对外暴露 run(question) 统一接口。
复用框架的 chat_with_tools 实现"思考->工具->再思考", 但把决策器做成
"当前若无结果就调用工具、有结果就总结"的通用规则, 并支持工具链步骤推动。

演示:
  - 注册 多个工具(算数/天气/搜书)
  - 一个 Agent 类编排: 收集中间结果, 逐步推进, 最终返回结论
  - 对外给一句话, 内部自动完成多步

运行:
  python "Day09 - 与Agent工作流集成/Code/09-agent.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework_function_calling import (
    FunctionCallingLLM, FunctionRegistry, FunctionSpec, tool_get_weather,
)


class ToolAgent:
    """迷你 ReAct Agent: 持有工具注册表与一个通用的多步决策器。"""

    def __init__(self, registry: FunctionRegistry):
        self.reg = registry
        self.llm = FunctionCallingLLM(plan=self._decide)

    def _decide(self, messages, tools):
        """通用规则: 尚未拿到结果 -> 根据问题选工具调用; 有结果 -> 总结/下一步。"""
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        question = next((m["content"] for m in messages if m["role"] == "user"), "")

        # 雇佣多步工作流: 每步按工具历史推进
        done = [m["name"] for m in tool_msgs]
        if "get_weather" not in done and "天气" in question:
            city = next((c for c in ("上海", "北京", "广州", "深圳") if c in question), None)
            if city:
                return ("call", [{"name": "get_weather", "args": {"city": city}}])
        if "add" not in done and ("加" in question or "+" in question):
            nums = [int(x) for x in question.replace("加", " ").replace("+", " ").split() if x.isdigit()]
            if len(nums) >= 2:
                return ("call", [{"name": "add", "args": {"a": nums[0], "b": nums[1]}}])

        # 已有结果: 汇总
        if tool_msgs:
            content = tool_msgs[-1]["content"]
            return ("text", f"(Agent) 结果: {content}")
        return ("text", "抱歉, 我可能需要更多信息。")

    def run(self, question: str) -> str:
        return self.llm.chat_with_tools(question, self.reg)


def tool_add(a: float, b: float) -> float:
    return a + b


def main() -> None:
    reg = FunctionRegistry()
    reg.add(FunctionSpec("get_weather", "查天气",
                         {"properties": {"city": {"type": "string"}},
                          "required": ["city"]}, tool_get_weather))
    reg.add(FunctionSpec("add", "两个数相加",
                         {"properties": {"a": {"type": "number"},
                                         "b": {"type": "number"}},
                          "required": ["a", "b"]}, tool_add))

    agent = ToolAgent(reg)
    print("Agent 可用工具:", reg.names())

    print("\n" + "=" * 60)
    q1 = "9 加 15 是多少"
    print("问:", q1)
    print("答:", agent.run(q1))
    assert "24" in agent.run(q1)

    print("\n" + "=" * 60)
    q2 = "北京天气怎么样"
    print("问:", q2)
    print("答:", agent.run(q2))
    assert "北京" in agent.run(q2)

    print("\nAgent 集成断言通过 ✓")


if __name__ == "__main__":
    main()