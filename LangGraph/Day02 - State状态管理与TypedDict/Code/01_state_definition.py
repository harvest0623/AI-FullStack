# 文件用途：用 TypedDict 定义 State，展示各种字段类型
# 场景：GraphFlow 的 input_text + analysis + risk_level + scores 状态定义
# 演示：标量字段、列表字段、字典字段、嵌套 TypedDict 的定义与初始化，
#       以及如何在非图环境下直接打印 State 结构，帮助建立对 State 形状的直觉。

from typing import TypedDict, Optional, List, Dict, Union


# ---- 1) 嵌套 TypedDict：把相关字段分组成结构体 ----
class RiskScores(TypedDict):
    """风险评分（0-100），数值越大风险越高。"""
    violence: int        # 暴力倾向
    hate: int            # 仇恨言论
    sexual: int          # 色情内容
    self_harm: int       # 自残内容


# ---- 2) 顶层 State：综合展示各种字段类型 ----
class State(TypedDict):
    """GraphFlow 的共享状态。包含标量、列表、字典、嵌套 TypedDict。"""
    # 标量字段
    input_text: str                 # 用户提交的原文（str）
    analysis: str                   # 综合分析结论（str）
    risk_level: str                 # 风险等级 low/medium/high（str）
    engage_human: bool              # 是否需要人工审核（bool）
    review_score: float             # 综合评分 0.0-1.0（float）
    review_count: int               # 审核次数（int）

    # 列表字段：默认「覆盖」语义，多个标签可一次性写入
    tags: List[str]                 # 命中的标签列表

    # 字典字段
    metadata: Dict[str, Union[str, int]]   # 元信息（来源、字数等）

    # 嵌套 TypedDict 字段
    scores: RiskScores              # 分维度风险评分

    # 可选字段（可能不存在）
    note: Optional[str]


def print_state_shape(state: State) -> None:
    """打印一个 State 的结构（field -> type -> value）。"""
    print(f"{'字段':<16}{'类型':<28}值")
    print("-" * 68)
    for key, value in state.items():
        t = type(value).__name__
        display = repr(value)
        if len(display) > 26:
            display = display[:26] + "..."
        print(f"{key:<16}{t:<28}{display}")


def main() -> None:
    print("=" * 68)
    print("GraphFlow - State 定义与初始化")
    print("=" * 68)

    # ---- 3) 初始化 State：直接构造字典（与 TypedDict 字段一一对应）----
    init_state: State = {
        "input_text": "这款手机降噪效果差，客服态度还不好。",
        "analysis": "",
        "risk_level": "",
        "engage_human": False,
        "review_score": 0.0,
        "review_count": 0,
        "tags": [],
        "metadata": {"author": "u_1024", "chars": 15},
        "scores": {"violence": 0, "hate": 5, "sexual": 0, "self_harm": 0},
        # note 为 Optional，此处可不提供
    }

    print("\n[初始 State 结构]")
    print_state_shape(init_state)

    # ---- 4) 展示各字段类型标注的语义 ----
    print("\n[字段类型标注回顾]")
    print("  str    : 单值文本（输入、结论、风险等级）")
    print("  int    : 计数值（审核次数）")
    print("  float  : 阈值分数（综合评分）")
    print("  bool   : 开关（是否需人工审核）")
    print("  List[str] : 标签列表（一次整体写入）")
    print("  Dict[str, Union[str,int]] : 元信息字典")
    print("  RiskScores : 嵌套 TypedDict（分组结构）")
    print("  Optional[str] : 可选字段")

    # ---- 5) Pylance / mypy 静态检查提示 ----
    # 若执行如下赋值（被注释掉），静态类型检查器会给出警告：
    #   init_state2: State = {"input_text": 123}      # 类型不匹配
    #   init_state2 = {"input_text": "x"}              # 缺少字段
    print("\n[类型检查] 用 Pylance(编辑器中)/mypy 打开本文件，"
          "将被注释掉的错误赋值取消注释可看到静态检查警告。")

    # ---- 6) 在实际图中使用该 State（最小演示）----
    from langgraph.graph import StateGraph, START, END

    def analyze_node(state: State) -> dict:
        """模拟分析节点：写满了分析类字段。"""
        return {
            "analysis": "内容涉及商家服务体验抱怨",
            "risk_level": "low",
            "engage_human": False,
            "review_score": 0.35,
            "review_count": 1,
            "tags": ["售后", "客服"],
        }

    builder = StateGraph(State)
    builder.add_node("analyze", analyze_node)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", END)
    app = builder.compile()

    print("\n[在图环境中执行 analyze 节点后]")
    out = app.invoke(init_state)
    for key, value in out.items():
        print(f"  {key}: {value!r}")


if __name__ == "__main__":
    main()