# Day12 代码说明

## 运行方式

```bash
cd "Agent/Day12 - 综合实战AgentHub/Code"

python 01_quickstart.py      # 最小用例
python 02_tools_memory.py    # 自定义工具 + 记忆
python 03_full_pipeline.py   # 全流程实战
```

所有代码零第三方依赖，完全离线可运行。

## 文件说明

| 文件 | 内容 |
|------|------|
| `agenthub.py` | **核心框架**：7 组件（ToolRegistry / Memory / Planner / Guard / ApprovalGate / TrajectoryLogger / ReActLoop 总装） |
| `01_quickstart.py` | 3 步跑通：注册工具 -> 运行任务 -> 查看轨迹 |
| `02_tools_memory.py` | 自定义 2 个新工具、长期记忆跨任务生效、审批函数注入 |
| `03_full_pipeline.py` | 一次运行体验：注入拦截 / 正常任务 / 高危审批 / 数量超权限被拒 / 手机号脱敏 / 轨迹日志 |

## agenthub.py 组件速查

```python
from agenthub import AgentHub, Tool, default_tools

hub = AgentHub(approve_fn=你的审批函数)   # 审批函数可注入任意交互逻辑
hub.register_tools(default_tools())     # 或自定义 Tool(name, desc, schema, handler, risk)
result = hub.run("任务描述")             # 一次调用走完全链路
print(hub.logger.render())               # 轨迹日志
hub.memory.longterm                      # 长期记忆
```

## 观察要点

**01_quickstart.py**
- 任务"查库存和价格，然后下单 10 个"被规划器分解为 3 步
- 轨迹日志中每步都有 思考/观察 记录，place_order 高危操作走了审批
- 最终回答由 `_summarize` 汇总所有观察生成

**02_tools_memory.py**
- 新工具（lookup_supplier / submit_refund）定义后直接注册即用
- 800 元退款被审批门拒绝、300 元通过：审批逻辑完全由注入的函数决定
- MemoryAwareHub 展示继承扩展框架的方式

**03_full_pipeline.py**
- 场景 1：注入攻击在进入规划前就被拦下（轨迹只有 1 条记录）
- 场景 3 vs 3b：同样的 place_order，10 个批准、500 个拒绝（模拟人类权限）
- 场景 4：物流工具返回的手机号 13812345678 在输出护栏被打码
- 场景 5：轨迹日志中 `[拦截]` 标记清晰可追溯每一步的放行/拦截

## 与真实框架对照

| AgentHub | LangGraph / LangChain |
|----------|----------------------|
| `ToolRegistry` | `BaseTool` + `bind_tools` |
| `ReActLoop`（run 主循环） | `create_react_agent` / 图循环 |
| `Memory.longterm` | `Checkpointer` / Store |
| `Guard` | 自定义 guardrail 节点 |
| `ApprovalGate` | `interrupt()` + `Command(resume=...)` |
| `TrajectoryLogger` | LangSmith tracing |

## 动手练习建议

1. 新增一个 `search_web` 工具并让 Planner 识别"搜索"关键词
2. 把 `_summarize` 改成调用真实 LLM API（OpenAI 兼容接口）
3. 给 TrajectoryLogger 增加 JSON 输出，存入文件实现持久化
4. 用 Day08 的 Supervisor 模式把两个 AgentHub 实例编排起来
