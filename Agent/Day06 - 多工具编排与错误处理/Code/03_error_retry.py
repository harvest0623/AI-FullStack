"""
03_error_retry.py
错误分类与重试策略：按错误类型分派处理动作。
- 参数错误 -> 修正后重试（由模型改参数）
- 执行错误 -> 指数退避重试（上限 3 次）
- 超时     -> 短超时重试 1 次，再失败上报
- 权限错误 -> 不重试，升级人工
- 幻觉工具 -> 不重试，返回可用清单

运行：python 03_error_retry.py
"""

import json
import time


# ---------------------------------------------------------------------------
# 错误分类器
# ---------------------------------------------------------------------------
def classify_error(err: dict) -> str:
    """把工具返回的错误归类 -> 决定重试策略。"""
    code = err.get("error")
    if code == "not_found_tool":
        return "hallucination"          # 幻觉工具
    if code in (403, "forbidden", "quota_exceeded"):
        return "permission"             # 权限/配额
    if code == "timeout":
        return "timeout"
    if code in (500, 502, 503, "internal"):
        return "transient"              # 瞬时执行错误
    return "param"                      # 其余视为参数类


STRATEGY = {
    "param":        "改参数后重试（错误信息要可指导）",
    "transient":    "指数退避重试，上限 3 次",
    "timeout":      "短超时重试 1 次，再失败上报",
    "permission":   "不重试！升级人工处理",
    "hallucination": "不重试！返回可用工具清单",
}


# ---------------------------------------------------------------------------
# 模拟工具与故障注入
# ---------------------------------------------------------------------------
class FlakyService:
    """一个不稳定的服务：前两次调用 500，第三次成功。"""
    def __init__(self):
        self.calls = 0

    def query(self, week: str):
        self.calls += 1
        if self.calls <= 2:
            return {"error": 503}
        return {"week": week, "sales": 1450}


def backoff_retry(service, args: dict, max_retries: int = 3):
    """指数退避重试。"""
    for attempt in range(1, max_retries + 1):
        result = service.query(**args)
        if "error" not in result:
            return result, attempt
        wait = 0.1 * (2 ** (attempt - 1))    # 0.1, 0.2, 0.4
        print(f"    第 {attempt} 次失败({result['error']})，退避 {wait:.1f}s 后重试...")
        time.sleep(wait)
    return result, max_retries


def main():
    print("=" * 62)
    print("错误分类 -> 重试策略分派")
    print("=" * 62)

    cases = [
        ({"error": 503}, "瞬时故障（服务过载）"),
        ({"error": "timeout"}, "工具超时"),
        ({"error": 403}, "权限不足"),
        ({"error": "not_found_tool"}, "幻觉工具（不存在）"),
        ({"error": "invalid_week_format"}, "参数格式错误"),
    ]
    for err, label in cases:
        etype = classify_error(err)
        print(f"  {label:<24} -> {etype:<14} => {STRATEGY[etype]}")

    print("\n" + "=" * 62)
    print("实战：指数退避重试（服务前 2 次失败，第 3 次成功）")
    print("=" * 62)
    svc = FlakyService()
    result, attempts = backoff_retry(svc, {"week": "2024-W03"})
    print(f"  最终结果：{result}（共尝试 {attempts} 次）")

    print("\n" + "=" * 62)
    print("权限错误为什么绝不能重试？")
    print("=" * 62)
    print("  1. 403/配额耗尽是确定性失败：重试 100 次还是 403")
    print("  2. 反复重试可能触发风控（被当攻击），扩大影响")
    print("  3. 正确动作：立即停止该工具路径 -> 上报人工 -> 记审计日志")

    print("\n要点：")
    print("  1. 错误分类是前提：类型不同，策略完全不同")
    print("  2. 退避重试只对瞬时故障有效；参数错要『改』而不是『重』")
    print("  3. 权限/幻觉类错误：快速失败 + 可指导的反馈 + 人工兜底")


if __name__ == "__main__":
    main()