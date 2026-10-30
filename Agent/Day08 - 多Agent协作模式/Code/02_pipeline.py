"""
02_pipeline.py
Pipeline 流水线：分析 -> 写作 -> 审查 三段串行加工。
上一步的产出是下一步的输入，演示阶段接口约定与错误传播处理。

运行：python 02_pipeline.py
"""


# ---------------------------------------------------------------------------
# 三个阶段（各自独立上下文，只通过"阶段产物"衔接）
# ---------------------------------------------------------------------------
def stage_analyze(task: str) -> dict:
    """阶段1：数据分析（真实场景=一个带数据工具的 Agent）。"""
    print(f"  [1/3 分析] 输入：{task}")
    output = {"sales": 1450, "prev": 980, "mom": "+48.0%",
              "top_category": "家电"}
    print(f"  [1/3 分析] 产出：{output}")
    return output


def stage_write(analysis: dict) -> str:
    """阶段2：写作（真实场景=一个写作 Agent）。"""
    print(f"  [2/3 写作] 输入：{analysis}")
    draft = (f"本月销量 {analysis['sales']}，环比 {analysis['mom']}；"
             f"主力品类为{analysis['top_category']}，表现稳健向好。")
    print(f"  [2/3 写作] 产出草稿：{draft}")
    return draft


def stage_review(draft: str) -> dict:
    """阶段3：审查（真实场景=一个校验 Agent）。"""
    print(f"  [3/3 审查] 输入草稿：{draft}")
    issues = []
    if "1450" not in draft:
        issues.append("缺少核心数据")
    if "%" not in draft:
        issues.append("缺少环比数据")
    result = {"approved": len(issues) == 0, "issues": issues}
    print(f"  [3/3 审查] 结论：{result}")
    return result


# ---------------------------------------------------------------------------
# 流水线执行器：串行 + 接口校验 + 错误传播处理
# ---------------------------------------------------------------------------
def run_pipeline(task: str) -> str:
    try:
        analysis = stage_analyze(task)
        # 阶段接口校验：防止上游产出坏数据污染下游
        if not isinstance(analysis, dict) or "sales" not in analysis:
            raise ValueError("分析阶段产出不合规：缺少 sales 字段")

        draft = stage_write(analysis)
        review = stage_review(draft)

        if not review["approved"]:
            return f"流水线终止于审查：{review['issues']}"
        return f"定稿：{draft}"
    except Exception as e:
        return f"流水线中断：{e}（上游失败，不继续传播）"


def main():
    print("=" * 62)
    print("Pipeline 流水线：分析 -> 写作 -> 审查")
    print("=" * 62)
    final = run_pipeline("生成本月销售周报")
    print(f"\n{final}")

    print("\n--- 错误传播演示：分析阶段产出坏数据 ---")

    def bad_analyze(task):
        print(f"  [1/3 分析] 输入：{task}")
        out = {"error": "数据源不可用"}          # 缺 sales 字段
        print(f"  [1/3 分析] 产出：{out}")
        return out

    def run_bad(task):
        try:
            analysis = bad_analyze(task)
            if not isinstance(analysis, dict) or "sales" not in analysis:
                raise ValueError("分析阶段产出不合规：缺少 sales 字段")
            draft = stage_write(analysis)
            return stage_review(draft)
        except Exception as e:
            return f"流水线中断：{e}（写手与审查者不被污染）"

    print(run_bad("生成本月销售周报"))

    print("\n要点：")
    print("  1. 串行加工：阶段产物即接口，约定结构（dict/str）防止衔接错乱")
    print("  2. 每阶段独立上下文：写手只拿到分析 JSON，不看查询过程，省 token")
    print("  3. 接口校验拦截坏数据：不让上游错误传播到下游")
    print("  4. 审查不通过 -> 定向重跑写作阶段即可，不必全链重来")


if __name__ == "__main__":
    main()