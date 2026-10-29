"""
02_parallel_tools.py
并行工具调用：一次决策产生多个 tool_calls，并发执行，
用 tool_call_id 关联回填，并演示部分失败的处理。

运行：python 02_parallel_tools.py
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor


# ---------------------------------------------------------------------------
# 工具（模拟不同耗时与一个会失败的）
# ---------------------------------------------------------------------------
def query_sales(region: str) -> dict:
    time.sleep(0.2)
    return {"region": region, "sales": {"north": 1450, "south": 980, "east": 1750}[region]}


def query_competitor(region: str) -> dict:
    time.sleep(0.3)
    return {"region": region, "competitor_avg": 1100}


def query_inventory(region: str) -> dict:
    time.sleep(0.2)
    if region == "east":
        return {"error": "inventory service unavailable", "region": region}
    return {"region": region, "stock": 5600}


TOOLS = {"query_sales": query_sales,
         "query_competitor": query_competitor,
         "query_inventory": query_inventory}


# ---------------------------------------------------------------------------
# 模型的一次并行决策（模拟：3 个 tool_calls 一次给出）
# ---------------------------------------------------------------------------
def model_decide_parallel():
    return {"role": "assistant", "content": None,
            "tool_calls": [
                {"id": "call_a", "name": "query_sales", "arguments": {"region": "north"}},
                {"id": "call_b", "name": "query_sales", "arguments": {"region": "south"}},
                {"id": "call_c", "name": "query_sales", "arguments": {"region": "east"}},
            ]}


def execute_parallel(calls: list[dict], workers: int = 4):
    """并发执行所有调用，返回按 id 索引的结果。"""
    def run_one(c):
        try:
            return c["id"], TOOLS[c["name"]](**c["arguments"])
        except Exception as e:
            return c["id"], {"error": str(e)}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(run_one, calls))
    return dict(results)


def aggregate(results: dict) -> str:
    """把多个结果聚合成一条观察（喂回模型的结构化文本）。"""
    rows = []
    for rid, r in results.items():
        if "error" in r:
            rows.append(f"[{rid}] ❌ {r['error']}")
        else:
            rows.append(f"[{rid}] {r['region']} 销量 {r['sales']}")
    return "\n".join(rows)


def main():
    print("=" * 62)
    print("并行工具调用：一次决策，多路执行，ID 关联回填")
    print("=" * 62)

    decision = model_decide_parallel()
    calls = decision["tool_calls"]
    print("模型一次输出 3 个 tool_calls：")
    for c in calls:
        print(f"  {c['id']}  {c['name']}({json.dumps(c['arguments'], ensure_ascii=False)})")

    t0 = time.perf_counter()
    results = execute_parallel(calls)
    dur = time.perf_counter() - t0
    print(f"\n并发执行完成：{dur:.2f}s（串行需 ~0.6s+）")

    print("\n按 tool_call_id 回填消息：")
    for rid, r in results.items():
        print(f"  [{rid}] {json.dumps(r, ensure_ascii=False)}")

    print("\n聚合后的观察（喂回模型）：")
    print(aggregate(results))

    # ---- 部分失败演示 ----
    print("\n" + "=" * 62)
    print("部分失败：库存查询（east 会失败）")
    print("=" * 62)
    mixed_calls = [
        {"id": "call_x", "name": "query_inventory", "arguments": {"region": "north"}},
        {"id": "call_y", "name": "query_inventory", "arguments": {"region": "east"}},
    ]
    mixed_results = execute_parallel(mixed_calls)
    print(aggregate(mixed_results))
    print("\n模型看到 [call_y] 失败后可以：重试一次 / 跳过 east 并说明 / 换数据源——")
    print("关键是失败被显式回填，而不是让整个调用挂掉。")

    print("\n要点：")
    print("  1. 并行 = 一次决策多个 tool_calls，并发执行后按 ID 回填（顺序无关）")
    print("  2. 聚合：多结果合并成结构化观察，减少消息往返")
    print("  3. 部分失败不致命：错误显式回填，交给模型决定重试/跳过/换源")
    print("  4. 并行要配整体超时：慢工具不能拖死整批（本例未演示，生产必备）")


if __name__ == "__main__":
    main()