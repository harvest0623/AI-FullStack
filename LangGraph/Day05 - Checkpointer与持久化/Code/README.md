# Day05 Code - Checkpointer 与持久化示例

> 本目录是 Day05 的可运行 Python 示例，均由 `python 文件名.py` 直接运行。

## 依赖安装

```bash
pip install langgraph langgraph-checkpoint langchain langchain-openai python-dotenv
pip install langgraph-checkpoint-sqlite   # 02_ 示例需要
```

请先在**项目根目录**的 `.env` 里配置（部分示例提供无 Key 的可运行兜底）：

```bash
OPENAI_API_KEY=sk-xxxx
```

## 文件清单

| 文件 | 运行方式 | 演示重点 |
|------|----------|----------|
| `01_memory_saver.py` | `python 01_memory_saver.py` | MemorySaver、thread_id 会话隔离、同/异 thread 状态累积、无 thread 报错 |
| `02_sqlite_saver.py` | `python 02_sqlite_saver.py` | SqliteSaver 文件持久化、`get_state` 恢复、`from_connstring` |
| `03_time_travel.py` | `python 03_time_travel.py` | `get_state_history` 历史快照、`update_state` 修正、重放 |

## 运行建议

- 先跑 `01_memory_saver.py` 理解 `thread_id` 隔离，再跑 `02` 理解跨进程持久化，最后用 `03` 体会时间旅行。
- `02` 会生成 `graphflow.db`（SQLite 文件），可放心重复运行以观察"重启后状态仍在"。
- 删除该 `.db` 文件即可重置持久化会话。