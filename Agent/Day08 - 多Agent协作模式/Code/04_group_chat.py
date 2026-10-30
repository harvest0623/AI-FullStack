"""
04_group_chat.py
GroupChat 群聊模式：多角色 + 主持人调度 + 共享黑板。
调度者根据任务状态决定下一个发言者，黑板沉淀全局信息。

运行：python 04_group_chat.py
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 共享黑板：所有角色读写同一状态
# ---------------------------------------------------------------------------
@dataclass
class Blackboard:
    goal: str
    findings: list = field(default_factory=list)
    todo: list = field(default_factory=list)
    done: list = field(default_factory=list)

    def write_finding(self, who: str, text: str):
        self.findings.append(f"[{who}] {text}")

    def pop_todo(self):
        return self.todo.pop(0) if self.todo else None


# ---------------------------------------------------------------------------
# 角色与主持人
# ---------------------------------------------------------------------------
class Member:
    def __init__(self, name: str, duty: str):
        self.name, self.duty = name, duty

    def speak(self, bb: Blackboard) -> str:
        # 各角色按职责对黑板做贡献（规则模拟）
        if self.name == "数据专员":
            bb.write_finding(self.name, "本月销量 1450，环比 +48%")
            return "已查询并写入核心数据。"
        if self.name == "市场专员":
            bb.write_finding(self.name, "行业均值 +20%，我们跑赢大盘")
            return "已补充行业对标。"
        if self.name == "文案":
            if bb.findings:
                bb.write_finding(self.name, "草稿：本月 1450 环比 +48%，跑赢行业")
                return "基于黑板数据完成草稿。"
            return "等待数据专员先发言。"
        if self.name == "审核":
            bb.write_finding(self.name, "数据一致性 OK，可交付")
            return "审查通过。"
        return "..."


class Moderator:
    """主持人（调度者）：多 Agent 系统的灵魂。"""

    def __init__(self, members: list[Member]):
        self.members = members

    def next_speaker(self, bb: Blackboard, round_no: int) -> Member | None:
        """调度策略：按任务状态选择发言者。"""
        has_data = any("数据专员" in f for f in bb.findings)
        has_market = any("市场专员" in f for f in bb.findings)
        has_draft = any("文案" in f for f in bb.findings)
        reviewed = any("审核" in f for f in bb.findings)

        by_name = {m.name: m for m in self.members}
        if not has_data:
            return by_name.get("数据专员")
        if not has_market:
            return by_name.get("市场专员")
        if not has_draft:
            return by_name.get("文案")
        if not reviewed:
            return by_name.get("审核")
        return None          # 全部完成

    def is_done(self, bb: Blackboard) -> bool:
        return any("可交付" in f for f in bb.findings)


def main():
    print("=" * 62)
    print("GroupChat：调度者 + 共享黑板")
    print("=" * 62)

    members = [Member("数据专员", "查询数据"),
               Member("市场专员", "行业对标"),
               Member("文案", "撰写结论"),
               Member("审核", "质量把关")]
    mod = Moderator(members)
    bb = Blackboard(goal="产出本月销售简报",
                    todo=["查数据", "行业对标", "写草稿", "审核"])

    print(f"目标：{bb.goal}\n")
    for round_no in range(1, 7):
        speaker = mod.next_speaker(bb, round_no)
        if speaker is None or mod.is_done(bb):
            print(f"[Round {round_no}] 调度者：任务完成，散会。")
            break
        print(f"[Round {round_no}] 调度者请 {speaker.name}（{speaker.duty}）发言")
        msg = speaker.speak(bb)
        print(f"  {speaker.name}: {msg}")

    print("\n黑板最终状态：")
    print(f"  目标   : {bb.goal}")
    for f in bb.findings:
        print(f"  沉淀   : {f}")

    print("\n要点：")
    print("  1. 调度者是多 Agent 的灵魂：没有调度，群聊=抢话+跑题+不收敛")
    print("  2. 黑板模式：信息写一次全员可见，避免上下文重复传递")
    print("  3. 调度策略编码了『谁先谁后』的依赖：数据->对标->草稿->审核")
    print("  4. 轮次上限必备：本例 6 轮封顶，防讨论失控")


if __name__ == "__main__":
    main()