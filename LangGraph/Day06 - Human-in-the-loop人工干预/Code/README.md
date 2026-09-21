# Day06 Code - Human-in-the-loop 人工干预示例

> 本目录是 Day06 的可运行 Python 示例，均由 `python 文件名.py` 直接运行。

## 依赖安装

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv
```

本目录示例以规则逻辑演示 HITL 框架能力，无需真实 API Key 也可运行（未读取到 Key 会打印提示并继续）。

## 文件清单

| 文件 | 运行方式 | 演示重点 |
|------|----------|----------|
| `01_interrupt_basics.py` | `python 01_interrupt_basics.py` | `interrupt()` 暂停、`get_state` 捕获打断态、`Command(resume)` 恢复 |
| `02_command_resume.py` | `python 02_command_resume.py` | 多处 `interrupt`、`Command(resume)` 逐级恢复、多线程隔离 |
| `03_approval_flow.py` | `python 03_approval_flow.py` | 完整审批工作流、可复用 `ApprovalWorkflow` |

## 运行建议

- 三者都依赖 `MemorySaver`（`interrupt` 必须有 checkpointer）。
- 观察输出中 `next` 字段：那正是图"停在哪一步"的证据。
- 想验证恢复关键性，可把 `resume` 去掉，`invoke` 会被永久挂起（输出中不见最终 `report`）。