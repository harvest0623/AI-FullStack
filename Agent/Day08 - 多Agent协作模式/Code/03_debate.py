"""
03_debate.py
Debate 辩论模式：正方/反方多轮交锋，裁判收敛结论。
演示轮次控制与边际收益（第 3 轮后论点趋同）。

运行：python 03_debate.py
"""


class Debater:
    def __init__(self, role: str, position: str):
        self.role = role
        self.position = position        # 立场：pro / con

    def argue(self, topic: str, history: list[str]) -> str:
        """基于历史论点产出新论（规则模拟）。"""
        n = len(history) // 2           # 已进行的轮次
        if self.position == "pro":
            args = ["数据驱动：历史环比 +48%，增长趋势明确",
                    "补充：主力品类扩张，结构性利好",
                    "让步修正：外部因素有风险，但核心逻辑仍成立"]
        else:
            args = ["风险视角：上期基数低，环比高估了增长",
                    "补充：行业整体上行，未必跑赢大盘",
                    "让步修正：趋势存在，但幅度应打折"]
        return args[min(n, len(args) - 1)]


class Judge:
    def converge(self, topic: str, history: list[str]) -> str:
        pros = sum(1 for h in history if "增长" in h or "利好" in h)
        cons = sum(1 for h in history if "风险" in h or "高估" in h)
        # 双方第三轮出现"让步修正" -> 论点趋同
        concessions = sum(1 for h in history if "让步修正" in h)
        if concessions >= 2:
            return ("[收敛] 双方已相互让步：增长趋势存在，但幅度需打折评估。"
                    "结论：谨慎乐观，预计环比 +30%~40%。")
        return f"[继续] 正方 {pros} 论点 vs 反方 {cons} 论点，分歧仍明显。"


def main():
    print("=" * 62)
    print("Debate 辩论模式：观点对抗 -> 收敛")
    print("=" * 62)

    topic = "本月增长是否可持续"
    pro, con = Debater("正方", "pro"), Debater("反方", "con")
    judge = Judge()
    history = []

    for round_no in range(1, 4):
        print(f"\n----- 第 {round_no} 轮 -----")
        a = pro.argue(topic, history)
        history.append(a)
        print(f"  正方: {a}")
        b = con.argue(topic, history)
        history.append(b)
        print(f"  反方: {b}")

        verdict = judge.converge(topic, history)
        print(f"  裁判: {verdict}")
        if verdict.startswith("[收敛]"):
            print("\n（第 %d 轮即收敛：继续辩论边际收益趋零）" % round_no)
            break

    print("\n要点：")
    print("  1. 对抗产出制衡：单模型易有的偏向被正反互搏抵消")
    print("  2. 轮次上限 2-3 轮：本例第 3 轮双方已让步，继续辩是浪费 token")
    print("  3. 裁判只看论点质量与趋同信号，不站队")
    print("  4. 适合质量敏感的判断类任务；不适合执行类任务（执行用 Supervisor/Pipeline）")


if __name__ == "__main__":
    main()