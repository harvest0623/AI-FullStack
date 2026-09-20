# 文件用途：第一个 LangGraph 图（最简单的两节点图）
# 场景：GraphFlow 内容的接收与预处理
#   接收节点：读取用户输入文本，做简单清洗，写入 state
#   处理节点：对文本做长度统计与规范化，产出预处理结果
# 完整展示 StateGraph 创建 / compile / invoke 流程，
# 并用 get_graph().print_ascii() 与 stream_mode="updates" 观察节点执行次序与状态流转。

from typing import TypedDict

from langgraph.graph import StateGraph, END, START


# 1) 定义 State：节点间共享的数据容器（TypedDict）
class State(TypedDict):
    """GraphFlow 工作流的共享状态。"""
    input_text: str      # 用户提交的原始文本（文章/评论）
    cleaned_text: str    # 清洗后的文本
    char_count: int      # 字符数
    process_note: str    # 处理说明


# 2) 定义 Node 函数：接收 state，返回 dict（对 state 的部分更新）
def receive_node(state: State) -> dict:
    """接收节点：读取输入文本，做简单清洗（去首尾空白），写入部分字段。"""
    raw = state["input_text"]
    cleaned = raw.strip()
    return {
        "cleaned_text": cleaned,
        "process_note": f"已接收 {len(raw)} 字符",
    }


def process_node(state: State) -> dict:
    """处理节点：基于前序节点写入的 cleaned_text 继续处理。"""
    text = state["cleaned_text"]
    return {
        "char_count": len(text),
        "process_note": state["process_note"] + f"；清洗后 {len(text)} 字符",
    }


# 3) 创建 StateGraph
graph = StateGraph(State)

# 4) 添加节点和边
graph.add_node("receive", receive_node)     # 接收节点
graph.add_node("process", process_node)     # 处理节点
graph.set_entry_point("receive")            # 入口：从 receive 开始（等价于 add_edge(START, "receive")）
graph.add_edge("receive", "process")        # receive -> process
graph.set_finish_point("process")           # 出口：process 之后结束（等价于 add_edge("process", END)）

# 5) 编译图为可执行对象
app = graph.compile()

# 打印图结构（ASCII 形式，直观展示节点与边）
print("=" * 50)
print("图结构（get_graph().print_ascii()）")
print("=" * 50)
app.get_graph().print_ascii()

# 6) 执行图：invoke(input)
print("=" * 50)
print("执行图：invoke()")
print("=" * 50)
result = app.invoke({"input_text": "  这是一篇需要审核的 GraphFlow 示例文章。  "})
for key, value in result.items():
    print(f"  {key}: {value!r}")

# 7) 观察节点执行次序与状态流转（stream_mode="updates" 逐节点输出增量）
print("=" * 50)
print("逐节点状态流转（stream_mode='updates'）")
print("=" * 50)
for event in app.stream({"input_text": "  第二条测试输入  "}, stream_mode="updates"):
    print("  事件:", event)