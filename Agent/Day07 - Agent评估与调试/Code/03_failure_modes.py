"""
03_failure_modes.py
五大典型失败模式的复现与诊断：每种模式给出症状、复现、对策。
相当于 Agent 的『故障手册』。

运行：python 03_failure_modes.py
"""

# 每个模式：名称 / 症状 / 复现轨迹片段 / 根因 / 对策
MODES = [
    {
        "name": "死循环",
        "symptom": "反复执行相同的 Action，步数耗尽",
        "trace": [
            ("查W02销量", "query_sales(W02)", "...980"),
            ("再查一次", "query_sales(W02)", "...980"),
            ("再查一次", "query_sales(W02)", "...980"),
        ],
        "cause": "模型短视：观察没变，思路没变；或工具返回让模型误解",
        "fix": "重复检测(工具+参数) + max_steps 兜底 + 错误观察显式化",
    },
    {
        "name": "幻觉工具",
        "symptom": "调用了注册表中不存在的工具",
        "trace": [
            ("查天气影响", "query_weather(city='北京')", "❌ not_found_tool"),
            ("换个参数试试", "query_weather(city='Beijing')", "❌ not_found_tool"),
        ],
        "cause": "模型把『常识能力』当成『已有工具』",
        "fix": "执行前白名单校验；错误回填可用工具清单",
    },
    {
        "name": "参数幻觉",
        "symptom": "工具存在但参数是编造的",
        "trace": [
            ("查上上周", "query_sales(week='前两周')", "❌ invalid format"),
        ],
        "cause": "Schema 描述含糊，没有 pattern/enum 约束",
        "fix": "JSON Schema 强校验 + 可指导错误信息（给示例）",
    },
    {
        "name": "过早放弃",
        "symptom": "浅尝辄止就直答，缺关键数据",
        "trace": [
            ("查一下销量", "query_sales(W03)", "...1450"),
            ("差不多了", "FINAL", "本月销量 1450（未做对比即下结论）"),
        ],
        "cause": "任务判据模糊；Prompt 没有要求完备性",
        "fix": "任务完成判据（如必须含对比）；Prompt 引导『检查是否满足全部要求』",
    },
    {
        "name": "观察误读",
        "symptom": "工具明确报错，下一步却当成功继续",
        "trace": [
            ("查W02", "query_sales(W02)", "{'error': 'timeout'}"),
            ("W02是1200", "calc((1450-1200)/1200)", "...20.8"),
        ],
        "cause": "长上下文淹没错误；模型选择性理解",
        "fix": "错误结果加显式标记（[ERROR]前缀）；缩短上下文；错误后强制重试分支",
    },
]


def main():
    print("=" * 64)
    print("Agent 故障手册：五大失败模式")
    print("=" * 64)

    for m in MODES:
        print(f"\n【{m['name']}】 {m['symptom']}")
        print("  复现轨迹：")
        for th, act, obs in m["trace"]:
            print(f"    Thought: {th:<14} Action: {act:<32} -> {obs}")
        print(f"  根因: {m['cause']}")
        print(f"  对策: {m['fix']}")

    print("\n" + "=" * 64)
    print("使用方法：线上失败案例 -> 对照手册分类 -> 直接套对策")
    print("然后：加入评估集作为回归用例（失败案例是最宝贵的评估数据）")

    print("\n要点：")
    print("  1. 五大模式覆盖绝大多数 Agent 线上故障")
    print("  2. 死循环/幻觉工具/参数幻觉是『执行层』问题，可工程硬防")
    print("  3. 过早放弃/观察误读是『认知层』问题，靠 Prompt + 判据 + 上下文管理")


if __name__ == "__main__":
    main()