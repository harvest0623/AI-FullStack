"""
Day02 练习二：用封装好的 LLM 做简单对话
=========================================
演示:
  1. 引入 Day02 的 llm.py(OpenAILLM / MockLLM)
  2. 无 KEY 时用 MockLLM + 自定义 decider 模拟"思考+问答"
  3. 有 KEY 时自动走真实模型

运行:
  python "Day02 - 环境与 LLM 调用封装/Code/02-chat-demo.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import MockLLM, OpenAILLM, auto_llm, text  # noqa: E402


def polite_decider(messages, tools=None):
    """模拟一个极简 LLM: 根据最后一条消息回一句固定话, 演示接口。"""
    last = messages[-1]["content"]
    if "天气" in last:
        return text("(Mock) 我可以查天气, 但还没接工具。我需要一个 weather 工具。")
    if "你好" in last or "hi" in last:
        return text("(Mock) 你好! 我是离线演示模型。")
    return text(f"(Mock) 收到: {last}")


def main() -> None:
    llm = auto_llm(mock_decider=polite_decider)

    if isinstance(llm, OpenAILLM):
        print("★ 检测到 OPENAI_API_KEY, 使用真实模型调用。\n")
    else:
        print("★ 未检测到 KEY, 使用离线 MockLLM 演示(不消耗 API)。\n")

    history = [{"role": "system", "content": "你是一个乐于助人的助手。"}]

    for question in ["你好", "今天天气怎么样?"]:
        history.append({"role": "user", "content": question})
        reply = llm.text(history)
        print(f"问: {question}")
        print(f"答: {reply}\n")
        history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()