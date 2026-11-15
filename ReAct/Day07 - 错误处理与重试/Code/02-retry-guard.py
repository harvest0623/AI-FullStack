"""
Day07 练习二：重试与上限护栏
==============================
工具连续失败时, 使用"最大工具调用次数"限制, 触发兜底回答,
绝不让 Agent 无限重试/死循环。

运行:
  python "Day07 - 错误处理与重试/Code/02-retry-guard.py"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools import tool, ToolRegistry  # noqa: E402


@tool
def flaky_tool(service: str) -> str:
    """模拟一个总是失败的第三方工具"""
    raise ConnectionError(f"{service} 服务超时")


def build_decider(always_fail):
    def d(messages, tools=None):
        # 即使失败也继续要求重试, 测试护栏
        return {"content": "调用 flaky_tool 再试一次", "tool_calls": []}
    return d


def main() -> None:
    reg = ToolRegistry([flaky_tool])
    max_tool_calls = 3
    calls = 0

    print("护栏演示: max_tool_calls =", max_tool_calls, "\n")
    while calls < 6:                      # 外部更大的上限
        calls += 1
        # 执行工具(假设模型又要调)
        try:
            reg.execute("flaky_tool", service="sign")
            print(f"[{calls}] 成功")
            break
        except Exception as e:
            print(f"[{calls}] flaky_tool 失败: {e}")

        # 关键: 达到工具调用上限就停
        if calls >= max_tool_calls:
            print("\n⚠️ 已达工具调用上限, 停止重试, 触发兜底回答:")
            print("   '抱歉, 服务暂时不可用。请稍后再试。'")
            return

    print("完成")


if __name__ == "__main__":
    main()