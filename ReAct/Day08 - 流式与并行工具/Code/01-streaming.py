"""
Day08 练习一：流式输出
=========================
用生成器逐 token 输出, 模拟 SSE 流式。演示:
  - yield 逐字
  - 汇总 full_text
  - Mock 流式后端接口

运行:
  python "Day08 - 流式与并行工具/Code/01-streaming.py"
"""
import time


class MockStreamLLM:
    """一个模拟"流式"的 LLM: stream() 分小片吐文本。"""

    def stream(self, messages, tools=None):
        full_answer = "这是一个通过流式逐字输出的回答。"
        for ch in full_answer:
            time.sleep(0.02)          # 模拟网络节奏
            yield ch


def stream_text(llm, messages, tools=None):
    """统一流式封装: yield 每一片, 同时累积返回全文。"""
    full = ""
    for piece in llm.stream(messages, tools):
        full += piece
        yield piece
    return full


def main() -> None:
    llm = MockStreamLLM()
    messages = [{"role": "user", "content": "输出一段流式文字"}]
    print("流式输出(逐个字符):\n")
    gen = stream_text(llm, messages)
    final_text = ""
    # 手动逐段消费; 为展示"流式"效果, 让生成器把每片拼进来
    g = llm.stream(messages)          # 用最简单的逐片
    for piece in g:
        print(piece, end="", flush=True)
        final_text += piece
    print("\n\n✔ 汇总全文:", repr(final_text))
    print("  (真实场景中可把 yield 交给 HTTP 流/UI 逐字渲染)")


if __name__ == "__main__":
    main()