#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: RetryPolicy 重试演示 —— 节点自动重试,指数退避 + 抖动
# 说明: 用可抛异常的模拟节点,展示 max_attempts / initial_interval / backoff_factor / jitter。
# 运行: python 01_retry_policy.py
# 依赖: pip install langgraph langchain python-dotenv pydantic（不调用真实 LLM）

import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.pregel.retry import RetryPolicy


class State(TypedDict):
    input_text: str
    result: str


class RetryDemo:
    """演示节点级 RetryPolicy:前几次失败自动重试,最终成功。"""

    def __init__(self):
        self.counter = {"attempts": 0}
        self.graph = self._build_graph()

    def _build_graph(self):
        def flaky_node(state: State) -> dict:
            self.counter["attempts"] += 1
            n = self.counter["attempts"]
            if n <= 2:
                # 模拟前两次 LLM 随机网络失败,触发重试
                raise ConnectionError(f"模拟网络抖动,第 {n} 次调用失败")
            return {"result": f"第 {n} 次尝试成功,审核结论:内容基本合规"}

        builder = StateGraph(State)
        builder.add_node(
            "flaky",
            flaky_node,
            retry=RetryPolicy(
                max_attempts=3,        # 含首次:共 3 次机会
                initial_interval=0.5,  # 首次重试前等 0.5s
                backoff_factor=2.0,    # 指数退避
                jitter=True,           # 加抖动
            ),
        )
        builder.add_edge(START, "flaky")
        builder.add_edge("flaky", END)
        return builder.compile()

    def run(self, text: str):
        start = time.time()
        result = self.graph.invoke({"input_text": text})
        elapsed = time.time() - start
        return result, elapsed, self.counter["attempts"]


def main():
    print("=" * 60)
    print("GraphFlow - RetryPolicy 自动重试")
    print("=" * 60)
    demo = RetryDemo()
    result, elapsed, attempts = demo.run("稳赚不赔的理财广告")
    print(f"最终结果   : {result['result']}")
    print(f"尝试次数   : {attempts} (前2次失败,第3次成功 => 验证了 max_attempts=3)")
    print(f"总耗时     : {elapsed:.2f}s (含退避等待)")


if __name__ == "__main__":
    main()