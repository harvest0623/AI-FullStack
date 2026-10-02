# Day05 - 构建 MCP Server（二）：资源与提示词

> 继工具之后，继续在 Server 里加入**资源（Resources）**与**提示词（Prompts）**，并用动态 URI、错误处理把它做完整。

---

## 1. 定义资源

在 FastMCP 中用 `@mcp.resource` 暴露资源。最简单形式是**静态字符串**：

```python
@mcp.resource("config://app")
def get_config() -> str:
    """返回应用配置（可作为 JSON 字符串返回）。"""
    return '{"debug": true, "model": "qwen"}'
```

- 资源用 **URI scheme**（如 `config://`、`file://`、`memory://`）命名
- 函数返回值就是 `resources/read` 返回的内容

### 动态 URI 资源

资源不一定只有一个。可以让函数的**参数变成 URI 的路径段**，实现『按需取不同资源』：

```python
@mcp.resource("docs://{topic}")
def get_doc(topic: str) -> str:
    """按主题返回文档。"""
    topics = {"mcp": "MCP 是...", "agent": "Agent 是..."}
    return topics.get(topic, "未找到该主题")
```

> 客户端 `read_resource("docs://mcp")` 时，框架会把 `{topic}` 替换为 `mcp` 传给函数。这就是动态 URI。

---

## 2. 定义提示词

用 `@mcp.prompt()` 定义可复用模板，参数在获取时填充：

```python
@mcp.prompt()
def review_code(code: str) -> str:
    """生成一段代码评审提示。"""
    return f"请评审以下代码，指出 bug 与改进点：\n```\n{code}\n```"
```

- 函数名即提示词名，docstring 即描述
- 返回值是填入参数后的完整提示文本

---

## 3. 组合使用

一个 Server 可以同时拥有工具、资源、提示词。客户端通过三套 list 接口分别发现：

- `tools/list` → 工具
- `resources/list` + `resources/read` → 资源
- `prompts/list` + `prompts/get` → 提示词

---

## 4. 错误处理与日志

- **返回错误**：工具内抛出 `ValueError` 等异常，SDK 会包装传回客户端
- **日志**：`mcp` 支持向客户端推送 `logging/message`，方便调试

```python
@mcp.tool()
def divide(a: float, b: float) -> float:
    """返回 a/b；b 为 0 时报错。"""
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b
```

---

## 5. 本节小结

- `@mcp.resource(uri)` 暴露资源，支持静态值与**动态 URI（`{param}`）**
- `@mcp.prompt()` 暴露可复用提示模板
- 三类原语可共存，客户端分别发现
- 异常即错误返回，SDK 封装日志

---

## 代码说明

进入 `Code/` 目录：

| 文件 | 作用 |
|------|------|
| `01_resources.py` | 讲解 + 模拟资源/提示词定义（离线） |
| `server_resources.py` | 带资源与提示词的真实 Server 模板（需 SDK） |
| `README.md` | 本目录说明 |

`01_resources.py` 离线可运行；`server_resources.py` 需已安装 `mcp`。