"""
03_autonomy_levels.py
Agent 自主性等级（L0-L4）：用同一个工单处理任务，观察五个等级的行为差异。

运行：python 03_autonomy_levels.py
"""

import time


def mock_actions():
    """五个等级在处理『退款工单』时各自的行为。"""
    cases = [
        {
            "level": "L0 反射式",
            "behavior": "关键词命中『退款』-> 自动回复固定话术",
            "human": "无",
            "risk": "极低（但答非所问常见）",
            "code": lambda: "已回复：您好，退款将在 3 个工作日内原路退回。",
        },
        {
            "level": "L1 辅助式",
            "behavior": "Agent 分析工单、起草回复 -> 人确认后发送",
            "human": "每单必审",
            "risk": "低",
            "code": lambda: "草稿已生成，等待人工确认发送。",
        },
        {
            "level": "L2 半自治",
            "behavior": "金额 < 100 元自动处理；超过则升级人工审批",
            "human": "高风险时介入",
            "risk": "可控",
            "code": lambda: "金额 45 元 < 100 元阈值 -> 自动执行退款并通知用户。",
        },
        {
            "level": "L3 受限自治",
            "behavior": "在退款政策与工具白名单内全自主：查订单->判断->执行->回复",
            "human": "仅异常上报",
            "risk": "中（依赖护栏强度）",
            "code": lambda: "自主完成：查订单->核对政策->执行退款->回复用户->记录日志。",
        },
        {
            "level": "L4 全自治",
            "behavior": "长期值守：主动发现批量异常工单，归纳根因，提交改进方案",
            "human": "周期性复盘",
            "risk": "高（需观测+回滚）",
            "code": lambda: "巡检发现 37 单同类异常 -> 归纳根因 -> 已提交改进建议工单。",
        },
    ]
    return cases


def main():
    print("=" * 66)
    print("同一任务（处理退款工单），五个自主性等级的行为")
    print("=" * 66)

    for c in mock_actions():
        print(f"\n【{c['level']}】")
        print(f"  行为：{c['behavior']}")
        print(f"  人工：{c['human']}   风险：{c['risk']}")
        print(f"  执行：{c['code']()}")

    print("\n" + "=" * 66)
    print("结论：自主性越高，效率越高，但风险与工程要求也越高。")
    print("  - L0-L1：几乎无风险，今天就能上线")
    print("  - L2：需要审批门（Day09）与权限矩阵")
    print("  - L3：需要护栏 + 评估 + 完整轨迹（Day07/09）")
    print("  - L4：需要可观测性 + 回滚能力 + 长期记忆（Day04/10）")
    print("工程建议：从 L1/L2 起步，靠评估数据逐步放权。")


if __name__ == "__main__":
    main()