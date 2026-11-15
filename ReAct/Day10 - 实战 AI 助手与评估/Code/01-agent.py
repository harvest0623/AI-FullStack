"""
Day10 练习一：封装一个完整 Agent
==================================
把"多工具 ReAct 循环"封装进 Agent 类:
  - 注册表 + LLM + system + 护栏
  - run() 返回 (answer, trace, stats)
  - 内置日志与成本(估算)统计
本脚本用 MockLLM 离线运行; 有 OPENAI_API_KEY 时自动切真实模型。

运行:
  python "Day10 - 实战 AI 助手与评估/Code/01-agent.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402
from llm import auto_llm, text, tool_call  # noqa: E402


# ---------- 一组工具 ----------
@tool
def search_product(kw: str) -> str:
    """按关键词返回商品名称与价格"""
    db = {"耳机": "无线降噪耳机 $199", "手表": "智能手表 $299"}
    return db.get(kw, f"未找到 {kw}")


@tool
def query_stock(sku: str) -> str:
    """查询库存是否充足"""
    return "充足" if len(sku) else "缺货"


@tool
def calc_mul(a: float, b: float) -> str:
    """计算 a 乘 b"""
    return f"{a * b}"


class Agent:
    def __init__(self, reg: ToolRegistry, llm, system: str = "", max_steps: int = 6):
        self.reg = reg
        self.llm = llm
        self.system = system
        self.max_steps = max_steps

    def run(self, user_text):
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": user_text})

        trace, tool_calls_done = [], 0
        for step in range(self.max_steps):
            resp = self.llm.chat(messages, tools=self.reg.openai_tools())
            messages.append({"role": "assistant", "content": resp.get("content") or "", "tool_calls": resp["tool_calls"]})
            trace.append(resp.get("content") or "(call tools)")

            if not resp["tool_calls"]:
                result = {
                    "answer": resp.get("content", ""),
                    "trace": trace,
                    "stats": {"steps": step + 1, "tool_calls": tool_calls_done,
                              "tokens": sum(len(m.get("content", "")) for m in messages) // 3},
                    "ok": True,
                }
                return result

            for tc in resp["tool_calls"]:
                tool_calls_done += 1
                try:
                    out = self.reg.execute(tc["name"], **tc["arguments"])
                except Exception as e:
                    out = f"工具错误: {e}"
                messages.append({"role": "tool", "content": str(out)})

        return {"answer": "(未完成: 达到最大轮次)", "trace": trace,
                "stats": {"steps": self.max_steps, "tool_calls": tool_calls_done,
                          "tokens": 0}, "ok": False}


def agent_decider(messages, tools=None):
    obs = [m["content"] for m in messages if m.get("role") == "tool"]
    user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    if "耳机" in user and not obs:
        return tool_call("search_product", {"kw": "耳机"})
    if obs and obs[-1].startswith("无线降噪耳机"):
        return text("推荐: 无线降噪耳机, 价格 $199。")
    if "乘法" in user or "*" in user or "乘" in user:
        if not obs:
            return tool_call("calc_mul", {"a": 3, "b": 4})
        if obs[-1] == "12.0" or obs[-1] == "12":
            return text("3*4 = 12。")
    return text("抱歉, 我不太会, 但可以帮你查商品。")


def main() -> None:
    reg = ToolRegistry([search_product, query_stock, calc_mul])
    llm = auto_llm(mock_decider=agent_decider)
    agent = Agent(reg, llm, system="你是电商助手, 用工具回答; 给出简洁自然语言。", max_steps=6)

    for q in ["一副耳机多少钱?", "3*4 等于几?"]:
        r = agent.run(q)
        print("问:", q)
        print("答:", r["answer"])
        print("统计:", r["stats"], "\n")


if __name__ == "__main__":
    main()