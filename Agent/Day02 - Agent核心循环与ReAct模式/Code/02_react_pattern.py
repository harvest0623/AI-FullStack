"""
02_react_pattern.py
完整 ReAct 模式：Thought / Action / Observation 三元组的显式实现。
展示"先写推理再行动"如何让每一步都可解释、可调试。

运行：python 02_react_pattern.py
"""

import json


# ---------------- 工具 ----------------
MOVIES = {
    "m1": {"title": "流浪地球2", "year": 2023, "rating": 8.3},
    "m2": {"title": "奥本海默", "year": 2023, "rating": 8.9},
    "m3": {"title": "沙丘2", "year": 2024, "rating": 8.2},
}
API_CALLS = []


def search_movies(keyword: str) -> str:
    hits = [m for m in MOVIES.values() if keyword in m["title"]]
    return json.dumps({"count": len(hits), "movies": hits}, ensure_ascii=False)


def get_rating(title: str) -> str:
    API_CALLS.append(("get_rating", title))
    for m in MOVIES.values():
        if m["title"] == title:
            return json.dumps({"title": title, "rating": m["rating"]}, ensure_ascii=False)
    return json.dumps({"error": "not found"}, ensure_ascii=False)


TOOLS = {"search_movies": search_movies, "get_rating": get_rating}


# ---------------- ReAct 引擎 ----------------
class ReActAgent:
    def __init__(self, goal: str, max_steps: int = 6):
        self.goal = goal
        self.max_steps = max_steps
        self.trajectory = []          # [(thought, action, observation), ...]

    def _reason(self, history) -> dict:
        """模拟 LLM 产生 Thought + 下一步 Action（或 Final Answer）。"""
        if not history:
            return {
                "thought": "用户要 2024 年评分最高的电影。我先搜索 2024 年的影片，"
                           "但我不知道具体片名，先用搜索工具找候选。",
                "action": "search_movies", "args": {"keyword": "沙丘"},
            }
        if len(history) == 1:
            obs = json.loads(history[-1][2])
            titles = [m["title"] for m in obs["movies"]]
            return {
                "thought": f"搜到候选 {titles}，但要『评分最高』还需要评分数据，逐个查询评分。",
                "action": "get_rating", "args": {"title": titles[0]},
            }
        if len(history) == 2:
            obs = json.loads(history[-1][2])
            return {
                "thought": f"《{obs['title']}》评分 {obs['rating']}。只有一部候选，可以下结论了。",
                "final": f"2024 年评分最高的电影是《{obs['title']}》（评分 {obs['rating']}）。",
            }
        return {"final": "信息不足。"}

    def run(self) -> str:
        history = []
        for step in range(1, self.max_steps + 1):
            d = self._reason(history)

            if "final" in d:
                print(f"Thought: {d['thought'] if 'thought' in d else '信息已足够，直接总结。'}")
                print(f"Final Answer: {d['final']}\n")
                self.trajectory.append(("已总结", "FINAL", d["final"]))
                return d["final"]

            print(f"Thought: {d['thought']}")
            print(f"Action: {d['action']}")
            print(f"Action Input: {json.dumps(d['args'], ensure_ascii=False)}")

            observation = TOOLS[d["action"]](**d["args"])
            print(f"Observation: {observation}\n")
            history.append((d["thought"], d["action"], observation))
            self.trajectory.append((d["thought"], f"{d['action']}({d['args']})", observation))

        return "达到最大步数，未能完成。"


def main():
    print("=" * 62)
    print("ReAct 模式：Thought -> Action -> Observation 循环")
    print("=" * 62)
    agent = ReActAgent("找一部 2024 年评分最高的电影")
    agent.run()

    print("=" * 62)
    print(f"轨迹共 {len(agent.trajectory)} 步（黑匣子数据）：")
    for i, (th, act, obs) in enumerate(agent.trajectory, 1):
        print(f"  {i}. Action={act[:40]}  Observation={obs[:40]}")

    print("\n要点：")
    print("  1. Thought 显式化：每步『为什么』都写在纸上，可解释可调试")
    print("  2. 没有 Thought 的 Agent 只见 Action 序列，出错时无从定位")
    print("  3. 轨迹三元组是后续评估(Day07)/审计(Day09)的数据基础")


if __name__ == "__main__":
    main()