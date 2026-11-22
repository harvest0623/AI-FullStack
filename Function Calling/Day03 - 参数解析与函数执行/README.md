# Day03 - 参数解析与函数执行

> 本节目标：吃透 Function Calling 循环里"**执行(e)**"这个环节——当模型给出
> `{name, args}` 后，你的程序如何把 args 解析出来、调用真实函数、拿到结果。

---

## 1. 一次调用的完整链路

模型输出的是一个**结构化的调用意图**，例如：

```json
{"name": "add", "args": {"a": 3, "b": 4}}
```

`add` 是我们定义的函数名，`args` 是参数。执行步骤：

```
1. 在注册表里按 name 找到函数
2. 校验 args 是否符合 parameters(缺必填/类型)   ← Day06 深入
3. 调用函数: add(3, 4)
4. 把返回值转成字符串, 作为 tool 消息喂回模型
```

---

## 2. 参数从哪来？

真实模型会有**两个来源**决定 `args`：

1. **从用户自然语言推断**——用户说"12 和 5"，模型推断出 `a=12, b=5`。
2. **从上下文/工具链推断**——前面步骤产生的数据作为后续步骤参数。

本 Day 用规则 planner 演示第 1 种：从文本里**提取数字转成参数**。

```python
def planner(messages, tools):
    text = messages[-1]["content"]
    nums = [int(x) for x in text.replace("和", " ").split() if x.isdigit()]
    if len(nums) >= 2:
        return ("call", [{"name": "add", "args": {"a": nums[0], "b": nums[1]}}])
```

---

## 3. 关键方法 `registry.execute`

```python
registry.execute("add", {"a": 3, "b": 4})   # -> "7"
```

它内部做：找函数 → 校验 → 调用 → 返回字符串。你只需要保证：
- `name` 在注册表里存在；
- `args` 是 dict，键名与函数形参对齐。

---

## 4. 本节练习

[03-execute.py](Code/03-execute.py) 演示：
直接用 `execute()` 执行函数；再用规则 planner 从自然语言"提取参数"触发 `add` 与
`get_weather`，验证参数解析 → 执行 → 结果的完整链路。

```bash
python "Day03 - 参数解析与函数执行/Code/03-execute.py"
```

---

## 5. 你要记住的三句话

1. 循环里"执行"环节：`name` 找函数 → `args` 当实参 → 调函数 → 转字符串喂回。
2. `args` 的键名必须与函数形参名一致（靠 schema 对齐）。
3. 一个不可靠的点：模型可能传错参——所以**校验**很关键（Day06）。

下一节：**多工具选择与循环**——模型在一次请求里连选好几个工具。