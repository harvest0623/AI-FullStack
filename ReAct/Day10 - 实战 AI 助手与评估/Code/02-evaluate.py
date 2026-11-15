"""
Day10 练习二：Agent 评估集
==========================
对一组任务批量跑 Agent, 计算:
  - 正确率:     回答命中期望关键词的比例
  - 平均轮次:   平均消耗的思考-行动步数
  - 失败率:     达到最大轮次 / 抛错的占比
真正认识"Agent 能力 = 一组测试用例的平均表现"。

本脚本复用 01-agent.py 中的 Agent 类与工具, 离线用 MockLLM 跑通。

运行:
  python "Day10 - 实战 AI 助手与评估/Code/02-evaluate.py"
"""
import sys, os, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402
from llm import auto_llm, text, tool_call  # noqa: E402

# 01-agent.py 以数字开头, 不是合法模块名, 用 importlib 从文件加载
_agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "01-agent.py")
_spec = importlib.util.spec_from_file_location("agent_mod", _agent_path)
_agent_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_agent_mod)
Agent = _agent_mod.Agent  # 复用 01-agent.py 里封装的 Agent 类


# ---------- 工具(与 01-agent 一致) ----------
STOCK = {"耳机": "充足", "手表": "充足", "键盘": "缺货"}


@tool
def search_product(kw: str) -> str:
    """按关键词返回商品名称与价格"""
    db = {"耳机": "无线降噪耳机 $199", "手表": "智能手表 $299", "键盘": "机械键盘 $89"}
    return db.get(kw, f"未找到 {kw}")


@tool
def calc_mul(a: float, b: float) -> str:
    """计算 a 乘 b"""
    return f"{a * b}"


@tool
def query_stock(sku: str) -> str:
    """查询商品库存是否充足"""
    return STOCK.get(sku, "未知")


def agent_decider(messages, tools=None):
    """规则版神经元的决策器, 让单测可控、结果稳定。"""
    obs = [m["content"] for m in messages if m.get("role") == "tool"]
    user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")

    # 耳机: 先搜再答
    if "耳机" in user and "库存" in user:
        if not obs:
            return tool_call("search_product", {"kw": "耳机"})
        if len(obs) == 1:
            return tool_call("query_stock", {"sku": "耳机"})
        return text(f"耳机情况: {obs[-1]}。")
    if "耳机" in user and not obs:
        return tool_call("search_product", {"kw": "耳机"})
    if obs and obs[-1].startswith("无线降噪耳机") and "耳机" in user and "库存" not in user:
        return text("推荐: 无线降噪耳机, 价格 $199。")

    # 乘法: 先算再答
    if ("乘" in user or "*" in user) and not obs:
        return tool_call("calc_mul", {"a": 3, "b": 4})
    if ("乘" in user or "*" in user) and obs and (obs[-1] in ("12.0", "12")):
        return text("3*4 = 12。")

    return text("抱歉, 我不太会, 但可以帮你查商品。")


# ---------- 评估集: (输入, 期望回答含有的关键词) ----------
EVAL_SET = [
    {"input": "一副耳机多少钱?",          "expect": ["199", "耳机"]},
    {"input": "请算 3*4 再告诉我",        "expect": ["12"]},
    {"input": "耳机有库存吗?",            "expect": ["充足"]},
    {"input": "推荐一个手表",              "expect": []},        # 守方未实现手表, 期望兜底->答错
    {"input": "今天天气怎么样?",          "expect": ["抱歉", "不太会"]},
]


def run_eval(agent, evals) -> dict:
    records = []
    correct = 0
    for i, item in enumerate(evals, 1):
        r = agent.run(item["input"])
        answer = r["answer"]
        # 有关键词期待: 全部命中且 Agent 未失败才算对
        if item["expect"]:
            ok = r.get("ok", False) and all(exp in answer for exp in item["expect"])
        # 无关键词期待(如"守方"用例): 只要给出非空回答即通过
        else:
            ok = r.get("ok", False) and bool(answer)
        correct += 1 if ok else 0
        records.append({
            "input": item["input"], "expect": item["expect"], "answer": answer,
            "ok": ok, "steps": r["stats"]["steps"], "tool_calls": r["stats"]["tool_calls"],
        })
        print(f"[{i}] {'✓' if ok else '✗'} 输入: {item['input']}")
        print(f"      期望命中: {item['expect']}")
        print(f"      答案: {answer}")
        print(f"      轮次/工具调用: {r['stats']['steps']}/{r['stats']['tool_calls']}\n")

    n = len(evals)
    avg_steps = sum(x["steps"] for x in records) / n
    failed = sum(1 for x in records if not x["ok"])
    return {
        "total": n,
        "correct": correct,
        "accuracy": correct / n,
        "avg_steps": round(avg_steps, 2),
        "failed": failed,
        "fail_rate": failed / n,
        "records": records,
    }


def main() -> None:
    reg = ToolRegistry([search_product, calc_mul, query_stock])
    llm = auto_llm(mock_decider=agent_decider)
    agent = Agent(reg, llm, system="你是电商助手, 用工具回答; 给出简洁自然语言。", max_steps=6)

    report = run_eval(agent, EVAL_SET)
    print("========== 评估报告 ==========")
    print(f"总任务数: {report['total']}")
    print(f"正确数  : {report['correct']}  正确率: {report['accuracy']:.0%}")
    print(f"平均轮次: {report['avg_steps']}")
    print(f"失败数  : {report['failed']}  失败率: {report['fail_rate']:.0%}")


if __name__ == "__main__":
    main()