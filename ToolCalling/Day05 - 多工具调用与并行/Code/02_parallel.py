# -*- coding: utf-8 -*-
"""
Day05 - 02 并行工具调用

相互独立的多工具调用用并发执行加快速度（演示用 time.sleep 模拟耗时）。

离线可运行。
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor


def get_weather(city):
    time.sleep(0.5)
    return f"{city} 晴 22°C"


def get_time(city):
    time.sleep(0.5)
    return f"{city} 时间 14:00"


TOOLS = {"get_weather": get_weather, "get_time": get_time}


def run_one(tc):
    name = tc["function"]["name"]
    args = json.loads(tc["function"]["arguments"])
    return tc["id"], TOOLS[name](**args)


def main():
    print(">> 并行调用\n")
    tool_calls = [
        {"id": "c1", "function": {"name": "get_weather", "arguments": json.dumps({"city": "北京"})}},
        {"id": "c2", "function": {"name": "get_time", "arguments": json.dumps({"city": "北京"})}},
    ]

    t0 = time.time()
    # 串行
    t_start = time.time()
    serial = [run_one(tc) for tc in tool_calls]
    serial_t = time.time() - t_start

    # 并行
    t_start = time.time()
    with ThreadPoolExecutor() as pool:
        parallel = list(pool.map(run_one, tool_calls))
    paral_t = time.time() - t_start

    print(f"  串行耗时 ≈ {serial_t:.2f}s ；并行耗时 ≈ {paral_t:.2f}s\n")
    for cid, result in parallel:
        print(f"  ✅ {result}（id={cid}）")
    print("\n  tips: 并行只适用于无依赖的独立调用，结果同样按 id 回填。")


if __name__ == "__main__":
    main()