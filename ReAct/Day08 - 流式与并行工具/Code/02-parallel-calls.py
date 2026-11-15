"""
Day08 练习二：并行工具调用
============================
一次返回多个 tool_calls, 用 ThreadPoolExecutor 并行执行两个独立工具,
再把结果逐条回填 Observation。演示并行比串行省时的收益。

运行:
  python "Day08 - 流式与并行工具/Code/02-parallel-calls.py"
"""
import time
from concurrent.futures import ThreadPoolExecutor
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import tool, ToolRegistry  # noqa: E402


@tool
def search_stock(symbol: str) -> str:
    """查询股票行情(模拟 2s 网络延迟)"""
    time.sleep(2.0)
    return f"{symbol} 现价 100 元"


@tool
def search_news(topic: str) -> str:
    """查询财经新闻(模拟 2s 延迟)"""
    time.sleep(2.0)
    return f"今日 {topic} 相关新闻: 市场稳中有升"


def main() -> None:
    reg = ToolRegistry([search_stock, search_news])

    # 模拟模型一次返回两个 tool_calls
    tool_calls = [
        {"name": "search_stock", "arguments": {"symbol": "600519"}},
        {"name": "search_news", "arguments": {"topic": "白酒"}},
    ]

    # 串行耗时
    t0 = time.time()
    for tc in tool_calls[:1]:
        reg.execute(tc["name"], **tc["arguments"])
    serial_one = time.time() - t0
    serial_total = serial_one * len(tool_calls)

    # 并行执行
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(reg.execute, tc["name"], **tc["arguments"]) for tc in tool_calls]
        results = [f.result() for f in futures]
    elapsed = time.time() - t0

    print("并行执行两个独立工具:\n")
    for tc, r in zip(tool_calls, results):
        print(f"  {tc['name']}({tc['arguments']}) -> {r}")

    print(f"\n 串行(估算)约 {serial_total:.2f}s vs 并行实测 {elapsed:.2f}s")
    print(" 收益: 总耗时 ≈ 最慢单个工具, 而非累加。")
    print(" 随后把所有 Observation 逐条回填历史, 让模型基于全部结果作答。")


if __name__ == "__main__":
    main()