# Day06 - 工具调用循环与错误处理

> 把"决策→执行→回填"放进循环，直到模型不再调用工具——这就是 Agent 的雏形。同时正确处理参数非法、执行失败、超时，并防止无限循环。

---

## 1. 工具调用循环

真正的工具调用往往不止一轮。循环伪代码：

```
messages = [用户消息]
循环:
    响应 = 模型调用(messages + tools)
    if 响应无 tool_calls:
        break                 # 模型作答，结束
    执行每个 tool_call，得 results
    messages += [assistant(tool_calls)] + tool_messages(results)
    回到循环顶部
最终返回模型最后的文本
```

这就是 Agent 的"行动骨架"：模型不断决定"还要不要调工具"，直到给出最终答复。

---

## 2. 终止条件

- **正常**：模型不再返回 `tool_calls`，返回纯文本 → 结束
- **保护**：设置**最大迭代数**（如 10），防止模型死循环
- **异常**：执行抛错或超时 → 视为一轮错误，回传错误信息并继续/结束

---

## 3. 错误处理

| 错误 | 处理 |
|------|------|
| arguments 非法 JSON | 捕获，回传"参数解析失败" |
| 必填缺失 / 类型不符 | 校验后回传具体错误 |
| 执行抛异常 | 把异常转成错误结果回填 |
| 工具超时 | 设超时，超时即返回超时错误 |
| 未知工具名 | 回传"没有此工具" |

通用做法：**把错误作为 tool 角色的 content 回填**，让模型知道失败并可重试或兜底。

```python
try:
    result = execute(tc)
except Exception as e:
    result = f"工具执行失败：{e}"
tool_messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
```

---

## 4. 防死循环

```python
MAX_ITER = 10
while iterations < MAX_ITER:
    ...
    if not tool_calls:
        break
    iterations += 1
else:
    final = f"已达到最大轮数 {MAX_ITER}，请人工介入。"
```

---

## 5. 本节小结

- 循环流程：**决策 → 执行 → 回填 → 再决策**，直至无 tool_calls
- 必须设**最大迭代数**防止死循环
- 各类错误统一转成 tool 结果回填，交给模型处理
- 这个循环就是最小 Agent 的核心（Day08 会实做）

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_tool_loop.py` | 带最大迭代数的工具调用循环（核心） |
| `02_error_handling.py` | 各类错误的处理与回填 |
| `03_max_iterations.py` | 防死循环的演示 |
| `README.md` | 本目录说明 |

均**离线可运行**。