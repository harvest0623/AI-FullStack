#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件用途: 超时与容错综合演示 —— 重试 → 降级 → 兜底 的健壮生产化节点
# 说明: async 节点 + asyncio.wait_for 超时控制;超时触发降级;Callback 记录错误;异常兜底返回。
# 运行: python 03_timeout_degrade.py
# 依赖: pip install langgraph langchain python-dotenv pydantic（不调用真实 LLM）

import asyncio
import time
from typing import Annotated, TypedDict

from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import END, START, StateGraph

# 控制模拟用时:设为 3 秒可触发下面的 0.5s 超时(演示超时降级)
SIMULATED_LATENCY = 3.0
TIMEOUT = 0.5


class State(TypedDict):
    input_text: str
    status: str       # ok / degraded / error
    message: str


# ---------------- 错误记录 Callback ----------------
class ErrorLogger(BaseCallbackHandler):
    """把节点错误与运行信息记录下来(生产可写日志/推送告警)。"""

    def on_chain_error(self, error, *, run_id=None, parent_run_id=None, **kwargs):
        print(f"  [Callback 上报] 节点 run={run_id} 发生错误: {type(error).__name__}: {error}")


logger = ErrorLogger()


# ---------------- 节点调用(模拟慢速 LLM) ----------------
async def slow_llm_call(state: State) -> str:
    """模拟耗时过长的 LLM 调用。"""
    await asyncio.sleep(SIMULATED_LATENCY)
    return "正常情况下本不该走到这里的完整分析结论"


async def resilient_analyze(state: State) -> dict:
    """核心节点:对慢调用加超时,超时则降级;再失败则由重试+兜底补上。"""
    try:
        # 超时控制:超过 TIMEOUT 秒视为失败
        result = await asyncio.wait_for(slow_llm_call(state), timeout=TIMEOUT)
        return {"status": "ok", "message": result}
    except asyncio.TimeoutError:
        # 超时 -> 降级:用关键词规则给出兜底结论
        print(f"  [超时] 调用超过 {TIMEOUT}s,触发降级")
        hits = [w for w in ["稳赚", "诱导", "链接"] if w in state["input_text"]]
        return {"status": "degraded", "message": f"[超时降级] 命中关键词 {hits} => 判为高风险"}
    except Exception as e:
        # 其它异常 -> 兜底
        logger.on_chain_error(e)
        return {"status": "error", "message": "[兜底] 分析失败,请稍后重试"}


class ResilientGraph:
    """完整的 重试→降级→兜底 容错示例。"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(State)
        builder.add_node("resilient", resilient_analyze)
        builder.add_edge(START, "resilient")
        builder.add_edge("resilient", END)
        return builder.compile()

    async def run(self, text: str) -> dict:
        return await self.graph.ainvoke({"input_text": text})


def main():
    print("=" * 60)
    print("GraphFlow - 超时与完整容错(重试/降级/兜底)")
    print("=" * 60)
    print(f"(模拟 LLM 时延 {SIMULATED_LATENCY}s > 超时阈值 {TIMEOUT}s => 将触发超时降级)")

    start = time.time()
    res = asyncio.run(ResilientGraph().run("稳赚不赔,点击链接领取收益"))
    elapsed = time.time() - start
    print(f"状态     : {res['status']}")
    print(f"消息     : {res['message']}")
    print(f"实际耗时 : {elapsed:.2f}s (被超时打断,未等待模拟的 {SIMULATED_LATENCY}s)")


if __name__ == "__main__":
    main()