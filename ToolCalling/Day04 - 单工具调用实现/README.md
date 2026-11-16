# Day04 - 单工具调用实现

> 用内置"模拟模型"完整跑通一次工具调用闭环，并安全解析/校验参数。这是理解后续所有扩展（多工具、循环、Agent）的范式。

---

## 1. 核心闭环（四步）

一次工具调用的最小实现：

```
 ① 定义工具 → ② 模型返回 tool_calls → ③ 应用执行 → ④ 回填后模型作答
```

```python
# ① 定义并传入（简化示意）
tools = [{"type": "function", "function": {
    "name": "get_weather",
    "description": "查询指定城市的天气",
    "parameters": {"type": "object",
                   "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}]

# ② 模型返回
tool_calls = [...]   # 含 name / arguments(JSON字符串)

# ③ 应用执行：解析参数、调用函数、拿结果
import json
args = json.loads(tool_call["arguments"])
result = get_weather(args["city"])

# ④ 回填给模型，模型基于 result 作答
```

---

## 2. 在一个"模拟模型"里体验闭环

由于不依赖真实 API，本日提供一个 `mock_model`：它是极简"函数即模型"的替身——**提前知道该调什么工具、参数是什么**，用于演示应用侧的执行与回填逻辑。你替换成任意真实支持 tool calling 的端点即可。

```
用户 → mock_model 产出 tool_calls → 应用执行 get_weather → 回填 → 作答
```

---

## 3. 安全解析与校验

- `function.arguments` 是 **JSON 字符串**，必须 `json.loads` 解析
- 解析可能失败（非法 JSON）→ 应捕获并回传错误
- 执行前校验必填字段与类型（见 Day02 的 validate）

```python
try:
    args = json.loads(tool_call.get("arguments", "{}"))
except json.JSONDecodeError:
    result = "参数解析失败，请检查参数格式"
```

---

## 4. 真实 API 形态（对照）

真实场景只需把"模拟模型返回"替换为真实 SDK 调用返回值，应用侧的处理逻辑完全一致。Day04 以 `02_real_shape.py` 给出 OpenAI 风格的真实形态示意，不真正发请求。

---

## 5. 本节小结

- 闭环四步：**定义 → 模型返回 tool_calls → 应用执行 → 回填作答**
- 参数必须安全解析 + 校验后再执行
- 模拟模型用于离线体验；真实时替换为真实端点即可

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_single_call.py` | 用模拟模型完整跑通一次工具调用闭环 |
| `02_real_shape.py` | OpenAI 风格的请求/返回形态示意 |
| `03_parse_arguments.py` | 参数安全解析与校验的实用函数 |
| `README.md` | 本目录说明 |

均**离线可运行**（不真实发请求）。