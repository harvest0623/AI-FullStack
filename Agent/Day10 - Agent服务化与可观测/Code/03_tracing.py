# -*- coding: utf-8 -*-
"""
Day10 - 03 链路追踪（Distributed Tracing）

演示内容：
1. trace_id 贯穿主 Agent、工具、子 Agent、LLM 调用
2. span 树结构（span_id / parent_span_id）
3. 渲染耗时瀑布图，定位慢在哪一环
4. OpenTelemetry 核心概念的 numpy-free 简化实现

离线可运行。
"""

import time
import uuid
from dataclasses import dataclass, field


# ============================================================
# 第一部分：Span 数据结构与追踪器
# ============================================================

@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str            # 环节名，如 main_agent / tool_search / llm_call
    status: str = "ok"   # ok / error
    start: float = 0.0
    end: float = 0.0
    attrs: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return (self.end - self.start) * 1000 if self.end else 0


class Tracer:
    """
    极简追踪器：生产中用 OpenTelemetry 替代。
    核心概念一致：trace_id 串联，parent_span_id 构树。
    """

    def __init__(self):
        self.spans: list[Span] = []

    def start_span(self, trace_id: str, name: str, parent: Span | None = None, **attrs) -> Span:
        span = Span(
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:8],
            parent_span_id=parent.span_id if parent else None,
            name=name,
            start=time.time(),
            attrs=attrs,
        )
        self.spans.append(span)
        return span

    def end_span(self, span: Span, status: str = "ok"):
        span.status = status
        span.end = time.time()

    # ---------- 分析工具 ----------
    def waterfall(self, trace_id: str) -> str:
        """渲染瀑布图：缩进表示层级，条长表示耗时"""
        spans = [s for s in self.spans if s.trace_id == trace_id]
        if not spans:
            return "无此 trace"

        root = next((s for s in spans if s.parent_span_id is None), spans[0])
        lines = [f"trace_id: {trace_id}（总耗时 {root.duration_ms:.0f}ms）"]

        def render(span: Span, depth: int):
            status_mark = "" if span.status == "ok" else " [ERROR]"
            bar = "#" * max(1, int(span.duration_ms / 20))
            lines.append(
                f"  {'  ' * depth}├─ {span.name:<16} {span.duration_ms:6.0f}ms {bar}{status_mark}"
            )
            children = [s for s in spans if s.parent_span_id == span.span_id]
            for c in children:
                render(c, depth + 1)

        for s in spans:
            if s.parent_span_id is None:
                render(s, 0)
        return "\n".join(lines)

    def slowest(self, trace_id: str) -> tuple:
        """找最耗时的非根环节（根 span 是总耗时，优化要看子环节）"""
        spans = [s for s in self.spans if s.trace_id == trace_id]
        children = [s for s in spans if s.parent_span_id is not None]
        if not children:
            children = spans
        s = max(children, key=lambda x: x.duration_ms)
        return s.name, s.duration_ms

    def error_spans(self, trace_id: str) -> list[str]:
        return [s.name for s in self.spans
                if s.trace_id == trace_id and s.status == "error"]


# ============================================================
# 第二部分：带追踪的 Agent 执行
# ============================================================

def traced_run(tracer: Tracer, user_input: str) -> str:
    """模拟一次请求：主 Agent -> 2 个工具 + 1 个子 Agent -> LLM 调用"""
    trace_id = f"tr-{uuid.uuid4().hex[:8]}"

    # 根 span：主 Agent
    main = tracer.start_span(trace_id, "main_agent", input_len=len(user_input))
    time.sleep(0.02)

    # 子 span 1：LLM 思考
    llm1 = tracer.start_span(trace_id, "llm_think", parent=main, model="gpt-sim")
    time.sleep(0.06)
    tracer.end_span(llm1)

    # 子 span 2：搜索工具
    tool1 = tracer.start_span(trace_id, "tool_search", parent=main, query="供应商报价")
    time.sleep(0.10)
    tracer.end_span(tool1)

    # 子 span 3：数据库工具（慢）
    tool2 = tracer.start_span(trace_id, "tool_db", parent=main, sql="SELECT...")
    time.sleep(0.15)
    tracer.end_span(tool2)

    # 子 span 4：子 Agent（内部还有 LLM 调用）
    sub = tracer.start_span(trace_id, "sub_agent", parent=main, role="writer")
    time.sleep(0.01)
    sub_llm = tracer.start_span(trace_id, "llm_write", parent=sub, model="gpt-sim")
    time.sleep(0.08)
    tracer.end_span(sub_llm)
    tracer.end_span(sub)

    tracer.end_span(main)
    return trace_id


def traced_run_with_error(tracer: Tracer, user_input: str) -> str:
    """演示错误 span 的标记：工具超时"""
    trace_id = f"tr-{uuid.uuid4().hex[:8]}"
    main = tracer.start_span(trace_id, "main_agent")
    tool = tracer.start_span(trace_id, "tool_api", parent=main, url="https://slow-vendor")
    time.sleep(0.05)
    tracer.end_span(tool, status="error")  # 标记失败
    tracer.end_span(main, status="error")
    return trace_id


# ============================================================
# 演示
# ============================================================

def main():
    tracer = Tracer()

    print("=" * 56)
    print("正常链路：trace_id 串联所有环节，瀑布图看耗时")
    print("=" * 56)
    trace_id = traced_run(tracer, "帮我对比供应商报价")
    print(tracer.waterfall(trace_id))

    name, dur = tracer.slowest(trace_id)
    print(f"\n最慢环节：{name}（{dur:.0f}ms）-> 优化优先级最高")

    print()
    print("=" * 56)
    print("异常链路：工具失败被标记为 ERROR")
    print("=" * 56)
    err_trace = traced_run_with_error(tracer, "查询物流状态")
    print(tracer.waterfall(err_trace))
    print(f"\n错误环节：{tracer.error_spans(err_trace)}")
    print("结论：整条链路失败，但根因定位到 tool_api 这一个 span")


if __name__ == "__main__":
    main()
